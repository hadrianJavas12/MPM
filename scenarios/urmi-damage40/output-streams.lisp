;;;; Owned output retention only. No solver, material, default recipe or restart.
(defpackage :cl-mpm/scenario/urmi-damage40/output-streams
  (:use :cl)
  (:export #:with-retained-output-file))
(in-package :cl-mpm/scenario/urmi-damage40/output-streams)

(defun %report-close-failure (stream condition)
  ;; Reporting must not replace the primary error/nonlocal exit. If stderr
  ;; itself is unavailable, this is necessarily a best-effort diagnostic.
  (handler-case
      (progn
        (format *error-output*
                "~&Owned Urmi output CLOSE failed while preserving an earlier error/nonlocal exit (~S): ~A~%"
                stream condition)
        (finish-output *error-output*))
    (error () nil)))

(defun %close-retained-output (stream normal-completion-p &optional (close-function #'close))
  "Close genuine output with :ABORT NIL even during stack unwinding.
CLOSE-FUNCTION is an internal synthetic-control seam; the production macro
always uses CL:CLOSE. A normal close failure propagates. During an earlier
error/nonlocal exit, report cleanup failure while preserving the earlier exit."
  (handler-case (funcall close-function stream :abort nil)
    (error (condition)
      (if normal-completion-p
          (error condition)
          (%report-close-failure stream condition)))))

(defmacro with-retained-output-file ((stream filespec) &body body)
  "Fresh owned character output whose actual written bytes survive errors.
Unlike WITH-OPEN-FILE's abort close, cleanup explicitly uses :ABORT NIL. This
does not make an incomplete row/frame complete, recover an unwritten state,
or provide crash/power-loss durability. Existing files are never overwritten."
  (let ((completed (gensym "NORMAL-COMPLETION-")))
    `(let ((,stream (open ,filespec :direction :output :if-exists :error
                                    :if-does-not-exist :create))
           (,completed nil))
       (unwind-protect
            (multiple-value-prog1 (progn ,@body)
              (setf ,completed t))
         (%close-retained-output ,stream ,completed)))))
