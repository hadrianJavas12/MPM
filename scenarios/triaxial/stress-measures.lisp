(in-package :cl-mpm/calibration/triaxial)

(defun q-of (stress)
  (- (* -1d0 (component stress 1))
     (* -0.5d0 (+ (component stress 0) (component stress 2)))))
