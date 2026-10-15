;;;; Construct and inspect the full reference geometry without time integration.
;;;; windows\cl-mpm.cmd scripts\joss-reference-geometry.lisp [config.json] [output-dir]
(in-package :cl-user)
(ql:quickload :cl-mpm-studio :silent t)
(let* ((args (cl-mpm-script-args))
       (config (cl-mpm-studio:load-config
                (uiop:parse-native-namestring
                 (or (first args) (namestring (cl-mpm-path "studio/reference/joss-bay-prose.json"))))))
       (output (uiop:ensure-directory-pathname
                (uiop:parse-native-namestring
                 (or (second args) (namestring (cl-mpm-path "output/reference-reproduction-2026-10-14/fine-geometry/"))))))
       (started (get-internal-real-time)))
  (cl-mpm/utils:set-workers (cl-mpm-studio:param config "workers"))
  (ensure-directories-exist output)
  (let ((sim (cl-mpm-studio:make-joss-reference-sim config)))
    (cl-mpm-studio::reference-check-finite sim)
    (cl-mpm/output:save-vtk (merge-pathnames "initial.vtk" output) sim)
    (cl-mpm/output:save-vtk-mesh (merge-pathnames "mesh.vtk" output) sim)
    (cl-mpm-studio::save-frame sim :damage "Joss Bay reference: t=0.00 s - SETTLE"
                             (merge-pathnames "initial.png" output) :timeout-seconds 60d0)
    (multiple-value-bind (mass damage) (cl-mpm-studio::reference-summary sim)
      (with-open-file (stream (merge-pathnames "geometry-summary.json" output) :direction :output :if-exists :supersede)
        (format stream "{~%  ~S: ~D,~%  ~S: ~F,~%  ~S: ~F,~%  ~S: ~F,~%  ~S: false~%}~%"
                "particles" (length (cl-mpm:sim-mps sim)) "massPerUnitDepth" mass
                "meshSize" (cl-mpm-studio:param config "meshSize") "massDamage" damage "collapseValidated"))
      (format t "~&REFERENCE GEOMETRY PASSED: ~D particles, mass ~,8F kg/m, ~,2F wall seconds; no time integration.~%"
              (length (cl-mpm:sim-mps sim)) mass
              (/ (- (get-internal-real-time) started) (float internal-time-units-per-second 1d0))))
    (ignore-errors (vgplot:close-all-plots))))
(uiop:quit 0)
