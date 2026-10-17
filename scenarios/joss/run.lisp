;;;; Reference equilibrium and physical time integration.
;;;; Extracted without changing the existing numerical expressions.
(in-package :cl-mpm/framework/cliff)

(defun run-joss-reference (config output-dir)
  "Bounded experimental reproduction runner. A frame cap means unfinished."
  (let* ((output-dir (uiop:ensure-directory-pathname output-dir))
         (vtk-dir (merge-pathnames "vtk/" output-dir))
         (frames-dir (merge-pathnames "frames/" output-dir))
         (metadata (make-hash-table :test #'equal))
         (phase :settle) (written 0) (settle-steps 0) (settle-duration 0d0)
         (termination "failed")
         (plotting (not (string= (or (uiop:getenv "CL_MPM_REFERENCE_PNG") "1") "0")))
         (plotted 0) (plotting-error nil) (sim nil)
         (target-time (param config "simulationTime")))
    (ensure-directories-exist vtk-dir)
    (ensure-directories-exist frames-dir)
    (describe-config config)
    (cl-mpm/utils:set-workers (param config "workers"))
    (unwind-protect
         (progn
           (setf sim (make-joss-reference-sim config))
           (setf (gethash "effectiveMaterial" metadata) (reference-effective-material sim))
           (cl-mpm/output:save-vtk-mesh (merge-pathnames "mesh.vtk" vtk-dir) sim)
           (cl-mpm/output:save-vtk (merge-pathnames "initial.vtk" vtk-dir) sim)
           (format t "~&Reference particles: ~D, initial dt: ~,8E s~%"
                   (length (cl-mpm:sim-mps sim)) (cl-mpm:sim-dt sim))
           (with-open-file (csv (merge-pathnames "timesteps.csv" output-dir)
                                :direction :output :if-exists :supersede)
             (with-open-file (transitions (merge-pathnames "transitions.csv" output-dir)
                                          :direction :output :if-exists :supersede)
               (format csv "step,time,preparationTime,phase,massScale,kineticEnergy,work,energyRatio,oobf,mass,massDamage,particles~%")
               (format transitions "time,from,to,energyRatio,oobf~%")
               (finish-output csv)
               (finish-output transitions)
               ;; Elastic equilibrium with physical mass; its elapsed time is
               ;; preparation time, not the paper's subsequent damage clock.
               (setf (cl-mpm:sim-damping-factor sim)
                     (reference-viscous-damping config 0.1d0))
               (let ((settled nil))
                 (loop for step from 1 to (param config "settleMaxSteps") do
                   (setf (cl-mpm:sim-dt sim)
                         (cl-mpm/setup:estimate-elastic-dt sim :dt-scale (param config "timeStepScale")))
                   (cl-mpm:update-sim sim)
                   (setf settle-steps step)
                   (when (zerop (mod step 50))
                     (format t "~&Settling ~D: energy ~,4E, OOBF ~,4E~%"
                             step (reference-energy-ratio sim) (cl-mpm::sim-stats-oobf sim))
                     (finish-output))
                   (reference-write-row csv sim :settle step (cl-mpm::sim-time sim))
                   (when (zerop (mod step 50)) (finish-output csv))
                   (when (and (< (reference-energy-ratio sim) (param config "settleTolerance"))
                              (< (cl-mpm::sim-stats-oobf sim) (param config "settleTolerance")))
                     (setf settled t)
                     (loop-finish)))
                 (finish-output csv)
                 (unless settled
                   (setf termination "equilibrium-not-converged")
                   (error "Reference elastic equilibrium did not converge after ~D steps: energy ~A, OOBF ~A"
                          settle-steps (reference-energy-ratio sim) (cl-mpm::sim-stats-oobf sim))))
               (setf settle-duration (cl-mpm::sim-time sim))
               (reference-check-finite sim)
               (cl-mpm/output:save-vtk (merge-pathnames "equilibrium.vtk" vtk-dir) sim)
               (reference-zero-velocities sim)
               (setf (cl-mpm::sim-time sim) 0d0 (cl-mpm::sim-stats-work sim) 0d0
                     (cl-mpm::sim-stats-energy sim) 0d0 (cl-mpm::sim-stats-power sim) 0d0
                     (cl-mpm::sim-enable-damage sim) (param config "enableDamage")
                     (cl-mpm:sim-damping-factor sim)
                     (reference-viscous-damping config 1d-4)
                     phase :accelerate)
               (loop for mp across (cl-mpm:sim-mps sim) do
                 (let ((cliff (not (= (cl-mpm/particle::mp-index mp) 1))))
                   (setf (cl-mpm/particle::mp-enable-damage mp) (and cliff (param config "enableDamage"))
                         (cl-mpm/particle::mp-enable-plasticity mp) (and cliff (param config "enablePlasticity")))))
               (format transitions "0.000000000000,settle,accelerate,~A,~A~%"
                       (reference-csv-number (reference-energy-ratio sim))
                       (reference-csv-number (cl-mpm::sim-stats-oobf sim)))
               (finish-output transitions)
               (loop while (and (< written (param config "maxSteps"))
                                (< (cl-mpm::sim-time sim) target-time)) do
                 (let* ((interval (param config (if (eq phase :accelerate) "accelerateInterval" "collapseInterval")))
                        (end-time (min target-time (+ (cl-mpm::sim-time sim) interval)))
                        (scale (if (eq phase :accelerate) (param config "massScaleAccelerate") 1d0)))
                   (setf (cl-mpm::sim-mass-scale sim) scale)
                   (loop while (< (cl-mpm::sim-time sim) end-time) do
                     (setf (cl-mpm:sim-dt sim)
                           (min (- end-time (cl-mpm::sim-time sim))
                                (cl-mpm/setup:estimate-elastic-dt sim :dt-scale (param config "timeStepScale"))))
                     (unless (and (reference-finite-p (cl-mpm:sim-dt sim)) (> (cl-mpm:sim-dt sim) 0d0))
                       (error "Invalid reference CFL timestep"))
                     (cl-mpm:update-sim sim))
                   (incf written)
                   (reference-check-finite sim)
                   (reference-write-row csv sim phase written (cl-mpm::sim-time sim))
                   (finish-output csv)
                   (cl-mpm/output:save-vtk (numbered vtk-dir "sim" written "vtk") sim)
                   (when plotting
                     (handler-case
                         (progn
                           (save-frame sim (param config "plotMode")
                                       (format nil "Joss reference: t=~,3F s, ~(~A~)" (cl-mpm::sim-time sim) phase)
                                       (numbered frames-dir "frame" written "png")
                                       :timeout-seconds 30)
                           (incf plotted))
                       (error (e) (setf plotting nil plotting-error (princ-to-string e))
                         (format t "~&Reference plotting disabled: ~A~%" e))))
                   (format t "~&Step ~D/~D; physical time ~,6F s; ~(~A~)~%"
                           written (param config "maxSteps") (cl-mpm::sim-time sim) phase)
                   (finish-output)
                   (let ((next (reference-next-state phase (reference-energy-ratio sim)
                                      (cl-mpm::sim-stats-oobf sim) (param config "quasiStaticTolerance"))))
                     (unless (eq next phase)
                       (format transitions "~,12F,~(~A~),~(~A~),~A,~A~%"
                               (cl-mpm::sim-time sim) phase next
                               (reference-csv-number (reference-energy-ratio sim))
                               (reference-csv-number (cl-mpm::sim-stats-oobf sim)))
                       (finish-output transitions)
                       (when (eq next :accelerate)
                         (setf (cl-mpm::sim-stats-work sim) 0d0)
                         (reference-zero-velocities sim))
                       (setf phase next)))))
               (setf termination (if (>= (cl-mpm::sim-time sim) target-time) "simulation-time" "frame-limit"))))
           sim)
      (setf (gethash "scenario" metadata) "joss-bay"
            (gethash "implementation" metadata) "experimental-paper-reference"
            (gethash "complete" metadata) (if (string= termination "simulation-time") t :false)
            (gethash "termination" metadata) termination
            (gethash "phase" metadata) (string-downcase (symbol-name phase))
            (gethash "physicalTime" metadata) (if sim (if (eq phase :settle) 0d0 (cl-mpm::sim-time sim)) 0d0)
            (gethash "equilibrationSteps" metadata) settle-steps
            (gethash "equilibrationDuration" metadata) (if (and sim (eq phase :settle)) (cl-mpm::sim-time sim) settle-duration)
            (gethash "frames" metadata) written
            (gethash "plottingCompleted" metadata) (if (and (> written 0) (= plotted written)) t :false)
            (gethash "plottedFrames" metadata) plotted
            (gethash "plottingTimeoutSeconds" metadata) 30
            (gethash "requestedSimulationTime" metadata) target-time
            (gethash "scientificValidation" metadata) "unverified"
            (gethash "damageCriterion" metadata) "author-Joss-Drucker-Prager"
            (gethash "damageCriterionConvention" metadata)
            "max(0, Drucker-Prager(undamaged Kirchhoff stress, stored radian friction angle)); reference-only author-code adaptation, full fracture/run-out unvalidated."
            (gethash "protectedBaseParticles" metadata)
            (if sim (count 1 (cl-mpm:sim-mps sim) :key #'cl-mpm/particle::mp-index) 0)
            (gethash "protectedBaseConvention" metadata)
            "Initial y <= soilBoundary is material index1; damage and plasticity remain disabled for this elastic beach."
            (gethash "statisticNorm" metadata)
            (if (typep sim 'joss-reference-aggregate-sim) "aggregate-projected-L2" "volume-weighted-L2")
            (gethash "statisticConvention" metadata)
            (if (typep sim 'joss-reference-aggregate-sim)
                "Author-code stabilization adaptation: bulk physical nodal KE/work plus aggregate constrained E^T M E kinetic energy and global displacement dot external work; OOBF uses independent E^T(internal+external) / E^T external L2 norms, excludes damping and dependent exterior DOFs. No volume weighting or literal Eq67 claim."
                "KE/work use mapped nodal volume V/h^2 (Eqs64-66); OOBF keeps the engine's L2 norm ratio. Printed Eq67 uses ambiguous L1/outer-square notation.")
            (gethash "stabilization" metadata)
            (if (typep sim 'joss-reference-aggregate-sim) "author-code-cut-cell-aggregation" "none")
            (gethash "viscousDampingConvention" metadata)
            "core damping=2*beta; beta_crit=(pi/2)*sqrt(E/(rho*h^2)); settle beta=0.1*beta_crit, dynamic beta=1e-4*beta_crit."
            (gethash "criticalDamping" metadata) (reference-critical-damping config)
            (gethash "settleDampingFactor" metadata) (reference-viscous-damping config 0.1d0)
            (gethash "dynamicDampingFactor" metadata) (reference-viscous-damping config 1d-4)
            (gethash "parameterAmbiguities" metadata)
            "Paper Table 5 E=100 MPa conflicts with prose E=1 GPa; Eq19 blend notation conflicts with prose. Effective inputs must be reported.")
      (when plotting-error (setf (gethash "plottingError" metadata) plotting-error))
      (with-open-file (stream (merge-pathnames "reference-metadata.json" output-dir)
                              :direction :output :if-exists :supersede)
        (write-string (jonathan:to-json metadata) stream))
      (ignore-errors (vgplot:close-all-plots)))))
