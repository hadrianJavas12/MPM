(in-package :cl-mpm/framework)

(defun cliff-mp-pos-x (mp) (magicl:tref (cl-mpm/particle:mp-position mp) 0 0))
(defun cliff-mp-pos-y (mp) (magicl:tref (cl-mpm/particle:mp-position mp) 1 0))

(defun cliff-mp-disp-mag (mp)
  (let ((d (cl-mpm/particle::mp-displacement mp)))
    (sqrt (+ (expt (magicl:tref d 0 0) 2)
             (expt (magicl:tref d 1 0) 2)))))

(defun cliff-mp-vel-mag (mp)
  (let ((v (cl-mpm/particle:mp-velocity mp)))
    (sqrt (+ (expt (magicl:tref v 0 0) 2)
             (expt (magicl:tref v 1 0) 2)))))

(defun run-mc-evolution-cliff (material config directory)
  "Two-stage MPM cliff/slope runner for :MC-H and :MC-HS following Urmi et al. (2024)
Section 4 (Stage 1: high-damping elastic gravity stress initialization; Stage 2:
low-damping elasto-plastic progressive failure propagation) with full CSV/VTK/manifest output."
  (let* ((output-dir (uiop:ensure-directory-pathname directory))
         (vtk-dir (merge-pathnames "vtk/" output-dir))
         (diagnostics (material-diagnostics material))
         (h (float (gethash "meshSize" config) 1d0))
         (height (float (gethash "shelfHeight" config) 1d0))
         (soil (float (gethash "soilBoundary" config) 1d0))
         (shelf-aspect (float (or (gethash "elongatedShelfAspect" config)
                                  (gethash "shelfAspect" config)) 1d0))
         (runout-aspect (float (or (gethash "runoutAspect" config)
                                   cl-mpm/framework/cliff::*runout-aspect*) 1d0))
         (shelf-length (* height shelf-aspect))
         (domain-length (+ shelf-length (* runout-aspect height)))
         (block-size (list domain-length (+ height soil)))
         (cells (list (ceiling domain-length h)
                      (ceiling (+ height soil (* 8d0 h)) h)))
         (frames (round (gethash "maxSteps" config)))
         (substeps (round (gethash "substeps" config)))
         (settle-steps (round (or (gethash "settleSteps" config) 200)))
         (cfl-scale (float (or (gethash "cflScale" config) 0.25d0) 1d0))
         (e-mod (float (gethash "E" config) 1d0))
         (nu (float (gethash "nu" config) 1d0))
         (rho (float (gethash "density" config) 1d0))
         (p-mod (cl-mpm/particle::calculate-p-wave-modulus e-mod nu))
         (cp (sqrt (/ p-mod rho)))
         ;; Urmi et al. (2024) Section 4: high damping (alpha=0.75) in Stage 1,
         ;; low damping (alpha=0.02) in Stage 2.
         (damping-settle (* 0.75d0 (/ cp h)))
         (damping-dynamic (* 0.02d0 (/ cp h)))
         (start-wall (get-internal-real-time)))
    (ensure-directories-exist vtk-dir)
    (cl-mpm/utils:set-workers (round (gethash "workers" config)))
    (let ((sim (cl-mpm/setup:make-simple-sim
                h cells
                :args-list (list :enable-fbar nil :enable-damage nil
                                 :ghost-factor nil :enable-split nil
                                 :mp-removal-size nil))))
      (setf (cl-mpm:sim-mps sim)
            (funcall (cliff-particle-factory material) config block-size h))
      (cl-mpm/framework/cliff::cut-cliff-face sim config shelf-length soil)
      (cl-mpm/framework/cliff::cut-toe-notch sim config shelf-length soil)
      (setf (cl-mpm:sim-allow-mp-split sim) nil
            (cl-mpm::sim-enable-damage sim) nil
            (cl-mpm::sim-enable-fbar sim) nil
            (cl-mpm::sim-mp-removal-size sim) nil
            (cl-mpm::sim-mass-filter sim) 1d-15
            (cl-mpm::sim-mass-scale sim) 1d0
            (cl-mpm:sim-gravity sim) -9.80665d0
            (cl-mpm::sim-velocity-algorithm sim) :FLIP)
      (setf (cl-mpm:sim-bcs sim)
            (cl-mpm/bc::make-outside-bc-var
             (cl-mpm:sim-mesh sim)
             (lambda (i) (cl-mpm/bc::make-bc-fixed i '(0 nil nil)))
             (lambda (i) (cl-mpm/bc::make-bc-fixed i '(0 nil nil)))
             (lambda (i) (cl-mpm/bc::make-bc-fixed i '(0 0 nil)))
             (lambda (i) (cl-mpm/bc::make-bc-fixed i '(0 0 nil)))
             (lambda (i) (cl-mpm/bc::make-bc-fixed i '(nil nil 0)))
             (lambda (i) (cl-mpm/bc::make-bc-fixed i '(nil nil 0)))))
      (configure-material-output diagnostics sim)
      (cl-mpm/output:save-vtk-mesh (merge-pathnames "mesh.vtk" vtk-dir) sim)

      ;; Stage 1: Quasi-static elastic gravity initialization (plasticity disabled)
      (loop for mp across (cl-mpm:sim-mps sim) do
        (setf (cl-mpm/particle::mp-enable-plasticity mp) nil
              (cl-mpm/particle::mp-gravity mp) -9.80665d0))
      (setf (cl-mpm:sim-damping-factor sim) damping-settle)
      (let ((dt-cfl (* 0.25d0 (cl-mpm/setup:estimate-elastic-dt sim))))
        (setf (cl-mpm:sim-dt sim) dt-cfl)
        (format t "~&[CLIFF Stage 1] Gravity initialization: particles=~D dt=~,5E s settle-steps=~D damping=~,2F 1/s~%"
                (length (cl-mpm:sim-mps sim)) dt-cfl settle-steps damping-settle)
        (finish-output)
        (dotimes (s settle-steps)
          (cl-mpm:update-sim sim)))

      ;; Reset velocities and Stage-1 displacements while preserving equilibrated stress state
      (cl-mpm/framework/cliff::reference-zero-velocities sim)
      (loop for mp across (cl-mpm:sim-mps sim) do
        (cl-mpm/fastmaths::fast-zero (cl-mpm/particle::mp-displacement mp))
        (setf (cl-mpm/particle::mp-enable-plasticity mp) t))
      (setf (cl-mpm::sim-time sim) 0d0
            (cl-mpm:sim-damping-factor sim) damping-dynamic)

      (let* ((mps (cl-mpm:sim-mps sim))
             (initial-mass (reduce #'+ mps :key #'cl-mpm/particle:mp-mass))
             (initial-toe-x (loop for mp across mps
                                  when (> (cliff-mp-pos-y mp) (+ soil (* 0.25d0 h)))
                                    maximize (cliff-mp-pos-x mp)))
             (top-y (loop for mp across mps maximize (cliff-mp-pos-y mp)))
             (crest-mps (loop for mp across mps
                              when (and (>= (cliff-mp-pos-x mp) (* 0.55d0 shelf-length))
                                        (<= (cliff-mp-pos-x mp) (+ shelf-length h))
                                        (>= (cliff-mp-pos-y mp) (- top-y (* 3d0 h))))
                                collect mp))
             (initial-crest-y (if crest-mps
                                  (/ (reduce #'+ crest-mps :key #'cliff-mp-pos-y)
                                     (float (length crest-mps) 1d0))
                                  top-y))
             (ts-path (merge-pathnames "cliff-timeseries.csv" output-dir))
             (diag-path (merge-pathnames "material-diagnostics.csv" output-dir))
             (fields (diagnostics-fields diagnostics))
             (total-updates 0))
        (labels ((write-state (frame phase-label)
                   (let ((vol-total 0d0) (mass-total 0d0)
                         (mean-k 0d0) (max-k 0d0)
                         (mean-phi 0d0) (min-phi 90d0)
                         (mean-c 0d0) (min-c 1d30)
                         (yield-vol 0d0) (soft-vol 0d0)
                         (max-disp 0d0) (max-vel 0d0)
                         (ke 0d0) (pwork 0d0) (max-res -1d30)
                         (cur-toe-x initial-toe-x))
                     (loop for mp across (cl-mpm:sim-mps sim) do
                       (validate-material-state diagnostics mp)
                       (let* ((v (cl-mpm/particle:mp-volume mp))
                              (m (cl-mpm/particle:mp-mass mp))
                              (k (cl-mpm/models/mc-evolution:particle-kappa mp))
                              (phi-deg (cl-mpm/models/mc-evolution:particle-phi-deg mp))
                              (c-kpa (* 1d-3 (cl-mpm/models/mc-evolution:particle-cohesion mp)))
                              (soft (cl-mpm/models/mc-evolution:particle-softened-indicator mp))
                              (pw (cl-mpm/models/mc-evolution:particle-plastic-work mp))
                              (res (cl-mpm/models/mc-evolution:particle-yield-residual-kirchhoff mp))
                              (dmag (cliff-mp-disp-mag mp))
                              (vmag (cliff-mp-vel-mag mp)))
                         (incf vol-total v)
                         (incf mass-total m)
                         (incf mean-k (* v k))
                         (setf max-k (max max-k k))
                         (incf mean-phi (* v phi-deg))
                         (setf min-phi (min min-phi phi-deg))
                         (incf mean-c (* v c-kpa))
                         (setf min-c (min min-c c-kpa))
                         (when (> k 1d-6) (incf yield-vol v))
                         (incf soft-vol (* v soft))
                         (setf max-disp (max max-disp dmag)
                               max-vel (max max-vel vmag)
                               max-res (max max-res res))
                         (incf ke (* 0.5d0 m (expt vmag 2)))
                         (incf pwork (* v pw))
                         (when (> (cliff-mp-pos-y mp) (+ soil (* 0.25d0 h)))
                           (setf cur-toe-x (max cur-toe-x (cliff-mp-pos-x mp))))))
                     (assert (< (abs (- mass-total initial-mass)) (* 1d-12 initial-mass))
                             () "Cliff mass conservation violated: ~E vs ~E" mass-total initial-mass)
                     (let* ((cur-crest-y (if crest-mps
                                             (/ (reduce #'+ crest-mps :key #'cliff-mp-pos-y)
                                                (float (length crest-mps) 1d0))
                                             initial-crest-y))
                            (toe-runout (max 0d0 (- cur-toe-x initial-toe-x)))
                            (crest-settle (max 0d0 (- initial-crest-y cur-crest-y)))
                            (sim-t (cl-mpm::sim-time sim)))
                       (cl-mpm/output:save-vtk
                        (merge-pathnames (format nil "sim_~5,'0D.vtk" frame) vtk-dir) sim)
                       (with-open-file (csv ts-path :direction :output
                                                    :if-exists (if (zerop frame) :supersede :append)
                                                    :if-does-not-exist :create)
                         (when (zerop frame)
                           (format csv "frame,updates,time_s,phase,mean_kappa,max_kappa,mean_phi_deg,min_phi_deg,mean_c_kpa,min_c_kpa,yielded_fraction,softened_fraction,toe_runout_m,crest_settlement_m,max_disp_m,max_vel_m_s,kinetic_energy_j,plastic_work_j,mass_kg,max_yield_residual_pa~%"))
                         (format csv "~D,~D,~,10F,~A,~,12F,~,12F,~,10F,~,10F,~,10F,~,10F,~,10F,~,10F,~,10F,~,10F,~,10F,~,10F,~,10F,~,10F,~,10F,~,12E~%"
                                 frame total-updates sim-t phase-label
                                 (/ mean-k vol-total) max-k
                                 (/ mean-phi vol-total) min-phi
                                 (/ mean-c vol-total) min-c
                                 (/ yield-vol vol-total) (/ soft-vol vol-total)
                                 toe-runout crest-settle max-disp max-vel
                                 ke pwork mass-total max-res))
                       (with-open-file (dcsv diag-path :direction :output
                                                       :if-exists (if (zerop frame) :supersede :append)
                                                       :if-does-not-exist :create)
                         (when (zerop frame)
                           (format dcsv "frame,time_s")
                           (dolist (field fields)
                             (format dcsv ",~(~A~)_~A" (third field) (first field)))
                           (terpri dcsv))
                         (format dcsv "~D,~,10F" frame sim-t)
                         (dolist (field fields)
                           (destructuring-bind (name unit reduction accessor definition) field
                             (declare (ignore name unit definition))
                             (let ((result nil))
                               (loop for mp across (cl-mpm:sim-mps sim)
                                     for sample = (funcall accessor mp) do
                                       (setf result
                                             (ecase reduction
                                               (:mean (+ (or result 0d0) (* sample (cl-mpm/particle:mp-volume mp))))
                                               (:max (if result (max result sample) sample)))))
                               (format dcsv ",~,12F" (if (eq reduction :mean) (/ result vol-total) result)))))
                         (terpri dcsv))
                       (format t "~&CLIFF frame=~D/~D updates=~D t=~,4F s max_k=~,4F min_phi=~,2F deg max_disp=~,4F m toe_runout=~,4F m KE=~,4E J~%"
                               frame frames total-updates sim-t max-k min-phi max-disp toe-runout ke)
                       (finish-output)))))
          (write-state 0 "stage1_equilibrated")
          (dotimes (i frames)
            (let ((step (1+ i)))
              (dotimes (s substeps)
                (setf (cl-mpm:sim-dt sim)
                      (* cfl-scale (cl-mpm/setup:estimate-elastic-dt sim)))
                ;; Diagnose the precise failed update while preserving the
                ;; original fail-closed error and leaving MPM physics unchanged.
                (handler-case
                    (cl-mpm:update-sim sim)
                  (cl-mpm/errors:error-dF-negative (failure)
                    (format *error-output*
                            "~&CLIFF NUMERICAL_FAILURE ERROR-DF-NEGATIVE frame=~D substep=~D/~D completed_updates=~D time_s=~,10E dt_s=~,10E cfl_scale=~,5F~%"
                            step (1+ s) substeps total-updates
                            (cl-mpm::sim-time sim) (cl-mpm:sim-dt sim) cfl-scale)
                    (finish-output *error-output*)
                    (error failure)))
                (incf total-updates))
              (write-state step "stage2_dynamic")))
          (let ((manifest (make-hash-table :test #'equal))
                (clean-cfg (make-hash-table :test #'equal)))
            (maphash (lambda (k v)
                       (setf (gethash k clean-cfg)
                             (cond ((eq v t) t)
                                   ((null v) 'yason:false)
                                   ((symbolp v) (string-downcase (symbol-name v)))
                                   (t v))))
                     config)
            (setf (gethash "complete" manifest) t
                  (gethash "scenario" manifest) "cliff"
                  (gethash "materialKind" manifest) (string-downcase (symbol-name (component-kind material)))
                  (gethash "nativeModel" manifest) "cl-mpm/models/mc-evolution::particle-mc-evolution"
                  (gethash "protocol" manifest) "Urmi et al. (2024) two-stage MPM landslide protocol (Stage 1 elastic gravity settle alpha=0.75; Stage 2 dynamic elasto-plastic evolution alpha=0.02)"
                  (gethash "particleCount" manifest) (length mps)
                  (gethash "settleSteps" manifest) settle-steps
                  (gethash "dynamicUpdates" manifest) total-updates
                  (gethash "frames" manifest) frames
                  (gethash "wallSeconds" manifest)
                  (/ (- (get-internal-real-time) start-wall)
                     (float internal-time-units-per-second 1d0)))
            (with-open-file (out (merge-pathnames "effective-config.json" output-dir)
                                 :direction :output :if-exists :supersede)
              (yason:encode clean-cfg out))
            (with-open-file (out (merge-pathnames "manifest.json" output-dir)
                                 :direction :output :if-exists :supersede)
              (yason:encode manifest out)))
          sim)))))

(defmethod execute-scenario ((scenario (eql :cliff)) (case simulation) config directory)
  (let ((material (resolve-material (simulation-material case) config
                                   '((:youngs-modulus "E" 5d6) (:poisson-ratio "nu" 0.49d0)
                                     (:density "density" 1800d0)
                                     (:plasticity "enablePlasticity" t))))
        (filter (geometry-filter (simulation-geometry case))))
    (when filter (error "Generic cliff filter uses the native geometry callback API; this clipping predicate is for triaxial."))
    (if (member (component-kind material) '(:mc-h :mc-hs))
        (run-mc-evolution-cliff material config directory)
        (cl-mpm/framework/cliff:run
         config directory :cliff-builder
         (lambda (config)
           (let ((sim (cl-mpm/framework/cliff:make-cliff-sim
                       config :particle-factory (unless (eq (component-kind material) :chalk)
                                                  (cliff-particle-factory material)))))
             (unless (eq (component-kind material) :chalk)
               (configure-material-output (material-diagnostics material) sim))
             sim))))))
