;;;; Owned CLOS state and native Hencky/Kirchhoff adapter for the experimental law.
(in-package :cl-mpm/models/clay-creep)

(defclass particle-clay-creep
    (cl-mpm/particle::particle-elastic cl-mpm/particle::particle-plastic)
  ((creep-law :initarg :creep-law :accessor particle-creep-law)
   (enable-creep :initarg :enable-creep :initform t :accessor particle-enable-creep)
   (kappa :initarg :kappa :initform 0d0 :accessor particle-kappa)
   (kappa-committed :initform 0d0)
   (rate :initform 0d0 :accessor particle-rate)
   (current-yield :initform 0d0 :accessor particle-current-yield)
   (work :initform 0d0 :accessor particle-work)
   (work-committed :initform 0d0)
   (committed-state :initform nil))
  (:documentation "Experimental phi_u=0 total-stress undrained clay surrogate.
The skeleton is volumetrically elastic; no pore pressure or coupled CU analysis.
Kappa is conventional equivalent isochoric vp strain, not native 1.5*kappa.
Disable creep explicitly for elastic geostatic initialization; never reset
gravity stresses or silently modify material parameters when enabling it."))

(defparameter +clay-transaction-slots+
  '(cl-mpm/particle::stress cl-mpm/particle::stress-kirchoff
    cl-mpm/particle::stress-eigenvalues cl-mpm/particle::stress-eigenvectors
    cl-mpm/particle::strain cl-mpm/particle::strain-n
    cl-mpm/particle::trial-elastic-strain cl-mpm/particle::strain-rate
    cl-mpm/particle::eng-strain-rate cl-mpm/particle::velocity-rate
    cl-mpm/particle::velocity-gradient cl-mpm/particle::stretch-tensor
    cl-mpm/particle::stretch-tensor-fbar cl-mpm/particle::vorticity
    cl-mpm/particle::deformation-gradient cl-mpm/particle::deformation-gradient-0
    cl-mpm/particle::deformation-gradient-increment
    cl-mpm/particle::deformation-gradient-increment-inverse
    cl-mpm/particle::deformation-gradient-strain-increment
    cl-mpm/particle::deformation-gradient-strain-increment-inverse
    cl-mpm/particle::deformation-jacobian-strain cl-mpm/particle::j-fbar
    cl-mpm/particle::fbar-j cl-mpm/particle::fbar-j-gather
    cl-mpm/particle::volume cl-mpm/particle::volume-n
    cl-mpm/particle::position-trial cl-mpm/particle::displacement-increment
    cl-mpm/particle::penalty-frictional-force
    cl-mpm/particle::penalty-frictional-force-prev
    cl-mpm/particle::p-modulus cl-mpm/particle::p-modulus-0
    cl-mpm/particle::strain-plastic cl-mpm/particle::strain-plastic-vm
    cl-mpm/particle::strain-plastic-vm-1 cl-mpm/particle::strain-plastic-vm-inc
    cl-mpm/particle::yield-func cl-mpm/particle::plastic-iterations
    kappa kappa-committed rate current-yield work work-committed))

(defun clay-copy-value (value)
  (typecase value
    (magicl:matrix/double-float (magicl:scale value 1d0))
    (cons (cons (clay-copy-value (car value)) (clay-copy-value (cdr value))))
    (array (let ((copy (make-array (array-dimensions value)
                                  :element-type (array-element-type value))))
             (dotimes (i (array-total-size value) copy)
               (setf (row-major-aref copy i) (clay-copy-value (row-major-aref value i))))))
    ((or null number symbol character) value)
    (t (error "Unsupported mutable clay transaction state ~S." (type-of value)))))

(defun clay-capture-slots (mp &optional previous)
  "Refresh an unaliased baseline, reusing private snapshot matrices when possible."
  (let ((entries (or previous
                     (loop for name in +clay-transaction-slots+
                           when (slot-exists-p mp name) collect (list name nil nil)))))
    (dolist (entry entries entries)
      (let ((name (first entry)))
        (setf (second entry) (slot-boundp mp name))
        (when (second entry)
          (let ((source (slot-value mp name)) (target (third entry)))
            (if (and (typep source 'magicl:matrix/double-float)
                     (typep target 'magicl:matrix/double-float) (not (eq source target))
                     (= (cl-mpm/utils:nrows source) (cl-mpm/utils:nrows target))
                     (= (cl-mpm/utils:ncols source) (cl-mpm/utils:ncols target)))
                (replace (cl-mpm/utils:fast-storage target) (cl-mpm/utils:fast-storage source))
                (setf (third entry) (clay-copy-value source)))))))))

(defun clay-restore-slots (mp entries)
  (dolist (entry entries mp)
    (destructuring-bind (name boundp value) entry
      (if boundp
          (let ((current (and (slot-boundp mp name) (slot-value mp name))))
            (if (and (typep current 'magicl:matrix/double-float)
                     (typep value 'magicl:matrix/double-float)
                     (= (cl-mpm/utils:nrows current) (cl-mpm/utils:nrows value))
                     (= (cl-mpm/utils:ncols current) (cl-mpm/utils:ncols value)))
                (replace (cl-mpm/utils:fast-storage current) (cl-mpm/utils:fast-storage value))
                (setf (slot-value mp name) (clay-copy-value value))))
          (slot-makunbound mp name)))))

(defun snapshot-clay-creep-particle (mp)
  "Owned constitutive/kinematic trial plus its independently owned committed state."
  (check-type mp particle-clay-creep)
  (list (clay-capture-slots mp) (clay-copy-value (slot-value mp 'committed-state))))

(defun restore-clay-creep-particle (mp snapshot)
  (check-type mp particle-clay-creep)
  (clay-restore-slots mp (first snapshot))
  (setf (slot-value mp 'committed-state) (clay-copy-value (second snapshot)))
  mp)

(defmethod initialize-instance :after ((mp particle-clay-creep) &key)
  (unless (and (slot-boundp mp 'creep-law) (typep (particle-creep-law mp) 'clay-creep-law)
               (finite-number-p (particle-kappa mp)) (>= (particle-kappa mp) 0d0))
    (error "A checked clay creep law and nonnegative initial kappa are required."))
  ;; Validate the elasticity/softening relation before a simulation starts.
  (clay-creep-update #(0d0 0d0 0d0 0d0 0d0 0d0)
                     (cl-mpm/particle::mp-E mp) (cl-mpm/particle::mp-nu mp)
                     (particle-creep-law mp) (particle-kappa mp) 0d0)
  (setf (particle-kappa mp) (float (particle-kappa mp) 1d0)
        (slot-value mp 'kappa-committed) (particle-kappa mp)
        (particle-current-yield mp) (clay-creep-yield (particle-creep-law mp) (particle-kappa mp))
        (cl-mpm/particle::mp-strain-plastic-vm mp) (* 1.5d0 (particle-kappa mp))
        (cl-mpm/particle::mp-strain-plastic-vm-1 mp) (* 1.5d0 (particle-kappa mp))
        (slot-value mp 'committed-state) (clay-capture-slots mp)))

(defmethod reinitialize-instance :after ((mp particle-clay-creep) &key)
  (when (slot-boundp mp 'committed-state)
    (setf (slot-value mp 'committed-state) (clay-copy-value (slot-value mp 'committed-state)))))

(defmethod cl-mpm/particle::new-loadstep-mp ((mp particle-clay-creep))
  (call-next-method)
  (setf (slot-value mp 'kappa-committed) (particle-kappa mp)
        (slot-value mp 'work-committed) (particle-work mp))
  (setf (slot-value mp 'committed-state)
        (clay-capture-slots mp (slot-value mp 'committed-state)))
  mp)

(defmethod cl-mpm/particle::reset-loadstep-mp ((mp particle-clay-creep))
  (unless (slot-value mp 'committed-state) (error "Missing clay committed baseline."))
  (call-next-method)
  (clay-restore-slots mp (slot-value mp 'committed-state))
  mp)

(defmethod cl-mpm/particle:constitutive-model ((mp particle-clay-creep) strain dt)
  "Pure trial first, publish only validated tensors and scalar state afterward."
  (let* ((j (cl-mpm/fastmaths:det-3x3 (cl-mpm/particle::mp-deformation-gradient mp)))
         (kappa-old (slot-value mp 'kappa-committed)))
    (unless (and (finite-number-p j) (> j 0d0))
      (error "Clay creep requires a finite positive deformation Jacobian."))
    (unless (and (typep strain 'magicl:matrix/double-float)
                 (= (cl-mpm/utils:nrows strain) 6) (= (cl-mpm/utils:ncols strain) 1))
      (error "Clay native adapter requires a 6x1 engineering strain matrix."))
    (let* ((result (clay-creep-update
                    (cl-mpm/utils:fast-storage strain)
                    (cl-mpm/particle::mp-E mp) (cl-mpm/particle::mp-nu mp)
                    (particle-creep-law mp) kappa-old dt
                    :enabled (and (particle-enable-creep mp)
                                  (cl-mpm/particle::mp-enable-plasticity mp))))
           (work (+ (slot-value mp 'work-committed) (clay-creep-result-work result)))
           (native-total (* 1.5d0 (clay-creep-result-kappa result)))
           (native-increment (* 1.5d0 (clay-creep-result-delta result)))
           (p-wave-0 (cl-mpm/particle::calculate-p-wave-modulus
                      (cl-mpm/particle::mp-E mp) (cl-mpm/particle::mp-nu mp)))
           (elastic-matrix (cl-mpm/utils:voigt-from-list
                            (coerce (clay-creep-result-elastic-strain result) 'list)))
           (p-wave (* (/ p-wave-0 j)
                      (exp (- (cl-mpm/fastmaths::min-eigenvalue-3x3 elastic-matrix)))))
           (targets (list (cl-mpm/particle:mp-strain mp)
                          (cl-mpm/particle::mp-stress-kirchoff mp)
                          (cl-mpm/particle::mp-strain-plastic mp))))
      (unless (and (finite-number-p work) (finite-number-p native-total)
                   (finite-number-p native-increment) (finite-number-p p-wave) (> p-wave 0d0)
                   (every (lambda (target) (and (typep target 'magicl:matrix/double-float)
                                               (= (cl-mpm/utils:nrows target) 6)
                                               (= (cl-mpm/utils:ncols target) 1))) targets))
        (error "Invalid clay native target storage or accumulated plastic work."))
      (replace (cl-mpm/utils:fast-storage (first targets)) (clay-creep-result-elastic-strain result))
      (replace (cl-mpm/utils:fast-storage (second targets)) (clay-creep-result-tau result))
      (replace (cl-mpm/utils:fast-storage (third targets)) (clay-creep-result-plastic-increment result))
      (setf (particle-kappa mp) (clay-creep-result-kappa result)
            (particle-rate mp) (clay-creep-result-rate result)
            (particle-current-yield mp) (clay-creep-result-yield result)
            (particle-work mp) work
            (cl-mpm/particle::mp-strain-plastic-vm mp) native-total
            (cl-mpm/particle::mp-strain-plastic-vm-inc mp) native-increment
            (cl-mpm/particle::mp-yield-func mp)
            (- (clay-creep-result-q result) (clay-creep-result-yield result))
            (cl-mpm/particle::mp-p-modulus-0 mp) p-wave-0
            (cl-mpm/particle::mp-p-modulus mp) p-wave
            (cl-mpm/particle::mp-plastic-iterations mp) 0)
      (cl-mpm/particle::mp-stress-kirchoff mp))))
