;;;; Reference material/state measurements and finite checks.
;;;; Extracted without changing the existing numerical expressions.
(in-package :cl-mpm/framework/cliff)

(defun reference-summary (sim)
  (let ((mass 0d0) (damage-mass 0d0))
    (loop for mp across (cl-mpm:sim-mps sim) do
      (incf mass (cl-mpm/particle:mp-mass mp))
      (incf damage-mass (* (cl-mpm/particle:mp-mass mp) (cl-mpm/particle:mp-damage mp))))
    (values mass damage-mass)))

(defun reference-effective-material (sim)
  "Record the initialized material fields, including inherited constructor effects."
  (let ((mp (aref (cl-mpm:sim-mps sim) 0))
        (values (make-hash-table :test #'equal)))
    (setf (gethash "E" values) (cl-mpm/particle::mp-E mp)
          (gethash "nu" values) (cl-mpm/particle::mp-nu mp)
          (gethash "plasticCohesion" values) (cl-mpm/particle::mp-c mp)
          (gethash "plasticFrictionRadians" values) (cl-mpm/particle::mp-phi mp)
          (gethash "damageFrictionRadians" values) (cl-mpm/particle::mp-friction-angle mp)
          (gethash "damageInitiationStress" values) (cl-mpm/particle::mp-initiation-stress mp)
          (gethash "ductility" values) (cl-mpm/particle::mp-ductility mp)
          (gethash "nonlocalLength" values) (cl-mpm/particle::mp-local-length mp)
          (gethash "delayTime" values) (cl-mpm/particle::mp-delay-time mp)
          (gethash "damageDelayExponent" values) (cl-mpm/particle::mp-delay-exponent mp)
          (gethash "residualTensileRatio" values) (cl-mpm/particle::mp-k-tensile-residual-ratio mp)
          (gethash "residualCompressionRatio" values) (cl-mpm/particle::mp-k-compressive-residual-ratio mp)
          (gethash "residualShearRatio" values) (cl-mpm/particle::mp-shear-residual-ratio mp))
    values))

(defun reference-check-finite (sim)
  (loop for mp across (cl-mpm:sim-mps sim) do
    (dolist (value (list (cl-mpm/particle:mp-mass mp) (cl-mpm/particle:mp-volume mp)
                        (cl-mpm/particle:mp-damage mp) (cl-mpm/particle::mp-history-stress mp)))
      (unless (reference-finite-p value) (error "Nonfinite reference particle state")))
    (unless (and (> (cl-mpm/particle:mp-mass mp) 0d0)
                 (> (cl-mpm/particle:mp-volume mp) 0d0)
                 (<= 0d0 (cl-mpm/particle:mp-damage mp) 1d0))
      (error "Invalid reference particle mass/volume/damage bounds"))
    (dolist (vector (list (cl-mpm/particle:mp-position mp) (cl-mpm/particle:mp-velocity mp)
                         (cl-mpm/particle:mp-stress mp) (cl-mpm/particle::mp-domain-size mp)))
      (loop for value across (cl-mpm/utils::fast-storage vector) do
        (unless (reference-finite-p value) (error "Nonfinite reference position/velocity/stress/domain"))))
    (unless (and (> (cl-mpm/utils:varef (cl-mpm/particle::mp-domain-size mp) 0) 0d0)
                 (> (cl-mpm/utils:varef (cl-mpm/particle::mp-domain-size mp) 1) 0d0))
      (error "Invalid reference GIMP domain dimensions")))
  t)
