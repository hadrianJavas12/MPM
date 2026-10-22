;;;; Homogeneous slope under a prescribed, finite-compliance crest descent.
(defpackage :cl-mpm/scenario/slope-descent
  (:use :cl)
  (:export #:compile-configuration #:run #:make-slope #:make-strip
           #:strip-target #:strip-contacts #:strip-reaction #:strip-mapped-reaction
           #:strip-measurements #:contact-reference-y #:contact-width #:contact-mp))
(in-package :cl-mpm/scenario/slope-descent)

(defun finite-p (x)
  (and (realp x) (not (sb-ext:float-nan-p (float x 1d0)))
       (not (sb-ext:float-infinity-p (float x 1d0)))))

(defun number-at (config key) (gethash key config))
(defun component (matrix axis) (magicl:tref matrix axis 0))
(defun matrix-finite-p (matrix)
  (every #'finite-p (cl-mpm/utils:fast-storage matrix)))

(defun json-object (&rest entries)
  (let ((object (make-hash-table :test 'equal)))
    (loop for (key value) on entries by #'cddr do (setf (gethash key object) value))
    object))

(defun write-json (path object)
  (with-open-file (stream path :direction :output :if-exists :supersede
                                  :if-does-not-exist :create)
    (yason:encode object stream)))
