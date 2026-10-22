;;;; Keep diagnostic history on abnormal exits; no solver or material state changes.
(defpackage :cl-mpm/output/history
  (:use :cl)
  (:export #:with-retained-history))

(in-package :cl-mpm/output/history)

(defun close-retained-stream (stream)
  ;; WITH-OPEN-FILE closes with :ABORT T during stack unwinding. For a newly
  ;; created :SUPERSEDE file, that can delete even already flushed evidence.
  (close stream :abort nil))

(defmacro with-retained-history ((stream filespec &rest options) &body body)
  "Like WITH-OPEN-FILE, but retain written evidence when BODY exits abnormally.
Close with :ABORT NIL in all cases. Propagate normal close errors; a cleanup
error must not replace the original error or other nonlocal exit from BODY."
  (let ((completed (gensym "COMPLETED")))
    `(let ((,stream (open ,filespec ,@options))
           (,completed nil))
       (unwind-protect
            (multiple-value-prog1 (locally ,@body)
              (setf ,completed t))
         (when ,stream
           (if ,completed
               (close-retained-stream ,stream)
               (ignore-errors (close-retained-stream ,stream))))))))
