(in-package :cl-mpm/scenario/slope-descent)

(defun state-statistics (sim diagnostics reference-mass config)
  (let ((mass 0d0) (ke 0d0) (max-yield (- most-positive-double-float)))
    (loop for mp across (cl-mpm:sim-mps sim) do
      (cl-mpm/framework:validate-material-state diagnostics mp)
      (dolist (matrix (list (cl-mpm/particle:mp-position mp) (cl-mpm/particle:mp-velocity mp)
                            (cl-mpm/particle:mp-stress mp) (cl-mpm/particle:mp-strain mp)
                            (cl-mpm/particle::mp-deformation-gradient mp)))
        (unless (matrix-finite-p matrix) (error "Nonfinite native particle field.")))
      (unless (and (finite-p (cl-mpm/particle:mp-volume mp))
                   (> (cl-mpm/particle:mp-volume mp) 0d0))
        (error "Invalid particle volume."))
      (let ((m (cl-mpm/particle:mp-mass mp)) (v (cl-mpm/particle:mp-velocity mp)))
        (incf mass m)
        (incf ke (* .5d0 m (loop for axis below 3 sum (expt (component v axis) 2)))))
      (setf max-yield (max max-yield (cl-mpm/models/mc-evolution:particle-yield-residual-kirchhoff mp))))
    (let ((error-fraction (/ (- mass reference-mass) reference-mass))
          (ratio (/ ke (* reference-mass (- (gethash "gravity" config)) (gethash "height" config)))))
      (unless (and (finite-p mass) (finite-p ke) (finite-p max-yield)
                   (finite-p (free-residual sim)) (< (abs error-fraction) 1d-12))
        (error "Nonfinite statistics or particle mass conservation failure."))
      (values mass ke ratio (free-residual sim) error-fraction max-yield))))

(defun material-signature (sim)
  "Exact numeric internal-state signature; reporting zeroing must leave it unchanged."
  (map 'vector
       (lambda (mp)
         (list (mapcar (lambda (matrix) (copy-seq (cl-mpm/utils:fast-storage matrix)))
                       (list (cl-mpm/particle:mp-stress mp) (cl-mpm/particle::mp-stress-kirchoff mp)
                             (cl-mpm/particle:mp-strain mp) (cl-mpm/particle::mp-strain-n mp)
                             (cl-mpm/particle::mp-deformation-gradient mp)
                             (cl-mpm/particle::mp-deformation-gradient-0 mp)))
               (cl-mpm/particle:mp-volume mp)
               (cl-mpm/models/mc-evolution:particle-kappa mp)
               (cl-mpm/models/mc-evolution::particle-kappa-committed mp)
               (cl-mpm/models/mc-evolution:particle-plastic-volume mp)
               (cl-mpm/models/mc-evolution:particle-plastic-work mp)))
       (cl-mpm:sim-mps sim)))

