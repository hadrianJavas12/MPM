;;;; A gravity-only, unnotched slope recipe. No constitutive law is defined here.
(defpackage :cl-mpm/scenario/gravity-slope
  (:use :cl)
  (:export #:compile-configuration #:build-slope #:run #:ramp-factor))

(in-package :cl-mpm/scenario/gravity-slope)

(defun finite-p (value)
  (and (realp value)
       (not (sb-ext:float-nan-p (float value 1d0)))
       (not (sb-ext:float-infinity-p (float value 1d0)))))

(defun component (matrix axis)
  (magicl:tref matrix axis 0))

(defun matrix-finite-p (matrix)
  (every #'finite-p (cl-mpm/utils:fast-storage matrix)))

(defun json-object (&rest entries)
  (let ((object (make-hash-table :test 'equal)))
    (loop for (key value) on entries by #'cddr
          do (setf (gethash key object) value))
    object))

(defun write-json (path object)
  (with-open-file (stream path :direction :output :if-exists :supersede
                               :if-does-not-exist :create)
    (yason:encode object stream)))
