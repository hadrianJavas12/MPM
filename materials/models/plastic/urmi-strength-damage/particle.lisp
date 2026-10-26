;;;; Undrained-only optional particle. A drained->undrained state transfer needs
;;;; its own atomic point gate before any recipe/MPM integration is authorized.
(in-package :cl-mpm/models/urmi-strength-damage)

(defclass particle-urmi-strength-damage (mc:particle-mc-evolution)
  ((kappa-origin :initarg :kappa-origin :initform 0d0 :reader particle-kappa-origin))
  (:default-initargs :E +youngs-modulus-pa+ :nu +poisson-ratio+ :enable-plasticity t)
  (:documentation "Undrained S1 MC strength degradation. D is derived, never stored or used to reduce stiffness."))

(defmethod mc:particle-transaction-slots ((mp particle-urmi-strength-damage))
  (append (call-next-method) '(kappa-origin)))

(defmethod initialize-instance :around ((mp particle-urmi-strength-damage) &rest initargs
                                        &key (kappa-origin 0d0) &allow-other-keys)
  (unless (and (mc::finite-real-p kappa-origin) (>= kappa-origin 0d0))
    (mc::integration-fail "Invalid owned activation kappa origin" kappa-origin))
  (let* ((missing (gensym)) (given-kappa (getf initargs :kappa missing))
         (given-law (getf initargs :evolution-law missing))
         (law (make-strength-damage-law :kappa-origin kappa-origin))
         (args (copy-list initargs)))
    (when (and (> kappa-origin 0d0) (eq given-kappa missing))
      (mc::integration-fail "Preserving nonzero origin requires explicit accumulated kappa"))
    (unless (and (mc::finite-real-p (if (eq given-kappa missing) 0d0 given-kappa))
                 (>= (if (eq given-kappa missing) 0d0 given-kappa) kappa-origin)
                 (= (getf args :E +youngs-modulus-pa+) +youngs-modulus-pa+)
                 (= (getf args :nu +poisson-ratio+) +poisson-ratio+))
      (mc::integration-fail "Owned S1 elasticity/history must match its declared undrained model"))
    (unless (or (eq given-law missing) (equalp given-law law))
      (mc::integration-fail "Particle requires the exact owned shifted strength-damage law"))
    (remf args :evolution-law) (remf args :kappa-origin)
    (apply #'call-next-method mp :evolution-law law :kappa-origin (float kappa-origin 1d0) args)))

(defun particle-strength-damage (mp)
  "Read-only actual constitutive strength loss, including successful trial/rollback state."
  (check-type mp particle-urmi-strength-damage)
  (let ((c (mc:particle-cohesion mp)))
    (unless (and (mc::finite-real-p c) (<= +remolded-strength-pa+ c +peak-strength-pa+))
      (mc::integration-fail "Accepted owned cohesion is outside the declared strength bounds" c))
    (- 1d0 (/ c +peak-strength-pa+))))

(defun particle-reference-info (mp)
  "Read-only model metadata with the particle's preserved activation origin."
  (check-type mp particle-urmi-strength-damage)
  (let ((record (strength-damage-reference)))
    (setf (gethash "kappaOrigin" record) (particle-kappa-origin mp)
          (gethash "peakKappa" record) (mc:evolution-law-peak-kappa (mc:particle-evolution-law mp))
          (gethash "cohesionKnots_kappa_cPa" record)
          (map 'vector (lambda (node) (coerce (copy-list node) 'vector))
               (mc:evolution-law-cohesion-points (mc:particle-evolution-law mp))))
    record))
