;;;; Replay ONLY the captured pure return, never an MPM restart or a Lisp input.
;;;; windows\cl-mpm.cmd scripts\replay-mc-failure.lisp CAPSULE.json FRESH-summary.json
(in-package :cl-user)
(require :asdf)
(ql:quickload '(:cl-mpm/models/mc-evolution :yason) :silent t)
(let* ((args (cl-mpm-script-args)) (input (first args)) (output (second args)))
  (unless (and (= (length args) 2) input output)
    (error "Usage: windows\\cl-mpm.cmd scripts\\replay-mc-failure.lisp CAPSULE.json FRESH-summary.json"))
  (let* ((record (with-open-file (stream input)
                   (yason:parse stream :object-as :hash-table :json-arrays-as-vectors t)))
         (failure
           (handler-case
               (progn (cl-mpm/models/mc-evolution:replay-integration-diagnostic record)
                      (error "Captured return did not reproduce a material failure."))
             (cl-mpm/models/mc-evolution:material-integration-error (condition) condition)))
         (replayed (cl-mpm/models/mc-evolution:integration-error-diagnostic failure))
         (summary (make-hash-table :test 'equal)))
    (unless (equalp record replayed)
      (error "Replayed failure payload differs; inspect source version and captured inputs."))
    (setf (gethash "passed" summary) t
          (gethash "scope" summary) "Exact JSON-input pure principal-return failure reproduction; not a whole-MPM restart"
          (gethash "physicalUpdatesExecuted" summary) 0
          (gethash "reason" summary) (gethash "reason" replayed)
          (gethash "diagnostic" summary) replayed)
    (ensure-directories-exist output)
    (with-open-file (stream output :direction :output :if-exists :error)
      (yason:encode summary stream))
    (format t "~&MC failure replay PASS: ~A~%" (gethash "reason" summary))))
(uiop:quit 0)
