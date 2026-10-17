(in-package :cl-mpm/calibration/triaxial)

(defun json-file (path object)
  (with-open-file (stream path :direction :output :if-exists :supersede)
    (yason:encode object stream)))

(defun object (&rest entries)
  (let ((h (make-hash-table :test 'equal)))
    (loop for (k v) on entries by #'cddr do (setf (gethash k h) v)) h))
