(in-package :cl-mpm/calibration/triaxial)

(defun j-of (mp)
  (cl-mpm/fastmaths:det-3x3 (cl-mpm/particle:mp-deformation-gradient mp)))
