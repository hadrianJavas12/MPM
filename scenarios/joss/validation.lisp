(in-package :cl-mpm/framework/cliff)

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
