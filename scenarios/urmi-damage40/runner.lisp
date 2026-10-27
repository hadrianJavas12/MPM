(in-package :cl-mpm/scenario/urmi-damage40)
(defun stable-dt (sim config)
  (let ((dt (* (value config "timeStepScale") (cl-mpm/setup:estimate-elastic-dt sim))))
    (unless (and (gs::finite-p dt) (> dt 0d0)) (error "Invalid owned stable timestep.")) dt))
(defun equilibrium-p (sim config)
  (let ((rf (force-ratio sim)) (rk (kinetic-ratio sim config)))
    (and rf rk (>= (cl-mpm::sim-time sim) (value config "gravityRampDuration"))
         (< rf (value config "forceTolerance")) (< rk (value config "kineticTolerance")))))
(defun preparation-step (sim config)
  (let* ((time (cl-mpm::sim-time sim)) (ramp (value config "gravityRampDuration"))
         (dt (min (- (value config "maxPreparationTimeS") time)
                  (if (< time ramp) (min (stable-dt sim config) (- ramp time)) (stable-dt sim config)))))
    (unless (> dt 0d0) (error "Owned drained preparation time cap reached."))
    (setf (cl-mpm:sim-dt sim) dt (cl-mpm:sim-gravity sim)
          (* (value config "gravity") (gs:ramp-factor (+ time dt) ramp)))
    (cl-mpm:update-sim sim)))
(defun make-manifest (config)
  (obj "scenario" "urmi-damage40" "status" "running" "complete" 'yason:false
       "phase" "initialization" "timeS" 0d0 "nativeTimeS" 0d0 "preparationTimeS" 0d0
       "updates" 0 "preparationUpdates" 0 "dynamicUpdates" 0 "savedFrames" 0 "config" config
       "requestedDynamicDurationS" 60d0 "scientificallyValidated" 'yason:false "landslideVerified" 'yason:false
       "model" (usd:strength-damage-reference)
       "formulation" "Native USF/FLIP plane strain, mass1, no Fbar/split/removal; engine damage disabled; soil MC strength damage remains active"
       "geometry" "Straight40deg H10m/crest12m/toe23.9175359259421m; full4m soil foundation active; domain60x20m; no notch"
       "initialization" "Constant drained elastoPLASTIC MC throughout2s smoothstep gravity ramp and measured relaxation; no field reset"
       "equilibriumForceNorm" "Serial active positive-mass free x/y DOFs: sqrt(sum_free((internal+external)^2)/sum_free(external^2)); damping excluded; zero denominator undefined and ineligible"
       "equilibriumKineticNorm" "After final velocity BCs: free nodal KE/(once-per-node free nodal mass*abs(targetg)*H); not a material-cohort mass"
       "equilibriumCriterion" "RF<1e-4 and RK<1e-8 for>=50 consecutive post-ramp updates spanning>=1s, then>=100 undamped updates spanning>=1s all passing; caps60000updates/20spreparation"
       "drainedDilationAssumption" "psi=0 is an explicit numerical assumption"
       "transfer" "All cloned candidates validated before one logical-ID/order-preserving vector swap; E/nu compliance changes; real dt0 material return may release stress and advance kappa/D without advancing clock"
       "history" "Native clock and cumulative kappa/plastic work remain continuous; per-MP kappa origin activates the new undrained law; D_s is strength loss, not stiffness/fracture/crack opening"
       "referenceVolume" "CSV reference_volume_m3_per_m is original material V0; global F/J never reset; original initial positions retained across transfer"
       "freeUpperSubset" "Fixed original x>2m and y>baseHeight+2m=6m cohort"
       "boundaryLimit" "Actual center/domain clearances and touching mass retained; center exit fails; no clamp/deletion/outlier filtering; fixed bottom/side rollers are not calibrated runout conditions"
       "colourField" "mc-strength-damage" "damageInactiveConvention" "Preparation has mc-damage-active=0 and explicit strength-damage0; legacy damage field stays inactive"
       "historyFile" "history.csv" "particleFile" "material-state.csv" "preparationHistoryFile" "preparation-history.csv"
       "preparationStateFile" "preparation-states.csv" "preparationParticleFile" "preparation-material-state.csv"
       "initialVtk" "vtk/initial.vtk" "drainedVtk" "vtk/drained.vtk" "dynamicVtkPattern" "vtk/particles_%04d.vtk"
       "transferLedgerFile" "transfer-ledger.json"
       "scope" "New Urmi-inspired S1 normalized strength law and parameter/history transfer adaptation; not literal paper calibration or validated failure time; stable/no-damage outcomes retained"))
