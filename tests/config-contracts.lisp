;;;; Backend/JSON construction contracts only; no solver timesteps.
;;;; windows\cl-mpm.cmd tests\config-contracts.lisp
(in-package :cl-user)
(ql:quickload :cl-mpm-framework :silent t)
(in-package :cl-mpm/framework)

(defvar *config-checks* 0)
(defun config-check (name function)
  (funcall function) (incf *config-checks*) (format t "~&PASS: ~A~%" name))
(defun config-error-p (function)
  (handler-case (progn (funcall function) nil) (error () t)))
(defun config-object (&rest entries)
  (apply #'cl-mpm/calibration/triaxial::object entries))
(defun config-valid (config)
  (cl-mpm/calibration/triaxial::validate-config config))
(defun config-equal-p (left right)
  (and (= (hash-table-count left) (hash-table-count right))
       (loop for key being the hash-keys of left using (hash-value input)
             always (multiple-value-bind (other present) (gethash key right)
                      (and present (equalp input other))))))
(defun config-test-case (&optional parameters (material (make-material :von-mises)))
  (make-simulation :scenario :triaxial :parameters parameters :material material
   :geometry (make-geometry :rectangle :width 0.02d0 :height 0.04d0)
   :boundary (make-boundary :confinement)
   :loading (make-loading :compression)
   :solver (make-solver :explicit :mesh-size 0.01d0 :mps-per-cell 1 :workers 1)))
(defun with-config-json (text function)
  (let ((path (merge-pathnames
               (format nil "cl-mpm-config-~D-~D.json" (get-universal-time) (random 1000000000))
               (uiop:temporary-directory))))
    (unwind-protect
         (progn
           (with-open-file (stream path :direction :output :if-exists :error)
             (write-string text stream))
           (funcall function path))
      (when (probe-file path) (delete-file path)))))

(setf *config-checks* 0)
(config-check "Existing default files validate without mutation or numeric normalization"
 (lambda ()
   (dolist (path '("calibration/triaxial-demo.json" "calibration/triaxial-2d.json"
                   "calibration/triaxial-homogeneous.json" "calibration/triaxial-controls.json"))
     (let* ((config (read-parameters path)) (before (alexandria:copy-hash-table config)))
       (assert (eq (config-valid config) config))
       (assert (config-equal-p config before))))
   (let ((empty (config-object)))
     (assert (eq (config-valid empty) empty))
     (assert (zerop (hash-table-count empty))))))

(config-check "Unknown keys reject through backend validation and public composition"
 (lambda ()
   (dolist (config (list (config-object "youngModulusPa" 5d6)
                         (config-object :workers 1) (config-object "phiDegrees" 30)))
     (assert (config-error-p (lambda () (config-valid config))))
     (assert (config-error-p (lambda () (compile-scenario :triaxial (config-test-case config))))))))

(config-check "Physical ranges and nonfinite inputs reject; valid boundary values remain accepted"
 (lambda ()
   (dolist (entry (list (list "diameterMm" 0) (list "heightMm" -1)
                        (list "meshSizeMm" 0) (list "youngsModulusPa" 0)
                        (list "densityKgM3" -1) (list "undrainedStrengthPa" 0)
                        (list "cellPressurePa" -1) (list "poissonRatio" -1)
                        (list "poissonRatio" 0.5d0) (list "loadingDurationS" 0)
                        (list "rampDurationS" -1) (list "timeStepScale" 0)
                        (list "dampingPerS" -1) (list "penaltyModulusScale" 0)
                        (list "targetAxialStrainPct" 0) (list "targetAxialStrainPct" 30)
                        (list "youngsModulusPa" sb-ext:double-float-positive-infinity)
                        (list "youngsModulusPa" (sb-kernel:make-double-float #x7ff80000 0))
                        (list "densityKgM3" (expt 10 1000))))
     (assert (config-error-p (lambda () (config-valid (apply #'config-object entry))))))
   (config-valid (config-object "cellPressurePa" 0 "dampingPerS" 0 "rampDurationS" 0
                                "poissonRatio" -0.5d0))
   (assert (config-error-p
            (lambda () (compile-scenario :triaxial
                         (config-test-case nil (make-material :von-mises :poisson-ratio 0.5d0))))))))

(config-check "Counts must be integral and in range instead of silently rounding"
 (lambda ()
   (dolist (entry '(("workers" 0) ("workers" 1.5d0) ("mpsPerCell" 0)
                    ("mpsPerCell" 4) ("mpsPerCell" 1.25d0) ("frames" 1)
                    ("frames" 2.5d0) ("maxUpdates" 0) ("maxUpdates" 3.5d0)
                    ("increments" 0) ("increments" 1.5d0)
                    ("spatialDimensions" 4) ("spatialDimensions" 2.5d0)))
     (assert (config-error-p (lambda () (config-valid (apply #'config-object entry))))))
   ;; Integral floating-point values were accepted by the historical backend.
   (config-valid (config-object "workers" 1d0 "mpsPerCell" 1d0 "frames" 2d0))))

(config-check "Mode and coupled loading/frame constraints fail before any output directory"
 (lambda ()
   (let ((directory (merge-pathnames
                     (format nil "cl-mpm-invalid-config-~D-~D/" (get-universal-time) (random 1000000000))
                     (uiop:temporary-directory))))
     (assert (not (probe-file directory)))
     (dolist (config (list (config-object "mode" "unknown") (config-object "mode" 7)
                           (config-object "mode" "homogeneous" "spatialDimensions" 2)
                           (config-object "loadingDurationS" 0.001d0 "rampDurationS" 0.01d0)
                           (config-object "mode" "homogeneous" "frames" 5 "increments" 2)))
       (assert (config-error-p
                (lambda () (cl-mpm/calibration/triaxial:run-config config directory))))
       (assert (not (probe-file directory))))
     (assert (config-error-p
              (lambda () (compile-scenario :triaxial
                           (config-test-case (config-object "mode" "unknown")))))))))

(config-check "JSON duplicate keys reject at every object scope, including escaped names and schema preflight"
 (lambda ()
   (dolist (text '("{\"workers\":1,\"workers\":2}"
                    "{\"outer\":{\"workers\":1,\"workers\":2}}"
                    "{\"mode\":\"mpm\",\"\\u006dode\":\"homogeneous\"}"))
     (with-config-json text
       (lambda (path) (assert (config-error-p (lambda () (read-parameters path)))))))
   (with-config-json "{\"meshSize\":4,\"meshSize\":8}"
     (lambda (path) (assert (config-error-p (lambda () (read-parameters path :schema t))))))
   (with-config-json "{\"a\":{\"x\":1},\"b\":{\"x\":2}}"
     (lambda (path)
       (let ((input (read-parameters path)))
         (assert (= (gethash "x" (gethash "a" input)) 1))
         (assert (= (gethash "x" (gethash "b" input)) 2)))))))

(config-check "One top-level object is required and trailing JSON content is rejected"
 (lambda ()
   (dolist (text '("[]" "null" "false" "{} {}" "{} true"))
     (with-config-json text
       (lambda (path) (assert (config-error-p (lambda () (read-parameters path)))))))))

(config-check "Null stays distinct from false and rejects numeric/boolean backend parameters"
 (lambda ()
   (dolist (key '("enablePlasticity" "workers" "mode" "densityKgM3"))
     (with-config-json (format nil "{~S:null}" key)
       (lambda (path)
         (let ((input (read-parameters path)))
           (assert (eq (gethash key input) :null))
           (assert (config-error-p (lambda () (config-valid input))))))))
   (dolist (input '("false" 0 :false :null))
     (assert (config-error-p
              (lambda () (config-valid (config-object "enablePlasticity" input))))))))

(config-check "JSON false remains NIL and actually disables plasticity on native particles"
 (lambda ()
   (with-config-json "{\"enablePlasticity\":false}"
     (lambda (path)
       (let* ((parameters (read-parameters path)) (case (config-test-case parameters))
              (config (compile-scenario :triaxial case))
              (material (resolve-material
                         (simulation-material case) config
                         '((:youngs-modulus "youngsModulusPa" 5d6)
                           (:poisson-ratio "poissonRatio" 0.49d0)
                           (:density "densityKgM3" 1800d0)
                           (:undrained-strength "undrainedStrengthPa" 25d3)
                           (:plasticity "enablePlasticity" t))))
              (sim (cl-mpm/calibration/triaxial:setup
                    config :particle-factory (make-particle-factory material)
                    :diagnostics (material-diagnostics material)
                    :geometry-filter (geometry-filter (simulation-geometry case)))))
         (assert (null (gethash "enablePlasticity" parameters)))
         (assert (null (gethash "enablePlasticity" config)))
         (assert (plusp (length (cl-mpm:sim-mps sim))))
         (loop for particle across (cl-mpm:sim-mps sim)
               do (assert (null (cl-mpm/particle::mp-enable-plasticity particle)))))))))

(config-check "Schema mode retains legacy normalization and config/case state is isolated"
 (lambda ()
   (let* ((path "studio/reference/joss-bay-accepted-collapse.json")
          (legacy (cl-mpm/framework/config:load-config (case-path path)))
          (preflight (read-parameters path :schema t)))
     (assert (config-equal-p legacy preflight)))
   (let* ((parameters (config-object "cellPressurePa" 50d3 "enablePlasticity" nil))
          (before (alexandria:copy-hash-table parameters))
          (case (config-test-case parameters))
          (first (compile-scenario :triaxial case)) (second (compile-scenario :triaxial case)))
     (setf (gethash "cellPressurePa" first) 75d3)
     (assert (= (gethash "cellPressurePa" second) 50d3))
     (assert (config-equal-p parameters before))
     (assert (config-equal-p (simulation-parameters case) before))
     (assert (null (gethash "enablePlasticity" second))))))

(format t "~&CONFIG CONTRACTS: ~D passed; no solver timesteps executed.~%" *config-checks*)
(uiop:quit 0)
