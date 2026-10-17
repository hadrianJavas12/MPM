(in-package :cl-mpm/framework/cliff)

(defun reference-summary (sim)
  (let ((mass 0d0) (damage-mass 0d0))
    (loop for mp across (cl-mpm:sim-mps sim) do
      (incf mass (cl-mpm/particle:mp-mass mp))
      (incf damage-mass (* (cl-mpm/particle:mp-mass mp) (cl-mpm/particle:mp-damage mp))))
    (values mass damage-mass)))