(defun run (material config directory &key approximate-preparation-duration)
  (let* ((output (uiop:ensure-directory-pathname directory)) (vtk (merge-pathnames "vtk/" output))
         (manifest (make-manifest config)) (manifest-path (merge-pathnames "manifest.json" output))
         (sim nil) (context nil) (preparation-updates 0) (dynamic-updates 0) (saved 0))
    (when approximate-preparation-duration
      (unless (= approximate-preparation-duration 3d0) (error "Rapid preparation must be declared3s."))
      (setf (gethash "scenario" manifest) "urmi-damage40-rapid"
            (gethash "requestedDynamicDurationS" manifest) (value config "duration")
            (gethash "approximateDemo" manifest) t
            (gethash "equilibriumVerified" manifest) 'yason:false
            (gethash "initialization" manifest) "RAPID DEMO: fixed3s drained gravity ramp/relaxation, NOT measured equilibrium; no field resets"
            (gethash "equilibriumCriterion" manifest) "NOT ENFORCED in explicitly user-authorized rough demonstration"
            (gethash "scope" manifest) "RAPID DEMO ONLY: h2m/PPC1/105MP, fixed3s approximate preparation then20s requested dynamics; mesh-sensitive uncalibrated Urmi-like law, no scientific accuracy claim"))
    (ensure-directories-exist vtk) (write-json manifest-path manifest)
    (labels ((progress (phase)
               (setf (gethash "phase" manifest) phase (gethash "updates" manifest) (+ preparation-updates dynamic-updates)
                     (gethash "preparationUpdates" manifest) preparation-updates (gethash "dynamicUpdates" manifest) dynamic-updates
                     (gethash "savedFrames" manifest) saved)
               (when sim
                 (setf (gethash "nativeTimeS" manifest) (cl-mpm::sim-time sim)
                       (gethash "preparationTimeS" manifest) (or (and context (observation-context-switch-native-time context)) (cl-mpm::sim-time sim))
                       (gethash "timeS" manifest) (if context (dynamic-time sim context) 0d0)
                       (gethash "freeForceRatio" manifest) (force-ratio sim)
                       (gethash "freeForceRatioDefined" manifest) (if (force-ratio sim) t 'yason:false)
                       (gethash "freeKineticRatio" manifest) (kinetic-ratio sim config)))
               (write-json manifest-path manifest))
             (prep-step (phase history consecutive hold)
               (when (or (>= preparation-updates (value config "maxPreparationUpdates"))
                         (>= (cl-mpm::sim-time sim) (value config "maxPreparationTimeS")))
                 (error "Owned drained equilibrium update cap reached; no parameter tuning/restart applied."))
               (preparation-step sim config) (incf preparation-updates)
               (gs::write-csv-row history
                 (list preparation-updates (cl-mpm::sim-time sim)
                       (if (force-ratio sim) 1 0) (or (force-ratio sim) 0d0)
                       (force-numerator2 sim) (force-denominator2 sim)
                       (free-ke sim) (free-nodal-mass sim) (or (kinetic-ratio sim config) 0d0)
                       consecutive hold (cl-mpm:sim-damping-factor sim))
                 '(updates time_s force_defined RF numerator2 denominator2 KE Mfree RK consecutive hold damping))
               (when (zerop (mod preparation-updates 100))
                 (finish-output history) (progress phase)
                 (format t "~&[urmi-damage40] ~A updates=~D native=~,6F RF=~S RK=~S~%"
                         phase preparation-updates (cl-mpm::sim-time sim) (force-ratio sim) (kinetic-ratio sim config)) (finish-output))))
      (handler-case
          (progn
            (cl-mpm/utils:set-workers 1) (setf sim (build-slope material config) context (capture-reference sim config))
            (configure-output sim)
            (setf (gethash "particleCount" manifest) (length (cl-mpm:sim-mps sim))
                  (gethash "initialMassKgPerM" manifest) (gs::reference-state-mass (observation-context-reference context)))
            (cl-mpm/output:save-vtk-mesh (merge-pathnames "mesh.vtk" vtk) sim)
            (cl-mpm/scenario/urmi-damage40/output-streams:with-retained-output-file (prep-state (merge-pathnames "preparation-states.csv" output))
              (cl-mpm/scenario/urmi-damage40/output-streams:with-retained-output-file (prep-mp (merge-pathnames "preparation-material-state.csv" output))
                (write-headers prep-state prep-mp)
                (save-state sim context config (merge-pathnames "initial.vtk" vtk) 0 0 0 prep-state prep-mp)
                (progress "drained-ramp-and-relaxation")
                (cl-mpm/scenario/urmi-damage40/output-streams:with-retained-output-file (history (merge-pathnames "preparation-history.csv" output))
                  (format history "updates,native_time_s,force_defined,RF,free_force_numerator2,free_force_denominator2,free_KE,free_nodal_mass,RK,prior_consecutive,prior_hold,damping~%")
                  (if approximate-preparation-duration
                      (loop while (< (cl-mpm::sim-time sim) approximate-preparation-duration) do
                        (prep-step "approximate-drained-preparation" history 0 0))
                  (let ((consecutive 0) (start nil))
                    (loop until (and (>= consecutive (value config "consecutiveChecks")) start
                                     (>= (- (cl-mpm::sim-time sim) start) (value config "consecutiveDurationS"))) do
                      (prep-step "drained-ramp-and-relaxation" history consecutive 0)
                      (if (equilibrium-p sim config)
                          (progn (unless start (setf start (cl-mpm::sim-time sim))) (incf consecutive))
                          (setf consecutive 0 start nil)))
                    (setf (cl-mpm:sim-damping-factor sim) 0d0)
                    (progress "drained-undamped-hold")
                    (let ((hold 0) (hold-start (cl-mpm::sim-time sim)))
                      (loop until (and (>= hold (value config "undampedHoldUpdates"))
                                       (>= (- (cl-mpm::sim-time sim) hold-start) (value config "undampedHoldDurationS"))) do
                        (prep-step "drained-undamped-hold" history consecutive hold) (incf hold)
                        (unless (equilibrium-p sim config) (error "Measured drained equilibrium failed its undamped hold.")))))))
                (when approximate-preparation-duration (setf (cl-mpm:sim-damping-factor sim) 0d0))
                (setf (observation-context-preparation-updates context) preparation-updates)
                (save-state sim context config (merge-pathnames "drained.vtk" vtk) 1 1 preparation-updates prep-state prep-mp)))
            (progress "material-transfer")
            (let* ((clock (cl-mpm::sim-time sim)) (ledger (tr:transfer! sim)))
              (unless (= clock (cl-mpm::sim-time sim)) (error "Material switch changed native clock."))
              (write-json (merge-pathnames "transfer-ledger.json" output)
                (obj "nativeTimeS" clock "mpmUpdates" 0 "entries" ledger
                     "scope" "Actual instantaneous material switch/release; energy proxies and native plastic work separately retained"))
              (rebind-reference-after-transfer sim context ledger)
              (setf (gethash "transferNativeTimeS" manifest) clock))
            (cl-mpm/scenario/urmi-damage40/output-streams:with-retained-output-file (history (merge-pathnames "history.csv" output))
              (cl-mpm/scenario/urmi-damage40/output-streams:with-retained-output-file (particles (merge-pathnames "material-state.csv" output))
                (write-headers history particles)
                (save-state sim context config (merge-pathnames "particles_0000.vtk" vtk) 0 2 preparation-updates history particles)
                (incf saved) (progress "undrained-dynamic")
                (loop for frame from 1 below (value config "frames")
                      for target = (+ (observation-context-switch-native-time context)
                                      (* (value config "duration") (/ frame (1- (value config "frames"))))) do
                  (loop while (< (cl-mpm::sim-time sim) target) do
                    (when (>= dynamic-updates (value config "maxDynamicUpdates")) (error "Owned dynamic update cap reached before60s."))
                    (let ((dt (min (stable-dt sim config) (- target (cl-mpm::sim-time sim)))))
                      (unless (> (+ (cl-mpm::sim-time sim) dt) (cl-mpm::sim-time sim)) (error "Owned timestep cannot advance time."))
                      (setf (cl-mpm:sim-dt sim) dt (cl-mpm:sim-gravity sim) (value config "gravity"))
                      (cl-mpm:update-sim sim) (incf dynamic-updates)))
                  (save-state sim context config (merge-pathnames (format nil "particles_~4,'0D.vtk" frame) vtk)
                              frame 3 (+ preparation-updates dynamic-updates) history particles)
                  (incf saved) (progress "undrained-dynamic")
                  (format t "~&[urmi-damage40] frame=~D/~D dynamic=~,6F native=~,6F updates=~D~%"
                          frame (1- (value config "frames")) (dynamic-time sim context) (cl-mpm::sim-time sim) dynamic-updates) (finish-output))))
            (unless (and (= saved (value config "frames"))
                         (>= (cl-mpm::sim-time sim) (+ (observation-context-switch-native-time context) (value config "duration"))))
              (error "Owned run did not reach every requested dynamic frame."))
            (setf (gethash "complete" manifest) t (gethash "status" manifest) "complete")
            (progress "finished") sim)
        (error (condition)
          (setf (gethash "complete" manifest) 'yason:false (gethash "status" manifest) "failed"
                (gethash "error" manifest) (princ-to-string condition))
          (progress (gethash "phase" manifest)) (error condition))))))
