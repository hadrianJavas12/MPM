;;;; Explicit native material/load-step transactions for evolving Mohr-Coulomb.
(in-package :cl-mpm/models/mc-evolution)

(defclass particle-mc-evolution
    (cl-mpm/particle::particle-elastic cl-mpm/particle::particle-plastic)
  ((evolution-law :initarg :evolution-law :accessor particle-evolution-law)
   (kappa :initarg :kappa :initform 0d0 :accessor particle-kappa)
   (kappa-committed :initform 0d0 :accessor particle-kappa-committed)
   (cohesion :initform 0d0 :accessor particle-cohesion)
   (phi :initform 0d0 :accessor particle-phi)
   (psi :initform 0d0 :accessor particle-psi)
   (plastic-increment :initform (cl-mpm/utils:voigt-zeros)
                      :accessor particle-plastic-increment)
   (plastic-volume :initform 0d0 :accessor particle-plastic-volume)
   (plastic-volume-committed :initform 0d0
                             :accessor particle-plastic-volume-committed)
   (plastic-work :initform 0d0 :accessor particle-plastic-work)
   (plastic-work-committed :initform 0d0 :accessor particle-plastic-work-committed)
   (last-projection :initform nil :accessor particle-last-projection)
   (committed-state :initform nil))
  (:documentation
   "Dedicated evolving MC class. KAPPA is sqrt(2/3)||dev delta-epsilon-p||,
accumulated per accepted load step. It never dispatches to native particle-mc.
PLASTIC-INCREMENT is the latest spatial engineering-Voigt increment; it is not
an objective accumulated finite-strain plastic tensor."))

(defparameter +particle-transaction-slots+
  '(cl-mpm/particle::stress cl-mpm/particle::stress-kirchoff
    cl-mpm/particle::stress-eigenvalues cl-mpm/particle::stress-eigenvectors
    cl-mpm/particle::strain cl-mpm/particle::strain-n
    cl-mpm/particle::trial-elastic-strain
    cl-mpm/particle::strain-rate cl-mpm/particle::eng-strain-rate
    cl-mpm/particle::velocity-rate cl-mpm/particle::velocity-gradient
    cl-mpm/particle::stretch-tensor cl-mpm/particle::stretch-tensor-fbar
    cl-mpm/particle::vorticity
    cl-mpm/particle::deformation-gradient
    cl-mpm/particle::deformation-gradient-0
    cl-mpm/particle::deformation-gradient-increment
    cl-mpm/particle::deformation-gradient-increment-inverse
    cl-mpm/particle::deformation-jacobian-strain
    cl-mpm/particle::deformation-gradient-strain-increment
    cl-mpm/particle::deformation-gradient-strain-increment-inverse
    cl-mpm/particle::j-fbar cl-mpm/particle::fbar-j
    cl-mpm/particle::fbar-j-gather
    cl-mpm/particle::volume cl-mpm/particle::volume-n
    cl-mpm/particle::position-trial cl-mpm/particle::displacement-increment
    cl-mpm/particle::penalty-frictional-force
    cl-mpm/particle::penalty-frictional-force-prev
    cl-mpm/particle::E cl-mpm/particle::nu
    cl-mpm/particle::2d-approximation
    cl-mpm/particle::elastic-matrix cl-mpm/particle::tangent-stiffness
    cl-mpm/particle::p-modulus cl-mpm/particle::p-modulus-0
    cl-mpm/particle::enable-plasticity cl-mpm/particle::softening
    cl-mpm/particle::strain-plastic cl-mpm/particle::strain-plastic-vm
    cl-mpm/particle::strain-plastic-vm-1
    cl-mpm/particle::strain-plastic-vm-inc
    cl-mpm/particle::yield-func cl-mpm/particle::plastic-iterations
    evolution-law kappa kappa-committed cohesion phi psi plastic-increment
    plastic-volume plastic-volume-committed plastic-work plastic-work-committed
    last-projection))

(defstruct (particle-state (:constructor %make-particle-state) (:copier nil))
  slots committed-state)

(defun %copy-state-value (value)
  "Copy the mutable values used by a particle transaction, including laws.
No snapshot owns a mutable array, table, or projection shared with its particle."
  (typecase value
    (magicl:matrix/double-float (magicl:scale value 1d0))
    (particle-state
     (%make-particle-state
      :slots (%copy-state-value (particle-state-slots value))
      :committed-state (%copy-state-value (particle-state-committed-state value))))
    (evolution-law
     (let ((result (copy-structure value)))
       (setf (evolution-law-points result)
             (%copy-state-value (evolution-law-points value))
             (evolution-law-cohesion-points result)
             (%copy-state-value (evolution-law-cohesion-points value))
             (evolution-law-strain-assumption result)
             (%copy-state-value (evolution-law-strain-assumption value)))
       result))
    (projection
     (let ((result (copy-structure value)))
       (setf (projection-tau result) (%copy-state-value (projection-tau value))
             (projection-plastic-increment result)
             (%copy-state-value (projection-plastic-increment value))
             (projection-active result) (%copy-state-value (projection-active value))
             (projection-multipliers result)
             (%copy-state-value (projection-multipliers value))
             (projection-residuals result)
             (%copy-state-value (projection-residuals value)))
       result))
    (cons (cons (%copy-state-value (car value))
                (%copy-state-value (cdr value))))
    (string (copy-seq value))
    (array
     (let ((result (make-array (array-dimensions value)
                               :element-type (array-element-type value))))
       (dotimes (i (array-total-size value) result)
         (setf (row-major-aref result i)
               (%copy-state-value (row-major-aref value i))))))
    ((or null number symbol character) value)
    (otherwise (integration-fail "Unsupported mutable transaction value" (type-of value)))))

(defun %capture-particle-state (mp)
  "Capture current slots without recursively embedding the committed baseline."
  (%make-particle-state
   :slots (loop for name in +particle-transaction-slots+
                when (slot-exists-p mp name)
                collect (if (slot-boundp mp name)
                            (list name t (%copy-state-value (slot-value mp name)))
                            (list name nil nil)))
   :committed-state nil))

(defun %sync-particle-state-in-place! (mp state)
  "Update STATE's slot records in place from MP, reusing existing distinct
magicl matrices inside STATE so explicit MPM steps do not allocate 30 matrices
per particle per step while keeping STATE completely unaliased from MP."
  (dolist (entry (particle-state-slots state) state)
    (let ((name (first entry)))
      (if (slot-boundp mp name)
          (let ((src (slot-value mp name))
                (dst (third entry)))
            (setf (second entry) t)
            (if (and (typep src 'magicl:matrix/double-float)
                     (typep dst 'magicl:matrix/double-float)
                     (not (eq src dst))
                     (= (cl-mpm/utils:nrows src) (cl-mpm/utils:nrows dst))
                     (= (cl-mpm/utils:ncols src) (cl-mpm/utils:ncols dst)))
                (replace (cl-mpm/utils:fast-storage dst)
                         (cl-mpm/utils:fast-storage src))
                (setf (third entry) (%copy-state-value src))))
          (setf (second entry) nil
                (third entry) nil)))))

(defun snapshot-particle (mp)
  "Return a deep constitutive/kinematic trial snapshot, including its baseline.
The embedded committed snapshot has no embedded baseline, so there is no cycle."
  (check-type mp particle-mc-evolution)
  (let ((result (%capture-particle-state mp)))
    (setf (particle-state-committed-state result)
          (%copy-state-value (slot-value mp 'committed-state)))
    result))

(defun %restore-current-slots (mp state)
  (let ((slots (%copy-state-value (particle-state-slots state))))
    (dolist (entry slots mp)
      (destructuring-bind (name boundp value) entry
        (if boundp (setf (slot-value mp name) value) (slot-makunbound mp name))))))

(defun restore-particle (mp state)
  "Restore a snapshot without sharing its arrays or nested committed baseline."
  (check-type mp particle-mc-evolution)
  (check-type state particle-state)
  (let ((saved (%copy-state-value state)))
    (%restore-current-slots mp saved)
    (setf (slot-value mp 'committed-state) (particle-state-committed-state saved)))
  mp)

(defun copy-particle-state (source target)
  "Deep-copy the complete material trial and committed baseline SOURCE -> TARGET.
Position, domain geometry, node caches, and other simulation data are not copied."
  (restore-particle target (snapshot-particle source)))

(defmethod initialize-instance :after ((mp particle-mc-evolution) &key)
  (unless (and (slot-boundp mp 'evolution-law)
               (typep (particle-evolution-law mp) 'evolution-law))
    (integration-fail "A checked evolution law is required"))
  (unless (and (finite-real-p (particle-kappa mp)) (>= (particle-kappa mp) 0d0))
    (integration-fail "Initial kappa must be finite and nonnegative"))
  (setf (particle-kappa mp) (float (particle-kappa mp) 1d0)
        (particle-kappa-committed mp) (particle-kappa mp))
  (multiple-value-bind (c phi psi) (law-values (particle-evolution-law mp)
                                             (particle-kappa mp))
    (setf (particle-cohesion mp) c (particle-phi mp) phi (particle-psi mp) psi))
  (setf (cl-mpm/particle::mp-strain-plastic-vm mp) (* 1.5d0 (particle-kappa mp))
        (cl-mpm/particle::mp-strain-plastic-vm-1 mp) (* 1.5d0 (particle-kappa mp))
        (cl-mpm/particle::mp-strain-plastic-vm-inc mp) 0d0
        (slot-value mp 'committed-state) (%capture-particle-state mp)))

(defmethod reinitialize-instance :after ((mp particle-mc-evolution) &key)
  (when (slot-boundp mp 'committed-state)
    (setf (slot-value mp 'committed-state)
          (%copy-state-value (slot-value mp 'committed-state))))
  (when (slot-boundp mp 'last-projection)
    (setf (slot-value mp 'last-projection)
          (%copy-state-value (slot-value mp 'last-projection)))))

(defmethod cl-mpm/particle::new-loadstep-mp ((mp particle-mc-evolution))
  "Commit native load-step fields before recording the complete custom baseline."
  (call-next-method)
  (setf (particle-kappa-committed mp) (particle-kappa mp)
        (particle-plastic-volume-committed mp) (particle-plastic-volume mp)
        (particle-plastic-work-committed mp) (particle-plastic-work mp))
  (let ((existing (slot-value mp 'committed-state)))
    (if (typep existing 'particle-state)
        (%sync-particle-state-in-place! mp existing)
        (setf (slot-value mp 'committed-state) (%capture-particle-state mp))))
  mp)

(defmethod cl-mpm/particle::reset-loadstep-mp ((mp particle-mc-evolution))
  "Run native rollback first, then restore stress, history, strength and arrays."
  (let ((before (snapshot-particle mp))
        (baseline (%copy-state-value (slot-value mp 'committed-state))))
    (unless baseline (integration-fail "No committed material baseline exists"))
    (handler-case
        (progn
          (call-next-method)
          (%restore-current-slots mp baseline)
          (setf (slot-value mp 'committed-state) baseline)
          mp)
      (error (condition)
        (restore-particle mp before)
        (error condition)))))
