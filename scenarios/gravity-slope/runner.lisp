(in-package :cl-mpm/scenario/gravity-slope)

(defun stable-dt (sim config)
  (let ((dt (* (gethash "timeStepScale" config) (cl-mpm/setup:estimate-elastic-dt sim))))
    (unless (and (finite-p dt) (> dt 0d0)) (error "Invalid gravity-slope stability timestep."))
    dt))

(defun make-manifest (config)
  (json-object
   "scenario" "gravity-slope" "status" "running" "complete" 'yason:false
   "phase" "initialization" "timeS" 0d0 "updates" 0 "savedFrames" 0 "config" config
   "scientificallyValidated" 'yason:false "landslideVerified" 'yason:false
   "formulation" "explicit USF MPM; 2D plane strain; unit out-of-plane thickness; FLIP; Fbar disabled"
   "loading" "gravity only; zero-stress/zero-velocity origin; plasticity active throughout smoothstep ramp"
   "gravitySchedule" "g(t_step_end)=gravity*r^2*(3-2*r), r=min(t_step_end/gravityRampDuration,1); actual sim-gravity is updated before each native step"
   "initialization" "no elastic settling, origin reset, state erasure, prestress or driver"
   "strengthReduction" "independent pre-reduced perfect Cauchy MC: c/F and atan(tan(phi)/F); SRF1.40 is a critical-bracket trial, not guaranteed unstable"
   "geometryProvenance" (gethash "geometryProvenance" config)
   "geometry" "unnotched trapezoid from (0,0), (width,0), (crestLength,height), (0,height); air beyond toe; no foundation layer"
   "boundaries" "left/right x rollers; bottom x/y fixed; top free. Fixed grid bottom is not a calibrated Coulomb runout bed"
   "particleIdConvention" "zero-based captured initial sim-mps vector index; count and object identity/order verified at every saved frame"
   "freeUpperSubset" "fixed initial MPs with x_initial > 2*meshSize AND y_initial > 2*meshSize; no driven contacts exist"
   "motionObservables" "mass-weighted centroid/velocity/RMS on fixed subset; coherence=norm(mean velocity)/RMS speed; moving threshold=0.001 m/s; downslope=(cos(beta),-sin(beta)) includes settlement; toe crossing compares current center x to initial geometric toe"
   "boundaryObservables" "center and half-particle-domain distances to grid edges; near-boundary mass uses center distance < meshSize; kernel-support adequacy is not certified. Center outside grid fails without deletion or clamping"
   "massScale" 1d0 "damping" 0d0 "driverCount" 0 "notchCount" 0
   "limits" "coarse explicit gravity/SSR onset adaptation; ramp/inertia/mesh/dt and fixed-base effects remain unvalidated; completion and color alone do not establish landslide or quantitative runout"))

