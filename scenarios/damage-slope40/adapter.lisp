;;;; Owned adaptation, not the published Joss geometry or a calibrated soil model.
;;;; No constitutive, solver, public schema or ordinary recipe changes.
(in-package :cl-mpm/framework)

(defparameter +damage-slope40-fixed+
  '(("shelfHeight" . 10d0) ("shelfAspect" . 2.39175359259421d0)
    ("cliffSlope" . 40d0) ("soilBoundary" . 1d0)
    ("runoutAspect" . 3.60824640740579d0) ("upperVerticalHeight" . 0d0)
    ("undercut" . 0d0) ("notchHeight" . 0d0) ("notchDepth" . 0d0)
    ("meshSize" . .5d0) ("mpsPerCell" . 2) ("workers" . 1)
    ("density" . 1700d0) ("E" . 1d9) ("nu" . .24d0)
    ("frictionAngle" . 50d0) ("cohesion" . 1965600d0)
    ("dilatancyAngle" . 0d0) ("enableDamage" . t) ("enablePlasticity" . t)
    ("fractureEnergy" . 4.8d0) ("damageCohesion" . 26000d0)
    ("damageFrictionAngle" . 50d0) ("nonlocalLength" . .5d0)
    ("ductility" . 53.59975505618717d0) ("initiationStress" . 18926.452181842527d0)
    ("delayTime" . 10d0) ("damageDelayExponent" . 2d0)
    ("residualTensileRatio" . 1d0) ("residualCompressionRatio" . 0d0)
    ("residualShearRatio" . .51d0) ("timeStepScale" . .5d0)
    ("massScaleAccelerate" . 10000d0) ("quasiStaticTolerance" . .01d0)
    ("settleTolerance" . .0001d0) ("settleMaxSteps" . 3000)
    ("accelerateInterval" . 2d0) ("collapseInterval" . .1d0)
    ("geometryRefinement" . 4) ("maxSteps" . 1500)))

(defun damage-slope40-equal-p (actual expected)
  (if (numberp expected)
      (and (realp actual) (= actual actual)
           (not (sb-ext:float-infinity-p (float actual 1d0)))
           (<= (abs (- actual expected)) (* 1d-12 (max 1d0 (abs expected)))))
      (equal actual expected)))

(defun damage-slope40-configuration (case)
  ;; READ-PARAMETERS must retain raw input here. Public coercion intentionally
  ;; still clamps ordinary cliff/Joss inputs to >=45 degrees.
  (let ((raw (simulation-parameters case))
        (angle (option (simulation-geometry case) :slope)))
    (unless (and (eql (gethash "cliffSlope" raw) 40d0) (eql angle 40d0))
      (error "This optional recipe requires explicit exact 40d0 slope in both input and geometry."))
    (dolist (entry +damage-slope40-fixed+)
      (unless (damage-slope40-equal-p (gethash (car entry) raw) (cdr entry))
        (error "Owned damage slope requires declared ~A=~S." (car entry) (cdr entry))))
    (maphash (lambda (key value)
               (declare (ignore value))
               (unless (gethash key (cl-mpm/framework/config:schema))
                 (error "Unknown damage-slope40 input ~S." key))) raw)
    (let ((config (cliff-configuration case t)))
      ;; The sole range extension is local and checked above. Never alter the
      ;; global schema, and never restore any other coerced parameter.
      (unless (= (gethash "cliffSlope" config) 45d0)
        (error "Expected canonical 45-degree lower bound before owned restoration."))
      (setf (gethash "cliffSlope" config) 40d0)
      (dolist (entry +damage-slope40-fixed+)
        (unless (damage-slope40-equal-p (gethash (car entry) config) (cdr entry))
          (error "Component/coercion changed owned damage-slope40 parameter ~A." (car entry))))
      ;; Only the declared 4-second fresh-equilibrium smoke and full 60 seconds
      ;; are accepted. A frame limit remains an incomplete native result.
      (unless (member (gethash "simulationTime" config) '(4d0 60d0) :test #'=)
        (error "Damage-slope40 duration must be 4 seconds (smoke) or 60 seconds (full)."))
      (unless (and (member (gethash "simulationTime" raw) '(4d0 60d0) :test #'=)
                   (= (gethash "maxSteps" config) 1500))
        (error "Invalid explicit damage-slope40 duration/frame budget."))
      config)))

(defmethod compile-scenario ((scenario (eql :damage-slope40)) (case simulation))
  (damage-slope40-configuration case))

(defun damage-slope40-smoke-case (case)
  "Separate fresh-equilibrium 4-second case; full case input remains unchanged."
  (damage-slope40-configuration case)
  (make-simulation :scenario :damage-slope40 :parameters (simulation-parameters case)
                   :material (simulation-material case) :geometry (simulation-geometry case)
                   :boundary (simulation-boundary case) :loading (simulation-loading case)
                   :solver (make-solver :staged :mesh-size .5d0 :mps-per-cell 2 :workers 1
                                        :time-step-scale .5d0 :simulation-time 4d0 :frames 1500)))

(defmethod execute-scenario ((scenario (eql :damage-slope40)) (case simulation) config directory)
  (declare (ignore case))
  (let ((record (make-hash-table :test #'equal))
        (effective (alexandria:copy-hash-table config)))
    (maphash (lambda (key value)
               (when (keywordp value) (setf (gethash key effective) (string-downcase value)))) effective)
    (setf (gethash "scenario" record) "damage-slope40"
          (gethash "backend" record) "unchanged-native-Joss-delayed-damage-staged-aggregate"
          (gethash "backendMetadataScenario" record) "joss-bay"
          (gethash "geometry" record) "straight40deg/H10m/crest12m/toe23.9175359259421m/base1m/domain60m/unnotched"
          (gethash "materialAssumption" record) "Inherited accepted Joss chalk parameters; not the previous soil MC material and not calibrated for this slope."
          (gethash "angleConvention" record) "Exactly40deg restored only in this optional recipe after ordinary canonical coercion; public schema remains unchanged."
          (gethash "initialization" record) "Self-weight elastic equilibrium required; evolution disabled until convergence; zero velocities and reset post-equilibrium clock; initially tagged base stays elastic."
          (gethash "timeConvention" record) "Native staged mass scaling10000/1 and velocity resets retained; requested duration is not experimental failure timing."
          (gethash "scientificValidation" record) "unverified"
          (gethash "effectiveConfig" record) effective)
    (with-open-file (stream (merge-pathnames "damage-slope40-protocol.json" directory)
                            :direction :output :if-exists :error)
      (write-string (jonathan:to-json record) stream)))
  (cl-mpm/framework/cliff:run-joss-reference config directory))
