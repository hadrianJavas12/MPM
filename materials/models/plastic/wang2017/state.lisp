;;;; Plain owned tensor/array/plist state extends the existing MC transaction API.
(in-package :cl-mpm/models/wang2017-native)

(defun make-soil2-law ()
  "Fixed paper Soil2 Cauchy cohesion:30->15kPa over signed-tensor kps0->.02."
  (mc-evolution:make-evolution-law
   :variant :hs :points '((0d0 35d0)) :psi 0d0 :stress-measure :cauchy
   :cohesion-points '((0d0 30000d0) (.02d0 15000d0)) :peak-kappa .02d0
   :strain-assumption "Wang2017 signed spatial Ep norm; incremental polar corotation approximation; reject history decrease beyond1e-13, no healing/max or finite-strain Fp claim"))

(defun soil2-law-p (law)
  "Exact numerical Soil2 curve; descriptive strain/peak metadata is not a curve."
  (and (typep law 'mc-evolution:evolution-law)
       (eq (mc-evolution:evolution-law-variant law) :hs)
       (equalp (mc-evolution:evolution-law-points law) '((0d0 35d0)))
       (equalp (mc-evolution:evolution-law-cohesion-points law) '((0d0 30000d0) (.02d0 15000d0)))
       (eql (mc-evolution:evolution-law-psi law) 0d0)
       (eq (mc-evolution:evolution-law-stress-measure law) :cauchy)))

(defclass particle-wang2017-soil2 (mc-evolution:particle-mc-evolution)
  ((paper-tensor :initarg :paper-tensor :initform (make-array 6 :initial-element 0d0)
                 :accessor %paper-tensor)
   (paper-tensor-committed :initform (make-array 6 :initial-element 0d0)
                           :accessor %paper-tensor-committed)
   (paper-rotation :initform (cl-mpm/utils:matrix-eye 1d0) :accessor %paper-rotation)
   (history-decrease-p :initform nil :accessor %history-decrease-p)
   (paper-diagnostic :initform nil :accessor %paper-diagnostic)
   (legacy-j2-committed :initform 0d0 :accessor %legacy-j2-committed)
   ;; Reusable outer-trial scratch is not persistent material state or a snapshot slot.
   (outer-trial-state :initform nil :accessor %outer-trial-state))
  (:default-initargs :E 20000000d0 :nu .25d0 :evolution-law (make-soil2-law))
  (:documentation "Experimental Soil2 MPM adapter: signed Ep with objective polar corotation, accepted monotonic-history scope only. Not an exact finite-strain paper/FEM reproduction."))

(defmethod mc-evolution:particle-transaction-slots ((mp particle-wang2017-soil2))
  (append (call-next-method)
          '(paper-tensor paper-tensor-committed paper-rotation history-decrease-p
            paper-diagnostic legacy-j2-committed)))

(defun particle-paper-tensor (mp) (copy-seq (%paper-tensor mp)))
(defun particle-paper-tensor-committed (mp) (copy-seq (%paper-tensor-committed mp)))
(defun particle-paper-kps (mp) (mc-evolution:particle-kappa mp))
(defun particle-paper-cohesion (mp) (mc-evolution:particle-cohesion mp))
(defun particle-history-decrease-p (mp) (%history-decrease-p mp))
(defun particle-rotation (mp) (magicl:scale (%paper-rotation mp) 1d0))
(defun particle-last-paper-diagnostic (mp) (mc-evolution::%copy-state-value (%paper-diagnostic mp)))
(defun particle-legacy-j2 (mp) (/ (cl-mpm/particle::mp-strain-plastic-vm mp) 1.5d0))
(defun snapshot-particle (mp) (check-type mp particle-wang2017-soil2) (mc-evolution:snapshot-particle mp))
(defun restore-particle (mp state) (check-type mp particle-wang2017-soil2) (mc-evolution:restore-particle mp state))
(defun copy-particle-state (source target)
  (check-type source particle-wang2017-soil2) (check-type target particle-wang2017-soil2)
  (mc-evolution:copy-particle-state source target))

(defun %validate-fixed-inputs (mp)
  (let ((e (cl-mpm/particle::mp-E mp)) (nu (cl-mpm/particle::mp-nu mp)))
    (unless (and (mc-evolution::finite-real-p e) (> e 0d0)
                 (mc-evolution::finite-real-p nu) (< -1d0 nu .5d0)
                 (soil2-law-p (mc-evolution:particle-evolution-law mp)))
      (mc-evolution::integration-fail "Wang Soil2 requires valid elasticity and the fixed paper cohesion/friction/dilation curve"))))

(defmethod initialize-instance :after ((mp particle-wang2017-soil2) &key (kappa nil kappa-p))
  (%validate-fixed-inputs mp)
  (let* ((tensor (paper::checked-tensor (%paper-tensor mp))) (kps (paper:paper-kps tensor)))
    (when (and kappa-p (not (= kappa kps)))
      (mc-evolution::integration-fail "Supplied Wang kappa differs from the supplied plastic tensor"))
    (setf (%paper-tensor mp) tensor (%paper-tensor-committed mp) (copy-seq tensor)
          (mc-evolution:particle-kappa mp) kps (mc-evolution:particle-kappa-committed mp) kps
          (mc-evolution:particle-cohesion mp) (paper:soil2-cohesion kps)
          ;; Native VM output is an independent additive history, not1.5*paper kps.
          (cl-mpm/particle::mp-strain-plastic-vm mp) 0d0
          (cl-mpm/particle::mp-strain-plastic-vm-1 mp) 0d0
          (cl-mpm/particle::mp-strain-plastic-vm-inc mp) 0d0
          (%legacy-j2-committed mp) 0d0
          (slot-value mp 'mc-evolution::committed-state) (mc-evolution::%capture-particle-state mp))))

(defmethod reinitialize-instance :after ((mp particle-wang2017-soil2) &key)
  (%validate-fixed-inputs mp)
  (dolist (slot '(paper-tensor paper-tensor-committed paper-rotation paper-diagnostic))
    (setf (slot-value mp slot) (mc-evolution::%copy-state-value (slot-value mp slot))))
  (setf (%outer-trial-state mp) nil))

(defmethod cl-mpm/particle::new-loadstep-mp ((mp particle-wang2017-soil2))
  ;; The superclass captures its baseline AFTER call-next-method, so set our
  ;; committed fields first. Repeating this call must not add history or rotate.
  (setf (%paper-tensor-committed mp) (copy-seq (%paper-tensor mp))
        (%legacy-j2-committed mp) (particle-legacy-j2 mp))
  (call-next-method))
