(in-package :cl-mpm/calibration/triaxial)

(defun vec (mp key)
  (funcall key mp))

(defun component (matrix i)
  (cl-mpm/utils:varef matrix i))

(defun (setf component) (new-value matrix i)
  (setf (cl-mpm/utils:varef matrix i) new-value))
