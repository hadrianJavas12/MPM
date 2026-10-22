;;;; Compile actual 10/20s cases; no gravity, contact application or physical timesteps.
(in-package :cl-user)
(ql:quickload :cl-mpm-framework :silent t)
(in-package :cl-mpm/scenario/slope-creep)

(defun load-hold-extension-case (path)
  (let ((cl-mpm/framework:*simulation* nil))
    (load path)
    (or cl-mpm/framework:*simulation* (error "Case did not declare a simulation."))))

(let* ((output-path (first (cl-user::cl-mpm-script-args)))
       (baseline-path (cl-user::cl-mpm-path "cases/benchmarks/clay-creep-pusher-drive-hold.lisp"))
       (candidate-path (cl-user::cl-mpm-path "cases/benchmarks/clay-creep-pusher-drive-hold-20s.lisp"))
       (baseline (compile-configuration (load-hold-extension-case baseline-path)))
       (candidate (compile-configuration (load-hold-extension-case candidate-path)))
       (expected-changes '("duration" "frames" "maxUpdates"))
       (changed nil))
  (when (and output-path (probe-file output-path))
    (error "Hold-extension preflight requires a fresh output JSON file."))
  (assert (= (hash-table-count baseline) (hash-table-count candidate)))
  (maphash (lambda (key value)
             (multiple-value-bind (actual present-p) (gethash key candidate)
               (assert present-p)
               (unless (equalp value actual) (push key changed))))
           baseline)
  (assert (equal (sort changed #'string<) expected-changes))
  (format t "~&PASS: actual compiled configurations differ only in duration, frames and update budget~%")
  (assert (= (gethash "duration" baseline) 10d0))
  (assert (= (gethash "duration" candidate) 20d0))
  (assert (= (gethash "frames" baseline) 101))
  (assert (= (gethash "frames" candidate) 201))
  (let ((before-cadence (/ (gethash "duration" baseline) (1- (gethash "frames" baseline))))
        (after-cadence (/ (gethash "duration" candidate) (1- (gethash "frames" candidate)))))
    (assert (= before-cadence after-cadence .1d0))
    (format t "PASS: 10/20s durations and 101/201 states preserve exact 0.1s output cadence~%")
    (assert (= (gethash "maxUpdates" baseline) 30000))
    (assert (= (gethash "maxUpdates" candidate) 60000))
    (assert (every (lambda (config)
                     (let ((budget (gethash "maxUpdates" config)))
                       (and (integerp budget) (plusp budget))))
                   (list baseline candidate)))
    (assert (>= (gethash "maxUpdates" candidate) (gethash "maxUpdates" baseline)))
    (format t "PASS: declared computational cap increases 30000 to 60000; no physics settings differ~%")
    (when output-path
      (ensure-directories-exist output-path)
      (with-open-file (stream output-path :direction :output :if-exists :error
                                          :if-does-not-exist :create)
        (yason:encode
         (json-object "passed" t "controlsPassed" 3 "physicalUpdatesExecuted" 0
                      "scope" "Actual native configuration compilation; no solver or material timesteps"
                      "baselineCase" (namestring baseline-path)
                      "candidateCase" (namestring candidate-path)
                      "changedKeys" (coerce expected-changes 'vector)
                      "physicalConfigurationUnchanged" t
                      "outputCadenceBeforeS" before-cadence
                      "outputCadenceAfterS" after-cadence
                      "updateBudgetBefore" (gethash "maxUpdates" baseline)
                      "updateBudgetAfter" (gethash "maxUpdates" candidate)
                      "updateBudgetNondecreasing" t
                      "baselineConfig" baseline "candidateConfig" candidate)
         stream)))))
(format t "~&SLOPE CREEP HOLD-EXTENSION PREFLIGHT: 3 controls passed; no physical updates executed.~%")
(uiop:quit 0)
