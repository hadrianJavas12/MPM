(in-package :cl-user)
(ql:quickload :cl-mpm-framework :silent t)
(load (cl-mpm-path "cases/benchmarks/clay-creep-slope-pilot.lisp"))
(let* ((case cl-mpm/framework:*simulation*)
       (config (cl-mpm/framework:compile-scenario :slope-creep case)))
  (assert (eq :gravity (cl-mpm/framework:component-kind
                       (cl-mpm/framework:simulation-loading case))))
  (assert (and (null (gethash "velocity" config))
               (null (gethash "targetDisplacement" config))
               (= 1d0 (gethash "duration" config))))
  (format t "~&PASS: sustained self-weight with no displacement trajectory~%")
  (multiple-value-bind (sim crest)
      (cl-mpm/scenario/slope-descent:make-slope
       (cl-mpm/framework:simulation-material case) config)
    (let* ((mass (reduce #'+ (cl-mpm:sim-mps sim) :key #'cl-mpm/particle:mp-mass))
           (count (length (cl-mpm:sim-mps sim)))
           (vector-values (cl-mpm/scenario/slope-creep::statistics
                           sim mass count config (coerce crest 'vector)))
           (list-values (cl-mpm/scenario/slope-creep::statistics
                         sim mass count config (coerce crest 'list))))
      (assert (equalp vector-values list-values))
      (assert (= 0d0 (nth 9 vector-values)))
      (assert (= 0d0 (nth 10 vector-values)))
      (format t "PASS: crest measurements support native vector and list sequences~%")))
  (setf (gethash "settleMinUpdates" config) 1
        (gethash "settleMaxUpdates" config) 1)
  (let* ((directory (uiop:ensure-directory-pathname
                    (or (first (cl-mpm-script-args))
                        (error "Pass a fresh negative-control directory."))))
         (manifest (merge-pathnames "manifest.json" directory)))
    (when (probe-file directory) (error "Negative control requires a fresh directory."))
    (handler-case
        (progn (cl-mpm/scenario/slope-creep:run
                (cl-mpm/framework:simulation-material case) config directory)
               (error "Expected gravity initialization failure."))
      (error (condition)
        (unless (search "did not converge" (princ-to-string condition)) (error condition))))
    (let ((text (uiop:read-file-string manifest)))
      (assert (search "\"complete\":false" text))
      (assert (search "\"status\":\"failed\"" text)))
    (assert (probe-file (merge-pathnames "gravity-history.csv" directory)))
    (format t "PASS: bounded failure retains CSV and incomplete native manifest~%")))
(format t "~&Slope creep scenario contracts: 3 controls passed.~%")
(uiop:quit 0)
