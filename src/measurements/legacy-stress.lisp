(in-package :cl-mpm/calibration/triaxial)

(defun qj2-of (stress)
  (sqrt (* 3d0 (cl-mpm/fastmaths::voigt-j2
               (cl-mpm/utils::deviatoric-voigt stress)))))
