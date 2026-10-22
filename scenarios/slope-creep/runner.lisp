(in-package :cl-mpm/scenario/slope-creep)

(defparameter +history-header+
  "frame,time_s,mass_kg_per_m,particle_count,kinetic_J_per_m,kinetic_ratio,free_residual_ratio,mass_error_fraction,max_displacement_m,max_speed_m_per_s,crest_settlement_m,crest_mean_speed_m_per_s,max_creep_kappa,mean_creep_kappa,max_creep_rate_per_s,min_yield_kirchhoff_pa,min_J")

(defun set-creep-enabled (sim enabled)
  (loop for mp across (cl-mpm:sim-mps sim) do
    (setf (cl-mpm/models/clay-creep:particle-enable-creep mp) enabled
          (cl-mpm/particle::mp-enable-plasticity mp) enabled)))

(defun write-row (stream index values)
  (format stream "~D" index)
  (dolist (value values) (format stream ",~,16E" (float value 1d0)))
  (terpri stream) (finish-output stream))

(defun settle (sim config initial-mass initial-count crest output manifest)
  "Instantaneous elastic geostatic initialization; creep age starts afterward."
  (set-creep-enabled sim nil)
  (setf (cl-mpm:sim-damping-factor sim) (gethash "settleDamping" config))
  (let ((hold 0) (converged nil))
    (cl-mpm/output/history:with-retained-history
        (history (merge-pathnames "gravity-history.csv" output)
                 :direction :output :if-exists :supersede :if-does-not-exist :create)
      (format history "updates,~A~%" (subseq +history-header+ 6))
      (loop for updates from 1 to (gethash "settleMaxUpdates" config) do
        (setf (cl-mpm:sim-dt sim) (stable-dt sim config))
        (cl-mpm:update-sim sim)
        (when (zerop (mod updates 25))
          (let ((values (statistics sim initial-mass initial-count config crest)))
            (write-row history updates values)
            (setf hold (if (and (>= updates (gethash "settleMinUpdates" config))
                                      (< (nth 4 values) (expt (gethash "settleTolerance" config) 2))
                                      (< (nth 5 values) (gethash "settleTolerance" config)))
                                 (1+ hold) 0)
                  (gethash "settleUpdates" manifest) updates
                  (gethash "gravityKineticRatio" manifest) (nth 4 values)
                  (gethash "gravityFreeResidualRatio" manifest) (nth 5 values))
            (when (zerop (mod updates 250))
              (write-json (merge-pathnames "manifest.json" output) manifest)
              (format t "~&[creep gravity] updates=~D residual=~,3E kinetic=~,3E~%"
                      updates (nth 5 values) (nth 4 values))
              (finish-output))
            (when (>= hold (gethash "settleHoldChecks" config))
              (setf converged t) (return))))))
    (unless converged (error "Elastic gravity initialization did not converge."))
    (setf (gethash "gravityConverged" manifest) t
          (gethash "gravityTimeS" manifest) (cl-mpm::sim-time sim))))