(defun write-gravity-state (sim path)
  (with-open-file (stream path :direction :output :if-exists :supersede :if-does-not-exist :create)
    (format stream "particle,x_m,y_m,volume_m3_per_m,kappa")
    (dolist (name '("stress" "elastic_strain"))
      (dotimes (axis 6) (format stream ",~A_~D" name axis)))
    (dotimes (row 3) (dotimes (col 3) (format stream ",F_~D~D" row col)))
    (terpri stream)
    (loop for mp across (cl-mpm:sim-mps sim) for index from 0 do
      (format stream "~D,~,16E,~,16E,~,16E,~,16E" index
              (component (cl-mpm/particle:mp-position mp) 0)
              (component (cl-mpm/particle:mp-position mp) 1)
              (cl-mpm/particle:mp-volume mp) (cl-mpm/models/mc-evolution:particle-kappa mp))
      (dolist (matrix (list (cl-mpm/particle:mp-stress mp) (cl-mpm/particle:mp-strain mp)))
        (dotimes (axis 6) (format stream ",~,16E" (component matrix axis))))
      (dotimes (row 3)
        (dotimes (col 3)
          (format stream ",~,16E" (magicl:tref (cl-mpm/particle::mp-deformation-gradient mp) row col))))
      (terpri stream))))

(defun zero-reporting-origin (sim)
  (let ((before (material-signature sim)))
    (loop for mp across (cl-mpm:sim-mps sim) do
      (cl-mpm/fastmaths:fast-zero (cl-mpm/particle:mp-velocity mp))
      (cl-mpm/fastmaths:fast-zero (cl-mpm/particle::mp-acceleration mp))
      (cl-mpm/fastmaths:fast-zero (cl-mpm/particle::mp-displacement mp)))
    (cl-mpm:iterate-over-nodes (cl-mpm:sim-mesh sim)
      (lambda (node)
        (cl-mpm/fastmaths:fast-zero (cl-mpm/mesh:node-velocity node))
        (cl-mpm/fastmaths:fast-zero (cl-mpm/mesh:node-acceleration node))))
    (setf (cl-mpm::sim-time sim) 0d0)
    (unless (equalp before (material-signature sim))
      (error "Reporting reset changed the gravity internal state."))
    t))

(defun stable-dt (sim config)
  (let ((dt (* (gethash "timeStepScale" config) (cl-mpm/setup:estimate-elastic-dt sim))))
    (unless (and (finite-p dt) (> dt 0d0)) (error "Invalid native stability timestep."))
    dt))

(defun run (material config directory)
  "Run actual explicit native MPM; retain incomplete/failure status and raw evidence."
  (let* ((output (uiop:ensure-directory-pathname directory))
         (vtk (merge-pathnames "vtk/" output))
         (manifest-path (merge-pathnames "manifest.json" output))
         (manifest (json-object
                    "scenario" "slope-descent" "status" "running" "complete" 'yason:false
                    "gravityConverged" 'yason:false "reportingResetPreservedState" 'yason:false
                    "config" config "formulation" "explicit USF MPM, 2D plane strain, unit thickness"
                    "loading" "bilateral tracked top-strip displacement penalty; finite compliance"
                    "convergenceScope" "gravity initialization only"
                    "reactionConvention" "actuator reaction +Y = minus applied soil force Y; raw signed values"
                    "geometryProvenance" "height is a user-supplied assumption; no paper height is inferred"
                    "massScale" 1d0 "scientificallyValidated" 'yason:false))
         (settle-updates 0) (updates 0) (frame 0) (sim nil))
    (ensure-directories-exist vtk)
    (write-json manifest-path manifest)
    (handler-case
        (progn
          (cl-mpm/utils:set-workers (gethash "workers" config))
          (multiple-value-bind (native top-row) (make-slope material config)
            (setf sim native)
            (let* ((diagnostics (cl-mpm/framework:material-diagnostics material))
                   (reference-mass (reduce #'+ (cl-mpm:sim-mps sim) :key #'cl-mpm/particle:mp-mass))
                   (original-intervals (make-hash-table :test 'eq))
                   (hold 0) (converged nil))
              (cl-mpm/framework:configure-material-output diagnostics sim)
              (loop for mp across top-row do
                (let ((x (component (cl-mpm/particle:mp-position mp) 0))
                      (half (* .5d0 (component (cl-mpm/particle::mp-domain-size mp) 0))))
                  (setf (gethash mp original-intervals) (cons (- x half) (+ x half)))))
              (setf (cl-mpm:sim-damping-factor sim) (gethash "settleDamping" config))
              (cl-mpm/output:save-vtk-mesh (merge-pathnames "mesh.vtk" vtk) sim)
              (cl-mpm/output:save-vtk (merge-pathnames "gravity_initial.vtk" vtk) sim)
              (setf (gethash "particleCount" manifest) (length (cl-mpm:sim-mps sim))
                    (gethash "initialMassKgPerM" manifest) reference-mass
                    (gethash "phase" manifest) "gravity")
              (write-json manifest-path manifest)
              (with-open-file (history (merge-pathnames "gravity-history.csv" output)
                                       :direction :output :if-exists :supersede :if-does-not-exist :create)
                (format history "updates,time_s,kinetic_energy_J_per_m,kinetic_ratio,free_residual_ratio,mass_error_fraction,max_yield_residual_pa,consecutive_checks~%")
                (loop while (< settle-updates (gethash "settleMaxUpdates" config)) do
                  (setf (cl-mpm:sim-dt sim) (stable-dt sim config))
                  (cl-mpm:update-sim sim) (incf settle-updates)
                  (when (or (zerop (mod settle-updates 25))
                            (= settle-updates (gethash "settleMaxUpdates" config)))
                    (multiple-value-bind (mass ke kinetic residual mass-error max-yield)
                        (state-statistics sim diagnostics reference-mass config)
                      (declare (ignore mass))
                      (setf hold (if (and (>= settle-updates (gethash "settleMinUpdates" config))
                                          (< kinetic (expt (gethash "settleTolerance" config) 2))
                                          (< residual (gethash "settleTolerance" config))
                                          (<= max-yield (* 1d-6 (gethash "E" config))))
                                     (1+ hold) 0))
                      (format history "~D,~,12E,~,12E,~,12E,~,12E,~,12E,~,12E,~D~%"
                              settle-updates (cl-mpm::sim-time sim) ke kinetic residual mass-error max-yield hold)
                      (setf (gethash "gravityKineticRatio" manifest) kinetic
                            (gethash "gravityFreeResidualRatio" manifest) residual
                            (gethash "gravityMaxYieldResidualPa" manifest) max-yield
                            (gethash "settleUpdates" manifest) settle-updates)
                      (when (>= hold (gethash "settleHoldChecks" config))
                        (setf converged t) (return))))))
              (unless converged (error "Gravity failed sustained equilibrium/admissibility criteria within ~D updates." settle-updates))
              (setf (gethash "gravityConverged" manifest) t
                    (gethash "gravityTimeS" manifest) (cl-mpm::sim-time sim))
              (cl-mpm/output:save-vtk (merge-pathnames "gravity_equilibrium.vtk" vtk) sim)
              (write-gravity-state sim (merge-pathnames "gravity-state.csv" output))
              (zero-reporting-origin sim)
              (setf (gethash "reportingResetPreservedState" manifest) t)
              (let* ((bc (make-strip top-row config original-intervals))
                     (duration (gethash "duration" config))
                     (frames (gethash "frames" config)) (next-frame 1))
                (cl-mpm:add-bcs-force-list sim (vector bc))
                (setf (cl-mpm:sim-damping-factor sim) (gethash "dynamicDamping" config)
                      (gethash "phase" manifest) "prescribed-descent"
                      (gethash "stripContactCount" manifest) (length (strip-contacts bc))
                      (gethash "penaltyStiffnessPaPerM" manifest) (strip-epsilon bc)
                      (gethash "initialLoadingDtS" manifest) (stable-dt sim config)
                      (gethash "plannedLoadingUpdatesEstimate" manifest) (ceiling duration (stable-dt sim config)))
                (write-json manifest-path manifest)
                (with-open-file (csv (merge-pathnames "force-displacement.csv" output)
                                    :direction :output :if-exists :supersede :if-does-not-exist :create)
                  (format csv "frame,time_s,commanded_settlement_m,measured_settlement_m,reaction_upward_N_per_m,soil_force_y_N_per_m,nodal_force_y_N_per_m,kinetic_energy_J_per_m,mass_kg_per_m,particle_count,penalty_gap_m,free_residual_ratio,kinetic_ratio,mass_error_fraction,max_gap_m,rms_gap_m,max_yield_residual_pa,updates~%")
                  (labels ((save-state ()
                             (multiple-value-bind (mass ke kinetic residual mass-error max-yield)
                                 (state-statistics sim diagnostics reference-mass config)
                               (multiple-value-bind (actual max-gap rms-gap) (strip-measurements bc)
                                 (cl-mpm/output:save-vtk
                                  (merge-pathnames (format nil "particles_~4,'0D.vtk" frame) vtk) sim)
                                 (format csv "~D,~,12E,~,12E,~,12E,~,12E,~,12E,~,12E,~,12E,~,12E,~D,~,12E,~,12E,~,12E,~,12E,~,12E,~,12E,~,12E,~D~%"
                                         frame (cl-mpm::sim-time sim) (strip-target bc) actual
                                         (strip-reaction bc) (- (strip-reaction bc)) (- (strip-mapped-reaction bc))
                                         ke mass (length (cl-mpm:sim-mps sim)) (- (strip-target bc) actual)
                                         residual kinetic mass-error max-gap rms-gap max-yield updates)
                                 (finish-output csv)
                                 (setf (gethash "loadingUpdates" manifest) updates
                                       (gethash "timeS" manifest) (cl-mpm::sim-time sim)
                                       (gethash "commandedSettlementM" manifest) (strip-target bc)
                                       (gethash "measuredSettlementM" manifest) actual
                                       (gethash "reactionUpwardNPerM" manifest) (strip-reaction bc)
                                       (gethash "maxPenaltyGapM" manifest) max-gap
                                       (gethash "massErrorFraction" manifest) mass-error
                                       (gethash "finalFieldsFinite" manifest) t)
                                 (write-json manifest-path manifest)
                                 (incf frame)))))
                    (save-state)
                    (loop while (< (cl-mpm::sim-time sim) duration) do
                      (when (>= updates (gethash "maxUpdates" config))
                        (error "Loading update cap reached before the physical displacement target."))
                      (let* ((time (cl-mpm::sim-time sim))
                             (save-time (* duration (/ next-frame (1- frames))))
                             (next (min duration save-time (+ time (stable-dt sim config)))))
                        (setf (cl-mpm:sim-dt sim) (- next time)
                              (strip-target bc) (* (gethash "velocity" config) next))
                        (cl-mpm:update-sim sim) (incf updates)
                        (when (>= (cl-mpm::sim-time sim) save-time)
                          (save-state) (incf next-frame))))))
                (unless (and converged
                             (<= (abs (- (strip-target bc) (gethash "targetDisplacement" config))) 1d-12)
                             (>= (cl-mpm::sim-time sim) duration))
                  (error "Physical loading target was not reached."))
                (setf (gethash "phase" manifest) "finished" (gethash "status" manifest) "complete"
                      (gethash "complete" manifest) t (gethash "savedFrames" manifest) frame)
                (write-json manifest-path manifest)
                sim))))
      (error (condition)
        (setf (gethash "status" manifest) "failed" (gethash "complete" manifest) 'yason:false
              (gethash "error" manifest) (princ-to-string condition)
              (gethash "settleUpdates" manifest) settle-updates (gethash "loadingUpdates" manifest) updates)
        (write-json manifest-path manifest)
        (error condition)))))
