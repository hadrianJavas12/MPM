;;;; Dedicated paper-reference experiment; ordinary Studio/chalk methods remain
;;;; unchanged. Numerical agreement with the supplied paper must be measured.
(in-package :cl-mpm-studio)

(defclass joss-reference-chalk (cl-mpm/particle::particle-chalk-delayed)
  ((plastic-cohesion :initarg :reference-cohesion :reader reference-cohesion)
   (plastic-friction :initarg :reference-friction :reader reference-friction)
   (plastic-dilation :initarg :reference-dilation :reader reference-dilation)
   (tensile-ratio :initarg :reference-tensile :reader reference-tensile)
   (compression-ratio :initarg :reference-compression :reader reference-compression)
   (shear-ratio :initarg :reference-shear :reader reference-shear)))

(defmethod initialize-instance :after ((mp joss-reference-chalk) &key)
  ;; The inherited frictional constructor recalculates cohesion/phi/residual
  ;; shear. Restore the explicitly prescribed reference parameters afterwards.
  (setf (cl-mpm/particle::mp-c mp) (reference-cohesion mp)
        (cl-mpm/particle::mp-phi mp) (reference-friction mp)
        (cl-mpm/particle::mp-psi mp) (reference-dilation mp)
        (cl-mpm/particle::mp-k-tensile-residual-ratio mp) (reference-tensile mp)
        (cl-mpm/particle::mp-k-compressive-residual-ratio mp) (reference-compression mp)
        (cl-mpm/particle::mp-shear-residual-ratio mp) (reference-shear mp)))

(defmethod cl-mpm/damage::damage-model-calculate-y ((mp joss-reference-chalk) dt)
  (declare (ignore dt))
  ;; Author Joss example's DP driving stress; stored friction angle is radians.
  ;; Frozen-state comparison and a short physical pilot support this adaptation,
  ;; but do not establish full fracture/run-out agreement with the reference.
  (let ((value (max 0d0 (cl-mpm/damage::drucker-prager-criterion
                         (cl-mpm/particle::mp-undamaged-stress mp)
                         (cl-mpm/particle::mp-friction-angle mp)))))
    (setf (cl-mpm/particle::mp-damage-y-local mp) value
          (cl-mpm/particle::mp-local-damage-increment mp) value)))

(defmethod cl-mpm::update-particle (mesh (mp joss-reference-chalk) dt)
  (cl-mpm::update-particle-kirchoff mesh mp dt)
  (cl-mpm::update-domain-det mesh mp))

(defclass joss-reference-sim (cl-mpm/damage::mpm-sim-damage) ())

(defclass joss-reference-aggregate-sim
    (joss-reference-sim cl-mpm/aggregate::mpm-sim-aggregated) ()
  (:documentation "Reference-only cut-cell stabilization through the author's aggregate solver."))