(defun run (material config directory)
  (let* ((output (uiop:ensure-directory-pathname directory))
         (vtk (merge-pathnames "vtk/" output))
         (manifest-path (merge-pathnames "manifest.json" output))
         (manifest (json-object "scenario" "slope-creep" "status" "running"
                     "complete" 'yason:false "gravityConverged" 'yason:false
                     "reportingResetPreservedState" 'yason:false "config" config
                     "loading" "constant self-weight; free crest; no prescribed trajectory or surcharge"
                     "material" "experimental total-stress clay; J2 Perzyna softening; phi_u=0"
                     "initialization" "elastic geostatic equilibrium; creep disabled until physical hold t=0"
                     "stressMeasure" "Kirchhoff yield; q=sqrt(3 J2(tau)); no pore-fluid coupling"
                     "massScale" 1d0 "dynamicDamping" 0d0 "scientificallyValidated" 'yason:false
                     "referenceAgreement" "NOT_APPLICABLE: different material/loading from Wang2017"
                     "landslideVerified" 'yason:false))
         (updates 0) (frame 0))
    (ensure-directories-exist vtk)
    (write-json manifest-path manifest)
    (handler-case
        (progn
          (cl-mpm/utils:set-workers (gethash "workers" config))
          (multiple-value-bind (sim crest) (make-slope material config)
            (unless crest (error "No crest observation particles."))
            (let ((mass (reduce #'+ (cl-mpm:sim-mps sim) :key #'cl-mpm/particle:mp-mass))
                  (count (length (cl-mpm:sim-mps sim))))
              (configure-creep-output sim)
              (setf (gethash "initialMassKgPerM" manifest) mass
                    (gethash "particleCount" manifest) count (gethash "phase" manifest) "gravity")
              (set-creep-enabled sim nil)
              (cl-mpm/output:save-vtk-mesh (merge-pathnames "mesh.vtk" vtk) sim)
              (cl-mpm/output:save-vtk (merge-pathnames "gravity_initial.vtk" vtk) sim)
              (settle sim config mass count crest output manifest)
              (cl-mpm/output:save-vtk (merge-pathnames "gravity_equilibrium.vtk" vtk) sim)
              (reset-reporting-origin sim)
              (setf (gethash "reportingResetPreservedState" manifest) t)
              (set-creep-enabled sim t)
              (setf (cl-mpm:sim-damping-factor sim) 0d0
                    (gethash "phase" manifest) "self-weight-creep-hold")
              (cl-mpm/output/history:with-retained-history
                  (history (merge-pathnames "creep-history.csv" output)
                           :direction :output :if-exists :supersede :if-does-not-exist :create)
                (format history "~A~%" +history-header+)
                (labels ((save-state ()
                           (let ((values (statistics sim mass count config crest)))
                             (write-row history frame values)
                             (cl-mpm/output:save-vtk
                              (merge-pathnames (format nil "particles_~4,'0D.vtk" frame) vtk) sim)
                             (setf (gethash "timeS" manifest) (first values)
                                   (gethash "loadingUpdates" manifest) updates
                                   (gethash "lastSavedFrame" manifest) frame
                                   (gethash "maxDisplacementM" manifest) (nth 7 values)
                                   (gethash "maxSpeedMPerS" manifest) (nth 8 values)
                                   (gethash "crestSettlementM" manifest) (nth 9 values)
                                   (gethash "maxCreepKappa" manifest) (nth 11 values)
                                   (gethash "massErrorFraction" manifest) (nth 6 values))
                             (write-json manifest-path manifest))))
                  (save-state)
                  (loop for next-frame from 1 below (gethash "frames" config)
                        for target = (* (gethash "duration" config)
                                        (/ next-frame (1- (gethash "frames" config)))) do
                    (loop while (< (cl-mpm::sim-time sim) (- target 1d-12)) do
                      (when (>= updates (gethash "maxUpdates" config))
                        (error "Creep update budget exhausted before duration."))
                      (setf (cl-mpm:sim-dt sim) (min (stable-dt sim config)
                                                   (- target (cl-mpm::sim-time sim))))
                      (cl-mpm:update-sim sim) (incf updates))
                    (setf frame next-frame) (save-state)
                    (format t "~&[creep hold] frame=~D t=~,3F max-u=~,4E max-speed=~,4E kappa=~,4E~%"
                            frame (gethash "timeS" manifest) (gethash "maxDisplacementM" manifest)
                            (gethash "maxSpeedMPerS" manifest) (gethash "maxCreepKappa" manifest))
                    (finish-output))))
              (unless (< (abs (- (cl-mpm::sim-time sim) (gethash "duration" config))) 1d-9)
                (error "Creep target duration not reached."))
              (setf (gethash "status" manifest) "completed" (gethash "complete" manifest) t)
              (write-json manifest-path manifest)))
          manifest)
      (error (condition)
        (setf (gethash "status" manifest) "failed" (gethash "complete" manifest) 'yason:false
              (gethash "error" manifest) (princ-to-string condition))
        (write-json manifest-path manifest)
        (error condition)))))

