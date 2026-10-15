;;;; Native triaxial scenario: tensors.lisp
(in-package :cl-mpm/calibration/triaxial)

(defun vec (mp key)
  (funcall key mp))
(defun component (matrix i)
  (cl-mpm/utils:varef matrix i))
(defun (setf component) (new-value matrix i)
  (setf (cl-mpm/utils:varef matrix i) new-value))
(defun j-of (mp)
  (cl-mpm/fastmaths:det-3x3 (cl-mpm/particle:mp-deformation-gradient mp)))
(defun q-of (stress)
  (- (* -1d0 (component stress 1))
     (* -0.5d0 (+ (component stress 0) (component stress 2)))))
(defun qj2-of (stress)
  (sqrt (* 3d0 (cl-mpm/fastmaths::voigt-j2
               (cl-mpm/utils::deviatoric-voigt stress)))))