(defun reference-finite-p (value)
  (and (typep value 'double-float)
       (not (sb-ext:float-nan-p value))
       (not (sb-ext:float-infinity-p value))))

(defun reference-critical-damping (config)
  "Paper Eq.24 for this 2D reference: beta_crit=(pi/2)*sqrt(E/(rho*h^2))."
  (* (/ pi 2d0)
     (sqrt (/ (param config "E")
              (* (param config "density") (expt (param config "meshSize") 2))))))

(defun reference-viscous-damping (config fraction)
  "Core uses -damping*M*v; paper uses -2*beta*M*v, so damping is 2*beta."
  (* 2d0 fraction (reference-critical-damping config)))

(defmethod cl-mpm::update-dynamic-stats ((sim joss-reference-sim))
  ;; Called by the explicit USF solver after force/velocity BCs are enforced.
  ;; OOBF excludes viscous damping: it measures internal + external imbalance.
  (let ((kinetic 0d0) (residual2 0d0) (external2 0d0) (work-increment 0d0))
    (let* ((mesh (cl-mpm:sim-mesh sim))
           (nodes (cl-mpm/mesh::mesh-nodes mesh))
           (nominal-volume (expt (cl-mpm/mesh:mesh-resolution mesh) (cl-mpm/mesh:mesh-nd mesh))))
      ;; Serial reduction: ITERATE-OVER-NODES is threaded and shared INCF
      ;; accumulators would lose updates with more than one worker.
      (loop for i below (array-total-size nodes)
            for node = (row-major-aref nodes i) do
       (when (cl-mpm/mesh:node-active node)
         ;; Mapped nodal volume, rather than node-volume-true, penalizes
         ;; ill-integrated nodes as in Eqs.64-66. For OOBF retain the engine's
         ;; L2 norm convention; the printed Eq.67 has ambiguous L1/square notation.
         (let ((weight (/ (cl-mpm/mesh::node-volume node) nominal-volume)))
           (unless (and (reference-finite-p weight) (>= weight 0d0))
             (error "Invalid mapped nodal-volume weight"))
           (incf kinetic (* weight 0.5d0 (cl-mpm/mesh:node-mass node)
                            (cl-mpm/fastmaths::mag-squared (cl-mpm/mesh:node-velocity node))))
           (dotimes (d 3)
             (let ((external (cl-mpm/utils:varef (cl-mpm/mesh::node-external-force node) d))
                   (internal (cl-mpm/utils:varef (cl-mpm/mesh::node-internal-force node) d))
                   (displacement (cl-mpm/utils:varef (cl-mpm/mesh::node-displacment node) d)))
               (incf residual2 (* weight (expt (+ internal external) 2)))
               (incf external2 (* weight (expt external 2)))
               (incf work-increment (* weight external displacement))))))))
    (unless (and (reference-finite-p kinetic) (reference-finite-p residual2)
                 (reference-finite-p external2) (reference-finite-p work-increment))
      (error "Nonfinite reference energy/force/work statistics"))
    (when (and (= external2 0d0) (> residual2 0d0))
      (error "Reference OOBF is undefined: zero external-force norm with a nonzero residual"))
    (setf (cl-mpm::sim-stats-energy sim) kinetic
          (cl-mpm::sim-stats-oobf sim) (if (> external2 0d0) (sqrt (/ residual2 external2)) 0d0)
          (cl-mpm::sim-stats-power sim) work-increment)
    (incf (cl-mpm::sim-stats-work sim) work-increment)
    (unless (reference-finite-p (cl-mpm::sim-stats-work sim))
      (error "Nonfinite accumulated reference work"))))

(defun reference-aggregate-statistics (sim)
  ;; The independent aggregate DOFs satisfy E^T*(f_int+f_ext)=0. Their dependent
  ;; exterior nodal forces need not vanish individually. Keep viscous damping
  ;; out of the physical residual, and do not count aggregate nodes twice.
  (let* ((mesh (cl-mpm:sim-mesh sim))
         (nodes (cl-mpm/mesh::mesh-nodes mesh))
         (energy 0d0) (residual2 0d0) (external2 0d0) (increment 0d0))
    (loop for i below (array-total-size nodes)
          for node = (row-major-aref nodes i) do
      (when (and (cl-mpm/mesh:node-active node) (not (cl-mpm/mesh::node-agg node)))
        (incf energy (* 0.5d0 (cl-mpm/mesh:node-mass node)
                       (cl-mpm/fastmaths::mag-squared (cl-mpm/mesh:node-velocity node))))
        (dotimes (d (cl-mpm/mesh:mesh-nd mesh))
          (let ((external (cl-mpm/utils:varef (cl-mpm/mesh::node-external-force node) d))
                (internal (cl-mpm/utils:varef (cl-mpm/mesh::node-internal-force node) d))
                (disp (cl-mpm/utils:varef (cl-mpm/mesh::node-displacment node) d)))
            (incf residual2 (expt (+ internal external) 2))
            (incf external2 (expt external 2))
            (incf increment (* external disp))))))
    (dotimes (d (cl-mpm/mesh:mesh-nd mesh))
      (let* ((external (cl-mpm/aggregate::assemble-global-vec sim #'cl-mpm/mesh::node-external-force d))
             (internal (cl-mpm/aggregate::assemble-global-vec sim #'cl-mpm/mesh::node-internal-force d))
             (residual (cl-mpm/fastmaths::fast-.+ external internal))
             (disp (cl-mpm/aggregate::assemble-global-vec sim #'cl-mpm/mesh::node-displacment d))
             (velocity (cl-mpm/aggregate::assemble-internal-vec sim #'cl-mpm/mesh::node-velocity d)))
        (incf residual2 (cl-mpm/fastmaths::mag-squared (cl-mpm/aggregate::aggregate-vec sim residual d)))
        (incf external2 (cl-mpm/fastmaths::mag-squared (cl-mpm/aggregate::aggregate-vec sim external d)))
        (incf increment (cl-mpm/fastmaths:dot disp external))
        (incf energy (* 0.5d0 (cl-mpm/fastmaths:dot velocity
                              (cl-mpm/aggregate::@-mass-matrix-vec sim velocity d))))))
    (dolist (value (list energy residual2 external2 increment))
      (unless (reference-finite-p value) (error "Nonfinite aggregate reference statistic")))
    (when (and (= external2 0d0) (> residual2 0d0))
      (error "Aggregate reference OOBF is undefined: zero external norm with nonzero residual"))
    (values energy (if (> external2 0d0) (sqrt (/ residual2 external2)) 0d0) increment)))

(defmethod cl-mpm::update-dynamic-stats ((sim joss-reference-aggregate-sim))
  (multiple-value-bind (energy oobf increment) (reference-aggregate-statistics sim)
    (setf (cl-mpm::sim-stats-energy sim) energy
          (cl-mpm::sim-stats-oobf sim) oobf
          (cl-mpm::sim-stats-power sim) increment)
    (incf (cl-mpm::sim-stats-work sim) increment)
    (unless (reference-finite-p (cl-mpm::sim-stats-work sim))
      (error "Nonfinite accumulated aggregate reference work"))))

(defun reference-energy-ratio (sim)
  (let ((energy (cl-mpm::sim-stats-energy sim))
        (work (abs (cl-mpm::sim-stats-work sim))))
    (cond ((> work 0d0) (/ energy work))
          ((= energy 0d0) 0d0)
          (t (error "Reference energy ratio is undefined: zero accumulated work with nonzero kinetic energy")))))

(defun reference-next-state (state epsilon oobf tolerance)
  "Algorithm 1: strict exceedance enters collapse; both strictly below leave it."
  (unless (and (reference-finite-p epsilon) (reference-finite-p oobf))
    (error "Nonfinite adaptive mass-scaling criterion"))
  (ecase state
    (:accelerate (if (or (> epsilon tolerance) (> oobf tolerance)) :collapse :accelerate))
    (:collapse (if (and (< epsilon tolerance) (< oobf tolerance)) :accelerate :collapse))))

(defun reference-zero-velocities (sim)
  (cl-mpm::iterate-over-mps
   (cl-mpm:sim-mps sim)
   (lambda (mp) (cl-mpm/fastmaths::fast-zero (cl-mpm/particle:mp-velocity mp))))
  (cl-mpm::iterate-over-nodes
   (cl-mpm:sim-mesh sim)
   (lambda (node) (cl-mpm/fastmaths::fast-zero (cl-mpm/mesh:node-velocity node)))))

(defun reference-face-x (config y)
  (let* ((base (param config "soilBoundary"))
         (height (param config "shelfHeight"))
         (toe (* height (param config "shelfAspect")))
         (lower-height (- height (param config "upperVerticalHeight")))
         (inward-per-height (/ 1d0 (tan (deg->rad (param config "cliffSlope"))))))
    (- toe (* inward-per-height (min lower-height (max 0d0 (- y base)))))))

(defun reference-solid-p (config x y)
  (let* ((base (param config "soilBoundary"))
         (toe (* (param config "shelfHeight") (param config "shelfAspect")))
         (notch (param config "notchDepth")))
    (or (<= y base)
        (and (<= x (reference-face-x config y))
             ;; 45-degree wave-notch ramp; foundation is preserved.
             (>= (- y base) (+ (- x toe) notch))))))

(defun reference-surface-height (config x)
  (let* ((base (param config "soilBoundary"))
         (height (param config "shelfHeight"))
         (toe (* height (param config "shelfAspect")))
         (kink-x (reference-face-x config (+ base height))))
    (cond ((<= x kink-x) (+ base height))
          ((< x toe) (+ base (* (- toe x) (tan (deg->rad (param config "cliffSlope"))))))
          (t base))))

(defun reference-domain-corners (config mp)
  (let* ((position (cl-mpm/particle:mp-position mp))
         (size (cl-mpm/particle::mp-domain-size mp))
         (x (cl-mpm/utils:varef position 0))
         (y (cl-mpm/utils:varef position 1))
         (dx (* 0.5d0 (cl-mpm/utils:varef size 0)))
         (dy (* 0.5d0 (cl-mpm/utils:varef size 1))))
    (loop for sx in '(-1d0 1d0) append
      (loop for sy in '(-1d0 1d0)
            collect (reference-solid-p config (+ x (* sx dx)) (+ y (* sy dy)))))))

(defun reference-clip-geometry (sim config)
  ;; Each loop is one bisection of partially intersecting domains, at most the
  ;; prescribed count per MP; reject fully removed domains between bisections.
  (dotimes (depth (param config "geometryRefinement"))
    (cl-mpm::split-mps-criteria
     sim
     (lambda (mp h)
       (declare (ignore h))
       (let ((corners (reference-domain-corners config mp)))
         (when (and (some #'identity corners) (not (every #'identity corners)))
           (if (>= (cl-mpm/utils:varef (cl-mpm/particle::mp-domain-size mp) 0)
                   (cl-mpm/utils:varef (cl-mpm/particle::mp-domain-size mp) 1))
               :x :y)))))
    (cl-mpm::remove-mps-func sim
      (lambda (mp) (not (some #'identity (reference-domain-corners config mp))))))
  (cl-mpm::remove-mps-func
   sim
   (lambda (mp)
     (not (reference-solid-p config
             (cl-mpm/utils:varef (cl-mpm/particle:mp-position mp) 0)
             (cl-mpm/utils:varef (cl-mpm/particle:mp-position mp) 1)))))
  sim)

(defun make-joss-reference-sim (config &key (aggregate t))
  (let* ((h (param config "meshSize"))
         (height (param config "shelfHeight"))
         (base (param config "soilBoundary"))
         (length (* height (+ (param config "shelfAspect") (param config "runoutAspect"))))
         (mps (param config "mpsPerCell"))
         (size (list length (+ height base)))
         (counts (mapcar (lambda (extent) (max 1 (round (* extent mps) h))) size))
         (cells (list (ceiling length h) (ceiling (+ height base (* 5d0 h)) h)))
         (damage-angle (param config "damageFrictionAngle"))
         (initiation (cl-mpm/damage::mohr-coloumb-coheasion-to-tensile
                       (param config "damageCohesion") damage-angle))
         ;; Eq. (44) uses k=1; the helper's default k=2 is a different estimate.
         (ductility (cl-mpm/damage::estimate-ductility-jirsek2004
                      (param config "fractureEnergy") (param config "nonlocalLength")
                      initiation (param config "E") 1d0))
         ;; The raw reference class remains available for bounded comparisons.
         (sim (cl-mpm/setup::make-block h cells :sim-type
                (if aggregate 'joss-reference-aggregate-sim 'joss-reference-sim))))
    (unless (and (> initiation 0d0) (> ductility 1d0)
                 (<= 0d0 (param config "upperVerticalHeight") height))
      (error "Invalid reference damage/geometry parameters (initiation=~A, ductility=~A)" initiation ductility))
    (setf (cl-mpm:sim-mps sim)
          (cl-mpm/setup::make-mps-from-list
           (cl-mpm/setup::make-block-mps-list
            '(0d0 0d0) size counts (param config "density") 'joss-reference-chalk
            :E (param config "E") :nu (param config "nu")
            :friction-angle (deg->rad damage-angle)
            :residual-friction (deg->rad 30d0) :oversize 0.99d0
            :initiation-stress initiation :ductility ductility
            :local-length (param config "nonlocalLength")
            :delay-time (param config "delayTime")
            :delay-exponent (param config "damageDelayExponent")
            :reference-cohesion (param config "cohesion")
            :reference-friction (deg->rad (param config "frictionAngle"))
            :reference-dilation (deg->rad (param config "dilatancyAngle"))
            :reference-tensile (param config "residualTensileRatio")
            :reference-compression (param config "residualCompressionRatio")
            :reference-shear (param config "residualShearRatio")
            :index 0 :enable-damage nil :enable-plasticity nil
            :gravity -9.8d0 :gravity-axis (cl-mpm/utils:vector-from-list '(0d0 1d0 0d0)))))
    (reference-clip-geometry sim config)
    (unless (plusp (length (cl-mpm:sim-mps sim))) (error "Reference geometry removed all particles"))
    ;; Material tag survives later motion/splitting; the beach remains elastic.
    (loop for mp across (cl-mpm:sim-mps sim) do
      (setf (cl-mpm/particle::mp-index mp)
            (if (<= (cl-mpm/utils:varef (cl-mpm/particle:mp-position mp) 1) base) 1 0)))
    (setf (cl-mpm:sim-gravity sim) -9.8d0
          (cl-mpm::sim-enable-damage sim) nil
          (cl-mpm::sim-nonlocal-damage sim) t
          (cl-mpm/damage::sim-enable-length-localisation sim) t
          (cl-mpm::sim-enable-fbar sim) t
          (cl-mpm::sim-velocity-algorithm sim) :BLEND
          (cl-mpm::sim-mass-scale sim) 1d0
          (cl-mpm::sim-mass-filter sim) 0d0
          (cl-mpm::sim-max-split-depth sim) (param config "geometryRefinement")
          (cl-mpm:sim-allow-mp-split sim) t)
    (setf (cl-mpm:sim-bcs sim)
          (cl-mpm/bc::make-outside-bc-varfix (cl-mpm:sim-mesh sim)
            '(0 nil 0) '(0 nil 0) '(nil nil 0) '(0 0 0) '(nil nil 0) '(nil nil 0)))
    (cl-mpm/setup::initialise-stress-self-weight-vardatum
     sim (lambda (position) (reference-surface-height config (cl-mpm/utils:varef position 0))))
    (setf (cl-mpm:sim-dt sim)
          (cl-mpm/setup:estimate-elastic-dt sim :dt-scale (param config "timeStepScale")))
    sim))

(defun reference-summary (sim)
  (let ((mass 0d0) (damage-mass 0d0))
    (loop for mp across (cl-mpm:sim-mps sim) do
      (incf mass (cl-mpm/particle:mp-mass mp))
      (incf damage-mass (* (cl-mpm/particle:mp-mass mp) (cl-mpm/particle:mp-damage mp))))
    (values mass damage-mass)))

(defun reference-effective-material (sim)
  "Record the initialized material fields, including inherited constructor effects."
  (let ((mp (aref (cl-mpm:sim-mps sim) 0))
        (values (make-hash-table :test #'equal)))
    (setf (gethash "E" values) (cl-mpm/particle::mp-E mp)
          (gethash "nu" values) (cl-mpm/particle::mp-nu mp)
          (gethash "plasticCohesion" values) (cl-mpm/particle::mp-c mp)
          (gethash "plasticFrictionRadians" values) (cl-mpm/particle::mp-phi mp)
          (gethash "damageFrictionRadians" values) (cl-mpm/particle::mp-friction-angle mp)
          (gethash "damageInitiationStress" values) (cl-mpm/particle::mp-initiation-stress mp)
          (gethash "ductility" values) (cl-mpm/particle::mp-ductility mp)
          (gethash "nonlocalLength" values) (cl-mpm/particle::mp-local-length mp)
          (gethash "delayTime" values) (cl-mpm/particle::mp-delay-time mp)
          (gethash "damageDelayExponent" values) (cl-mpm/particle::mp-delay-exponent mp)
          (gethash "residualTensileRatio" values) (cl-mpm/particle::mp-k-tensile-residual-ratio mp)
          (gethash "residualCompressionRatio" values) (cl-mpm/particle::mp-k-compressive-residual-ratio mp)
          (gethash "residualShearRatio" values) (cl-mpm/particle::mp-shear-residual-ratio mp))
    values))

(defun reference-check-finite (sim)
  (loop for mp across (cl-mpm:sim-mps sim) do
    (dolist (value (list (cl-mpm/particle:mp-mass mp) (cl-mpm/particle:mp-volume mp)
                        (cl-mpm/particle:mp-damage mp) (cl-mpm/particle::mp-history-stress mp)))
      (unless (reference-finite-p value) (error "Nonfinite reference particle state")))
    (unless (and (> (cl-mpm/particle:mp-mass mp) 0d0)
                 (> (cl-mpm/particle:mp-volume mp) 0d0)
                 (<= 0d0 (cl-mpm/particle:mp-damage mp) 1d0))
      (error "Invalid reference particle mass/volume/damage bounds"))
    (dolist (vector (list (cl-mpm/particle:mp-position mp) (cl-mpm/particle:mp-velocity mp)
                         (cl-mpm/particle:mp-stress mp) (cl-mpm/particle::mp-domain-size mp)))
      (loop for value across (cl-mpm/utils::fast-storage vector) do
        (unless (reference-finite-p value) (error "Nonfinite reference position/velocity/stress/domain"))))
    (unless (and (> (cl-mpm/utils:varef (cl-mpm/particle::mp-domain-size mp) 0) 0d0)
                 (> (cl-mpm/utils:varef (cl-mpm/particle::mp-domain-size mp) 1) 0d0))
      (error "Invalid reference GIMP domain dimensions")))
  t)

(defun reference-csv-number (value)
  ;; Common Lisp prints double exponents as D; CSV consumers expect E.
  (substitute #\e #\d (string-downcase (format nil "~,12E" value))))

(defun reference-write-row (stream sim phase step time)
  (multiple-value-bind (mass damage-mass) (reference-summary sim)
    (format stream "~{~A~^,~}~%"
            (list step (format nil "~,12F" (if (eq phase :settle) 0d0 time))
                  (format nil "~,12F" (if (eq phase :settle) time 0d0))
                  (string-downcase (symbol-name phase))
                  (reference-csv-number (cl-mpm::sim-mass-scale sim))
                  (reference-csv-number (cl-mpm::sim-stats-energy sim))
                  (reference-csv-number (cl-mpm::sim-stats-work sim))
                  (reference-csv-number (reference-energy-ratio sim))
                  (reference-csv-number (cl-mpm::sim-stats-oobf sim))
                  (reference-csv-number mass) (reference-csv-number damage-mass)
                  (length (cl-mpm:sim-mps sim))))))

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
