(in-package :cl-mpm/scenario/residual-clay-slope)
(defun make-law (config)
  (mc:make-evolution-law :variant :hs
    :points (map 'list (lambda (row) (coerce row 'list)) (value config "frictionTable"))
    :cohesion 0d0 :psi 0d0 :stress-measure :cauchy :peak-kappa .037d0
    :strain-assumption "Human-approved residual clay: peak phi at kappa0, original postpeak coordinates; residual tan(phi)=tan(33.99deg)/4; no kappa preload/strain-axis scaling"))

(defun check-config (case)
  (let* ((cfg (fw:simulation-parameters case)) (material (fw:simulation-material case))
         (solver (fw:simulation-solver case)) (args (fw:material-particle-initargs material)))
    (dolist (entry '(("meshSize" . .5d0) ("mpsPerCell" . 2) ("workers" . 1)
                     ("height" . 10d0) ("slope" . 40d0) ("crestLength" . 24d0)
                     ("baseHeight" . 8d0) ("domainWidth" . 72d0) ("domainHeight" . 24d0)
                     ("duration" . 20d0) ("frames" . 41) ("gravityRampDuration" . 2d0)
                     ("density" . 2000d0) ("timeStepScale" . .2d0)
                     ("youngsModulusPa" . 20000000d0) ("poissonRatio" . .2d0)
                     ("cohesionPa" . 0d0) ("dilationDeg" . 0d0) ("residualStrengthRatio" . .25d0)))
      (unless (= (value cfg (car entry)) (cdr entry)) (error "Residual clay config differs:~A" (car entry))))
    (unless (and (if (gethash "explicitHsApex" cfg)
                    (eq (fw:material-particle-class material)
                        (find-symbol "PARTICLE-MC-HS-APEX" "CL-MPM/MODELS/MC-HS-APEX"))
                    (eq (fw:material-particle-class material) 'mc:particle-mc-evolution))
                 (= (getf args :E) 20d6) (= (getf args :nu) .2d0)
                 (= (fw:option material :density) 2000d0)
                 (equalp (getf args :evolution-law) (make-law cfg)))
      (error "Residual clay actual material differs."))
    (dolist (entry '((:mesh-size . .5d0) (:mps-per-cell . 2) (:workers . 1)
                     (:time-step-scale . .2d0) (:frames . 41) (:max-updates . 80000) (:damping . .02d0)))
      (unless (= (fw:option solver (car entry)) (cdr entry)) (error "Residual clay solver differs.")))
    (let ((law (make-law cfg)) (peak (tan (* pi (/ 33.99d0 180d0)))))
      (multiple-value-bind (c phi psi) (mc:law-values law 1d0)
        (unless (and (zerop c) (zerop psi) (< (abs (- (/ (tan phi) peak) .25d0)) 1d-12) (> phi 0d0))
          (error "Quarter-strength residual floor differs."))))
    cfg))