(defun run (material config directory)
  "Run real native MPM and retain paired CSV/VTK evidence, including on failure."
  (let* ((output (uiop:ensure-directory-pathname directory))
         (vtk (merge-pathnames "vtk/" output))
         (manifest-path (merge-pathnames "manifest.json" output))
         (manifest (make-manifest config)) (sim nil) (updates 0) (saved 0))
    (ensure-directories-exist vtk)
    (write-json manifest-path manifest)
    (handler-case
        (progn
          (cl-mpm/utils:set-workers (gethash "workers" config))
          (setf sim (build-slope material config))
          (let* ((reference (capture-reference-state sim config))
                 (diagnostics (cl-mpm/framework:material-diagnostics material))
                 (duration (gethash "duration" config)) (frames (gethash "frames" config)))
            (cl-mpm/framework:configure-material-output diagnostics sim)
            (setf (gethash "particleCount" manifest) (length (cl-mpm:sim-mps sim))
                  (gethash "initialMassKgPerM" manifest) (reference-state-mass reference)
                  (gethash "freeUpperMassKgPerM" manifest) (reference-state-upper-mass reference)
                  (gethash "analyticalPolygonAreaM2" manifest)
                  (* .5d0 (gethash "height" config)
                     (+ (gethash "width" config) (gethash "crestLength" config)))
                  (gethash "initialStableDtS" manifest) (stable-dt sim config)
                  (gethash "phase" manifest) "gravity-ramp")
            (cl-mpm/output:save-vtk-mesh (merge-pathnames "mesh.vtk" vtk) sim)
            (cl-mpm/output/history:with-retained-history
                (history (merge-pathnames "history.csv" output) :direction :output
                         :if-exists :supersede :if-does-not-exist :create)
              (cl-mpm/output/history:with-retained-history
                  (particles (merge-pathnames "particles.csv" output) :direction :output
                             :if-exists :supersede :if-does-not-exist :create)
                (format history "~{~A~^,~}~%" +history-columns+)
                (format particles "~{~A~^,~}~%" +particle-columns+)
                (labels ((save-state (frame)
                           (let* ((time (cl-mpm::sim-time sim))
                                  (factor (ramp-factor time (gethash "gravityRampDuration" config)))
                                  (stats (measure-state sim diagnostics reference config)))
                             (cl-mpm/output:save-vtk
                              (merge-pathnames (format nil "particles_~4,'0D.vtk" frame) vtk) sim)
                             (write-csv-row history
                                            (append (list frame time updates factor (cl-mpm:sim-gravity sim))
                                                    (mapcar (lambda (key) (gethash key stats))
                                                            (nthcdr 5 +history-columns+)))
                                            +history-columns+)
                             (loop for mp across (cl-mpm:sim-mps sim) for id from 0 do
                               (write-csv-row particles (particle-row mp reference id frame time)
                                              +particle-columns+))
                             (finish-output history) (finish-output particles)
                             (incf saved)
                             (setf (gethash "timeS" manifest) time
                                   (gethash "lastSavedTimeS" manifest) time
                                   (gethash "updates" manifest) updates
                                   (gethash "savedFrames" manifest) saved
                                   (gethash "lastSavedStatistics" manifest) stats
                                   (gethash "phase" manifest)
                                   (if (< time (gethash "gravityRampDuration" config)) "gravity-ramp" "gravity-hold"))
                             (write-json manifest-path manifest)
                             (format t "~&[gravity-slope] frame=~D time=~,5F updates=~D maxdisp=~,4E maxspeed=~,4E~%"
                                     frame time updates (gethash "max_displacement_m" stats)
                                     (gethash "max_speed_m_per_s" stats))
                             (finish-output))))
                  (save-state 0)
                  (loop for frame from 1 below frames
                        for target = (* duration (/ frame (1- frames))) do
                    (loop while (< (cl-mpm::sim-time sim) target) do
                      (when (>= updates (gethash "maxUpdates" config))
                        (error "Gravity-slope update cap reached before requested physical duration."))
                      (let* ((time (cl-mpm::sim-time sim))
                             (dt (min (stable-dt sim config) (- target time)))
                             (next (+ time dt)))
                        (unless (> next time) (error "Gravity-slope timestep cannot advance time."))
                        (setf (cl-mpm:sim-dt sim) dt
                              (cl-mpm:sim-gravity sim)
                              (* (gethash "gravity" config)
                                 (ramp-factor next (gethash "gravityRampDuration" config))))
                        (cl-mpm:update-sim sim) (incf updates)))
                    (save-state frame)))))
            (unless (and (= saved frames) (>= (cl-mpm::sim-time sim) duration))
              (error "Gravity-slope run did not reach every requested saved state."))
            (setf (gethash "status" manifest) "complete" (gethash "phase" manifest) "finished"
                  (gethash "complete" manifest) t)
            (write-json manifest-path manifest)
            sim))
      (error (condition)
        (setf (gethash "status" manifest) "failed" (gethash "complete" manifest) 'yason:false
              (gethash "error" manifest) (princ-to-string condition)
              (gethash "updates" manifest) updates (gethash "savedFrames" manifest) saved)
        (when sim (setf (gethash "attemptTimeS" manifest) (cl-mpm::sim-time sim)))
        (write-json manifest-path manifest)
        (error condition)))))
