(in-package :cl-mpm/models/visco)

(declaim (optimize (debug 3) (safety 3) (speed 0)))




(defun voight-trace-2d (s)
  (+ (varef s 0)
     (varef s 1)))
(defun voigt-eye-2d (v)
  (cl-mpm/utils:voigt-from-list
   (list
    v
    v
    0d0
    0d0
    0d0
    0d0)))