(defun run (material cfg directory)
  (let* ((out (uiop:ensure-directory-pathname directory)) (vtk (merge-pathnames "vtk/" out))
         (sim nil) (ctx nil) (updates 0) (saved 0)
         (manifest (obj "scenario" "residual-clay-slope-quarter" "status" "running" "complete" 'yason:false
           "config" cfg "particleCount" 0 "savedFrames" 0 "updates" 0 "timeS" 0d0 "nativeTimeS" 0d0
           "phase" "initialization" "equilibriumVerified" 'yason:false
           "material" "Prior3D triaxial residual CLAY E20MPa/nu.2/rho2000/c0/psi0; human-approved peak-initialized frictional HS, positive quarter residual"
           "initialization" "Gravity from zero stress and kappa0, smooth2s ramp; NO claim of initial geostatic equilibrium; actual motion/softening saved during ramp"
           "trigger" "Gravity loading of40deg cohesionless slope; no notch/driver/undrained material switch or hidden weakening"
           "history" "Global F/J/originalV0/kappa/plastic work never reset; no100kPa laboratory confinement on slope"
           "domainUpdate" "Opt-in volume-based cpGIMP l_i=l_i0 sqrt(J); positiveJ/domain guarded"
           "damageDefinition" "D_phi=1-tan(phi)/tan(phi_peak), frictional strength loss at fixed positive normal stress, bounded0..0.75; not cohesion/stiffness/crack damage"
           "historyFile" "history.csv" "particleFile" "material-state.csv" "dynamicVtkPattern" "vtk/particles_%04d.vtk"
           "scientificallyValidated" 'yason:false "landslideVerified" 'yason:false)))
    (when (gethash "explicitHsApex" cfg)
      (setf (gethash "apexConvention" manifest)
            "Explicit additional gA=p volumetric flow at zero-stress apex; evolving friction/c0/regular psi0 retained, NOT strict MC in tension"
            (gethash "material" manifest)
            "Prior triaxial clay HS, quarter residual friction PLUS declared volumetric apex extension; gravity-only unnotched trial"))
    (ensure-directories-exist vtk)
    (labels ((progress (phase)
               (setf (gethash "phase" manifest) phase (gethash "savedFrames" manifest) saved
                     (gethash "updates" manifest) updates)
               (when sim (setf (gethash "timeS" manifest) (cl-mpm::sim-time sim)
                               (gethash "nativeTimeS" manifest) (cl-mpm::sim-time sim)
                               (gethash "freeForceRatio" manifest) (u::force-ratio sim)
                               (gethash "freeKineticRatio" manifest) (kinetic-ratio sim cfg)))
               (write-json (merge-pathnames "manifest.json" out) manifest)))
      (setf u::*proper-volume-domain* t)
      (unwind-protect
        (handler-case
          (progn
            (cl-mpm/utils:set-workers 1)
            (setf sim (u:build-slope material cfg :sim-type 'u::urmi-proper-sim))
            (u::proper-setup sim)
            (setf ctx (capture-reference sim cfg) (observation-context-failure-directory ctx) out
                  (observation-context-switch-native-time ctx) 0d0
                  (observation-context-switch-positions ctx) (map 'vector (lambda (p) (cl-mpm/utils:vector-copy (cl-mpm/particle:mp-position p))) (cl-mpm:sim-mps sim))
                  (observation-context-switch-kappa ctx) (map 'vector #'mc:particle-kappa (cl-mpm:sim-mps sim))
                  (observation-context-switch-work ctx) (map 'vector #'mc:particle-plastic-work (cl-mpm:sim-mps sim)))
            (unless (= (length (cl-mpm:sim-mps sim)) 14010) (error "Expected14010 actual center-clipped MPs."))
            (setf (gethash "particleCount" manifest) 14010)
            (configure-output sim)
            (cl-mpm/output:save-vtk-mesh (merge-pathnames "mesh.vtk" vtk) sim)
            (cl-mpm/scenario/urmi-damage40/output-streams:with-retained-output-file (history (merge-pathnames "history.csv" out))
              (cl-mpm/scenario/urmi-damage40/output-streams:with-retained-output-file (particles (merge-pathnames "material-state.csv" out))
                (write-headers history particles)
                (loop for frame below (value cfg "frames")
                      for target = (* (value cfg "duration") (/ frame (1- (value cfg "frames")))) do
                  (loop while (< (cl-mpm::sim-time sim) target) do
                    (when (>= updates (value cfg "maxDynamicUpdates")) (error "Residual clay update budget reached."))
                    (let* ((time (cl-mpm::sim-time sim)) (ramp (value cfg "gravityRampDuration"))
                           (dt (min (stable-dt sim cfg) (- target time))))
                      (when (< time ramp) (setf dt (min dt (- ramp time))))
                      (unless (> (+ time dt) time) (error "Residual clay dt cannot advance."))
                      (setf (cl-mpm:sim-dt sim) dt
                            (cl-mpm:sim-gravity sim) (* (value cfg "gravity") (gs:ramp-factor (+ time dt) ramp))
                            (cl-mpm:sim-damping-factor sim) (if (< time ramp) .75d0 .02d0))
                      (cl-mpm:update-sim sim) (incf updates)
                      (when (zerop (mod updates 250)) (progress "gravity-ramp-or-motion"))))
                  (save-state sim ctx cfg (merge-pathnames (format nil "particles_~4,'0D.vtk" frame) vtk) frame 3 updates history particles)
                  (incf saved) (progress (if (< target 2d0) "gravity-ramp" "gravity-motion"))
                  (format t "~&[residual-clay] frame~D/~D time=~,6F updates=~D~%" frame (1- (value cfg "frames")) (cl-mpm::sim-time sim) updates) (finish-output))))
            (setf (gethash "complete" manifest) t (gethash "status" manifest) "complete")
            (progress "finished") sim)
          (error (c) (setf (gethash "status" manifest) "failed" (gethash "error" manifest) (princ-to-string c))
            (progress (gethash "phase" manifest)) (error c)))
        (setf u::*proper-volume-domain* nil)))))

(in-package :cl-mpm/framework)
(defmethod compile-scenario ((scenario (eql :residual-clay-slope-quarter)) (case simulation))
  (cl-mpm/scenario/residual-clay-slope::check-config case))
(defmethod execute-scenario ((scenario (eql :residual-clay-slope-quarter)) (case simulation) config directory)
  (declare (ignore scenario))
  (cl-mpm/scenario/residual-clay-slope::run (simulation-material case) config directory))
