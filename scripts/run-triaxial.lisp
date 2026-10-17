;;;; Trusted local native CL-MPM calibration entry point.
;;;; windows\cl-mpm.cmd scripts\run-triaxial.lisp [config.json] [output-directory]
(in-package :cl-user)
(require :asdf)
(ql:quickload :cl-mpm/settings :silent t)
;; Same source equations, project compiler policy and the existing isolated cache.
(asdf:initialize-output-translations
 (list :output-translations
       (list (cl-mpm-path "src/**/*.*")
             (cl-mpm-path "output/reference-reproduction-2026-10-14/fast-cache-safe/src/**/*.*"))
       :inherit-configuration))
(setf cl-mpm/settings::*optimise-setting*
      '(optimize (speed 3) (safety 1) (debug 1) (compilation-speed 0)))
(ql:quickload '(:cl-mpm :cl-mpm/setup :cl-mpm/output :cl-mpm/penalty :yason) :silent t)
;; Snapshot before LOAD, then execute the snapshot itself. A source file edited
;; during a long run must never be mistaken for the exact loaded harness bytes.
(let* ((args (cl-mpm-script-args))
       (directory (uiop:ensure-directory-pathname
                   (or (second args) (cl-mpm-path "output/triaxial-demo/"))))
       (snapshot (merge-pathnames "source/calibration/triaxial.lisp" directory))
       (modules '("src/simulation/compatibility/triaxial-package.lisp"
                  "scenarios/triaxial/state.lisp"
                  "src/simulation/config/legacy-triaxial-values.lisp"
                  "scenarios/triaxial/config.lisp"
                  "src/output/legacy-triaxial-json.lisp"
                  "materials/adapters/diagnostics-call.lisp"
                  "src/numerics/legacy-tensors.lisp"
                  "src/measurements/legacy-particle.lisp"
                  "scenarios/triaxial/stress-measures.lisp"
                  "src/measurements/legacy-stress.lisp"
                  "materials/adapters/triaxial.lisp"
                  "materials/adapters/legacy-triaxial.lisp"
                  "scenarios/triaxial/geometry.lisp"
                  "src/boundaries/pressure/isotropic.lisp"
                  "scenarios/triaxial/measurements.lisp"
                  "scenarios/triaxial/mpm.lisp"
                  "scenarios/triaxial/homogeneous.lisp"
                  "scenarios/triaxial/controls.lisp"
                  "scenarios/triaxial/runner.lisp"))
       (provenance (make-hash-table :test 'equal)))
  (when (some (lambda (name) (probe-file (merge-pathnames name directory)))
              '("stress-strain.csv" "controls.json" "manifest.json" "source-provenance.json"))
    (error "Output already contains a run: ~A" directory))
  (ensure-directories-exist snapshot)
  (uiop:copy-file (cl-mpm-path "calibration/triaxial.lisp") snapshot)
  (dolist (relative modules)
    (let ((target (merge-pathnames (concatenate 'string "source/" relative) directory)))
      (ensure-directories-exist target)
      (uiop:copy-file (cl-mpm-path relative) target)))
  (uiop:copy-file *load-truename* (merge-pathnames "source/run-triaxial.lisp" directory))
  (setf (gethash "sourceSnapshotExactLoadedBytes" provenance) t
        (gethash "loadedHarness" provenance) (namestring snapshot)
        (gethash "scenarioModuleCount" provenance) (length modules)
        (gethash "scenarioModules" provenance) (coerce modules 'vector)
        (gethash "scope" provenance) "Exact compatibility loader and complete scenario/material/neutral owner closure copied before LOAD and executed from that snapshot; dependency source/FASL and native DLL identity are separate provenance.")
  (with-open-file (stream (merge-pathnames "source-provenance.json" directory)
                          :direction :output :if-exists :supersede)
    (yason:encode provenance stream))
  (load snapshot))
(handler-case
    (progn
      (cl-mpm/calibration/triaxial:main (cl-mpm-script-args))
      (uiop:quit 0))
  (error (condition)
    (format *error-output* "~&TRIAXIAL FAILED: ~A~%" condition)
    (uiop:quit 1)))
