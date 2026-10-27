;;;; FIRST owned point controls only; no MPM, old suites or physical validation.
;;;; windows\cl-mpm.cmd tests\benchmarks\urmi-damage40-pipeline-controls.lisp output\FRESH
(in-package :cl-user)
(require :asdf)
(setf *read-default-float-format* 'double-float)
(defvar *up-frozen* nil) (defvar *up-directory* nil) (defvar *up-exit* 1)
(unless *up-frozen* (load (cl-mpm-path "scripts/lisp/native-source-snapshot.lisp")))
(unless *up-frozen*
  (let* ((argument (first (cl-mpm-script-args)))
         (directory (and argument (uiop:ensure-directory-pathname (merge-pathnames argument)))))
    (unless directory (error "Provide fresh point-control output."))
    (when (and (probe-file directory) (or (uiop:directory-files directory) (uiop:subdirectories directory)))
      (error "Preserve existing point evidence."))
    (snapshot-require-fresh-runtime)
    (multiple-value-bind (copied records) (snapshot-case-sources directory *load-truename*)
      (dolist (relative '("research/notes/urmi-mc-damage40-2026-10-26/recipe-plan.md"
                          "cases/benchmarks/urmi-damage40-proper.lisp"))
        (let* ((from (cl-mpm-path relative)) (to (merge-pathnames (concatenate 'string "source/inputs/" relative) directory))
               (bytes (case-source-bytes from)))
          (ensure-directories-exist to) (uiop:copy-file from to)
          (assert (equalp bytes (case-source-bytes to))) (push to copied)
          (push (snapshot-object "path" (enough-namestring to directory) "originalPath" (namestring (truename from))
                 "bytes" (length bytes) "sha256" (snapshot-sha256-bytes bytes)) records)))
      (dolist (required '("source/materials/models/plastic/urmi-strength-damage/package.lisp"
                          "source/materials/models/plastic/urmi-strength-damage/law.lisp"
                          "source/materials/models/plastic/urmi-strength-damage/particle.lisp"
                          "source/scenarios/urmi-damage40/package.lisp"
                          "source/scenarios/urmi-damage40/transfer.lisp"
                          "source/scenarios/urmi-damage40/runner.lisp"
                          "source/inputs/studio/reference/urmi-damage40.json"
                          "source/inputs/cases/benchmarks/urmi-damage40-proper.lisp"))
        (assert (find required records :key (lambda (row) (gethash "path" row)) :test #'string=)))
      (snapshot-write-json (merge-pathnames "source/source-manifest.json" directory)
       (snapshot-object "scope" "New optional S1 bounded native pipeline controls and recipe plan; all selected first-party/DLL bytes frozen before load"
                        "files" (coerce records 'vector)))
      (let ((*native-snapshot-context* (snapshot-register-native directory records))
            (*up-frozen* t) (*up-directory* directory))
        (snapshot-check-plan "cl-mpm/settings") (ql:quickload :cl-mpm/settings :silent t)
        (setf (symbol-value (find-symbol "*OPTIMISE-SETTING*" "CL-MPM/SETTINGS"))
              '(optimize (speed 3) (safety 1) (debug 1) (compilation-speed 0)))
        (dolist (system '("yason" "cl-mpm" "cl-mpm-framework/urmi-damage40-proper"))
          (snapshot-check-plan system) (ql:quickload system :silent t))
        (snapshot-native-proof)
        (write-case-source-provenance directory copied nil)
        (rename-file (merge-pathnames "source-provenance.json" directory)
                     (merge-pathnames "source-provenance-before.json" directory))
        (flet ((proof (name)
                 (snapshot-write-json (merge-pathnames name directory)
                  (snapshot-object "files" (coerce (mapcar (lambda (path)
                    (snapshot-object "path" (enough-namestring path directory) "sha256" (snapshot-sha256 path))) copied) 'vector)))))
          (proof "source-proof-before.json")
          (snapshot-verify-file (merge-pathnames "source/case.lisp" directory))
          (load (merge-pathnames "source/case.lisp" directory))
          (dolist (path copied) (snapshot-verify-file path))
          (write-case-source-provenance directory copied nil)
          (proof "source-proof-after.json")))))
  (uiop:quit *up-exit*))



(in-package :cl-mpm/scenario/urmi-damage40)
(let* ((fw:*input-root* (merge-pathnames "source/inputs/" cl-user::*up-directory*))
       (fw:*simulation* nil))
  (load (merge-pathnames "source/inputs/cases/benchmarks/urmi-damage40-proper.lisp" cl-user::*up-directory*))
  (let* ((cfg (compile-proper-configuration fw:*simulation*))
         (sim (proper-setup (build-slope (fw:simulation-material fw:*simulation*) cfg :sim-type 'urmi-proper-sim)))
         (node (cl-mpm/mesh:get-node (cl-mpm:sim-mesh sim) '(1 1 0)))
         (mp (aref (cl-mpm:sim-mps sim) 0)))
    (assert (= (length (cl-mpm:sim-mps sim)) 3503))
    (setf (cl-mpm/mesh:node-active node) t (cl-mpm/mesh:node-mass node) 1d0)
    (setf (magicl:tref (cl-mpm/mesh:node-velocity node) 0 0) 1d0
          (magicl:tref (cl-mpm/mesh::node-external-force node) 0 0) 2d0)
    (cl-mpm::calculate-forces-cundall node .75d0 .1d0 1d0)
    (assert (< (abs (- (magicl:tref (cl-mpm/mesh:node-velocity node) 0 0) 1.05d0)) 1d-12))
    ;; Default disabled hook delegates to the existing unmodified engine primary.
    (let* ((expected (aref (cl-mpm:sim-mps
                            (build-slope (fw:simulation-material fw:*simulation*) cfg)) 0))
           (*proper-volume-domain* nil))
      (cl-mpm::update-particle-kirchoff (cl-mpm:sim-mesh sim) expected 0d0)
      (cl-mpm::update-domain-polar (cl-mpm:sim-mesh sim) expected 0d0)
      (cl-mpm::update-particle (cl-mpm:sim-mesh sim) mp 0d0)
      (dotimes (i 2) (assert (= (component (cl-mpm/particle::mp-domain-size mp) i)
                               (component (cl-mpm/particle::mp-domain-size expected) i)))))
    ;; Initial actual native state for the NEW filled renderer integration only.
    ;; No equilibrium or dynamic result is claimed from this initialization.
    (let ((ctx (capture-reference sim cfg)))
      (configure-output sim)
      (cl-mpm/scenario/urmi-damage40/output-streams:with-retained-output-file (h (merge-pathnames "initial-history.csv" cl-user::*up-directory*))
        (cl-mpm/scenario/urmi-damage40/output-streams:with-retained-output-file (p (merge-pathnames "initial-material-state.csv" cl-user::*up-directory*))
          (write-headers h p)
          (save-state sim ctx cfg (merge-pathnames "initial.vtk" cl-user::*up-directory*) 0 0 0 h p))))
    (write-json (merge-pathnames "profile-controls.json" cl-user::*up-directory*)
      (obj "status" "PASS" "groups" 4 "particles" 3503 "mpmUpdates" 0
        "scope" "Actual case compile, local force damping, disabled-hook delegation, initial filled-render input only"))
    (setf cl-user::*up-exit* 0)))
