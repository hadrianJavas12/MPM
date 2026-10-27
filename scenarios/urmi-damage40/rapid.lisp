(in-package :cl-mpm/scenario/urmi-damage40)

(defparameter +rapid-inputs+
  (mapcar (lambda (entry)
    (cons (car entry) (or (cdr (assoc (car entry)
      '(("meshSize" . 2d0) ("mpsPerCell" . 1) ("duration" . 20d0) ("frames" . 41)
        ("maxPreparationTimeS" . 3d0) ("maxPreparationUpdates" . 5000)
        ("maxDynamicUpdates" . 20000)) :test #'string=)) (cdr entry)))) +fixed-inputs+))

(defun compile-rapid-configuration (case)
  "Separate exact rough-demo profile; strict configuration/defaults remain unchanged."
  (let ((actual (fw:simulation-parameters case))
        (material (fw:simulation-material case)) (geometry (fw:simulation-geometry case))
        (solver (fw:simulation-solver case)))
    (unless (= (hash-table-count actual) (length +rapid-inputs+)) (error "Rapid input keys differ."))
    (dolist (entry +rapid-inputs+)
      (unless (and (gs::finite-p (gethash (car entry) actual)) (= (gethash (car entry) actual) (cdr entry)))
        (error "Rapid parameter differs: ~A" (car entry))))
    (dolist (entry '((:mesh-size . 2d0) (:mps-per-cell . 1) (:workers . 1) (:time-step-scale . .2d0)
                     (:frames . 41) (:max-updates . 20000) (:damping . 0d0)))
      (unless (= (fw:option solver (car entry)) (cdr entry)) (error "Rapid solver option differs: ~S" entry)))
    (fw::check-kind solver '(:explicit))
    ;; Reuse the strict material/geometry/boundary validation with its own full
    ;; configuration, then expose every deliberate demo override in actual config.
    (let ((strict-input (make-hash-table :test #'equal)))
      (dolist (entry +fixed-inputs+) (setf (gethash (car entry) strict-input) (cdr entry)))
      (let* ((strict (fw:make-simulation :scenario :urmi-damage40 :parameters strict-input
               :material material :geometry geometry :boundary (fw:simulation-boundary case)
               :loading (fw:simulation-loading case)
               :solver (fw:make-solver :explicit :mesh-size .5d0 :mps-per-cell 2 :workers 1
                 :time-step-scale .2d0 :frames 301 :max-updates 200000 :damping 0d0)))
             (config (compile-configuration strict)))
        (dolist (entry +rapid-inputs+) (setf (gethash (car entry) config) (cdr entry)))
        (setf (gethash "settleDamping" config)
              (* .4d0 (/ (sqrt (/ (value config "drainedE") (value config "density"))) 2d0)))
        config))))

(in-package :cl-mpm/framework)
(defmethod compile-scenario ((scenario (eql :urmi-damage40-rapid)) (case simulation))
  (cl-mpm/scenario/urmi-damage40::compile-rapid-configuration case))
(defmethod execute-scenario ((scenario (eql :urmi-damage40-rapid)) (case simulation) config directory)
  (declare (ignore scenario))
  (cl-mpm/scenario/urmi-damage40:run (simulation-material case) config directory
    :approximate-preparation-duration 3d0))
