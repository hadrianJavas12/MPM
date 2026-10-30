;;;; Explicit comparison: gentle upper face and steep lower toe, no weak seed.
(in-package :cl-mpm/scenario/residual-clay-slope)
(defparameter *toe-failure-directory* nil)
(defclass particle-clay-toe (cl-mpm/models/mc-hs-apex:particle-mc-hs-apex) ())
(defun toe-surface (cfg x)
  (let* ((crest (value cfg "crestLength")) (base (value cfg "baseHeight"))
         (height (value cfg "height")) (lower (value cfg "lowerFaceHeight"))
         (upper-tan (tan (* pi (/ (value cfg "upperSlopeDeg") 180d0))))
         (lower-tan (tan (* pi (/ (value cfg "lowerSlopeDeg") 180d0))))
         (kink (+ crest (/ (- height lower) upper-tan))))
    (+ base (cond ((<= x crest) height)
                 ((<= x kink) (- height (* (- x crest) upper-tan)))
                 (t (max 0d0 (- lower (* (- x kink) lower-tan))))))))

(defun toe-config ()
  (let ((cfg (fw:read-parameters "studio/reference/residual-clay-slope-quarter.json")))
    (setf (gethash "upperSlopeDeg" cfg) 20d0 (gethash "lowerSlopeDeg" cfg) 40d0
          (gethash "lowerFaceHeight" cfg) 3d0 (gethash "duration" cfg) 8d0
          (gethash "frames" cfg) 17 (gethash "explicitHsApex" cfg) t
          (gethash "toeProfile" cfg) t
          (gethash "toeX" cfg) (+ 24d0 (/ 7d0 (tan (* pi (/ 20d0 180d0))))
                                       (/ 3d0 (tan (* pi (/ 40d0 180d0))))))
    cfg))

(defun build-toe-slope (material cfg)
  (let* ((h (value cfg "meshSize")) (width (value cfg "domainWidth"))
         (top (+ (value cfg "baseHeight") (value cfg "height")))
         (ppc (value cfg "mpsPerCell"))
         (sim (cl-mpm/setup:make-simple-sim h (list (round width h) (round (value cfg "domainHeight") h))
                :sim-type 'u::urmi-proper-sim :args-list (list :enable-fbar nil :enable-damage nil
                  :ghost-factor nil :enable-split nil :mp-removal-size nil)))
         (mps (apply #'cl-mpm/setup:make-block-mps '(0d0 0d0) (list width top)
                (list (* (round width h) ppc) (* (round top h) ppc)) (value cfg "density")
                (fw:material-particle-class material) :gravity 0d0
                :gravity-axis (cl-mpm/utils:vector-from-list '(0d0 1d0 0d0))
                :body-force (cl-mpm/utils:vector-from-list '(0d0 0d0 0d0))
                :clip-func (lambda (x y z) (declare (ignore z)) (<= y (toe-surface cfg x)))
                (fw:material-particle-initargs material))))
    (cl-mpm:add-mps sim (remove-if-not (lambda (mp) (typep mp 'cl-mpm/particle:particle)) mps))
    (loop for mp across (cl-mpm:sim-mps sim) for id from 0 do (setf (cl-mpm/particle::mp-unique-index mp) id))
    (setf (cl-mpm:sim-gravity sim) 0d0 (cl-mpm::sim-mass-scale sim) 1d0
          (cl-mpm::sim-mass-filter sim) 1d-15 (cl-mpm::sim-mp-removal-size sim) nil
          (cl-mpm:sim-allow-mp-split sim) nil (cl-mpm::sim-velocity-algorithm sim) :FLIP
          (cl-mpm:sim-damping-factor sim) .75d0 (cl-mpm::sim-bcs-force-list sim) nil)
    (setf (cl-mpm:sim-bcs sim) (cl-mpm/bc::make-outside-bc-var (cl-mpm:sim-mesh sim)
      (lambda (i) (cl-mpm/bc:make-bc-fixed i '(0 nil nil)))
      (lambda (i) (cl-mpm/bc:make-bc-fixed i '(0 nil nil)))
      (lambda (i) (cl-mpm/bc:make-bc-fixed i '(nil nil nil)))
      (lambda (i) (cl-mpm/bc:make-bc-fixed i '(0 0 nil)))
      (lambda (i) (cl-mpm/bc:make-bc-fixed i '(nil nil 0)))
      (lambda (i) (cl-mpm/bc:make-bc-fixed i '(nil nil 0)))))
    (u::proper-setup sim) sim))

(defun capture-toe-increment-failure (mp dt fbar &optional (scope "Actual failing particle context; observed before unchanged condition propagates, not a restart"))
  (when *toe-failure-directory*
    (handler-case
      (let* ((stretch (cl-mpm/particle::mp-stretch-tensor mp))
             (df (cl-mpm/utils:matrix-eye 1d0)))
        (cl-mpm/fastmaths::fast-.+-matrix df stretch df)
        (ensure-directories-exist (merge-pathnames "actual-df-failure.json" *toe-failure-directory*))
        (write-json (merge-pathnames "actual-df-failure.json" *toe-failure-directory*)
          (obj "schema" "cl-mpm.toe-profile.incremental-deformation-guard.v1"
            "scope" scope
            "particleId" (cl-mpm/particle::mp-unique-index mp) "dtS" dt
            "fbar" (if fbar t 'yason:false)
            "position" (copy-seq (cl-mpm/utils:fast-storage (cl-mpm/particle:mp-position mp)))
            "F" (copy-seq (cl-mpm/utils:fast-storage (cl-mpm/particle:mp-deformation-gradient mp)))
            "F0" (copy-seq (cl-mpm/utils:fast-storage (cl-mpm/particle::mp-deformation-gradient-0 mp)))
            "stretchTensor" (copy-seq (cl-mpm/utils:fast-storage stretch))
            "dF" (copy-seq (cl-mpm/utils:fast-storage df))
            "detDF" (cl-mpm/fastmaths:det-3x3 df)
            "guard" "Original calculate-df rejects det(I+stretchTensor)<0; no clamp/retry")))
      (error (c) (format *error-output* "~&Failure context capture failed: ~A~%" c)))))
(defmethod cl-mpm::update-stress-mp :around (mesh (mp particle-clay-toe) dt fbar)
  (handler-bind ((cl-mpm/errors:error-dF-negative
                   (lambda (c) (declare (ignore c)) (capture-toe-increment-failure mp dt fbar))))
    (call-next-method)))

(defun toe-onset (sim ctx cfg)
  (let ((plastified 0) (damaged 0) (toe-plastic 0) (toe-damage 0)
        (max-k -1d0) (max-d -1d0) (max-k-xy nil) (max-d-xy nil))
    (loop for mp across (cl-mpm:sim-mps sim) for id from 0
          for initial = (aref (gs::reference-state-positions (observation-context-reference ctx)) id)
          for near = (and (< (abs (- (component initial 0) (value cfg "toeX"))) 3d0)
                          (< (abs (- (component initial 1) (value cfg "baseHeight"))) 3d0))
          for k = (mc:particle-kappa mp) for d = (damage-value mp) do
      (when (> k 1d-8) (incf plastified) (when near (incf toe-plastic)))
      (when (> d 1d-6) (incf damaged) (when near (incf toe-damage)))
      (when (> k max-k) (setf max-k k max-k-xy (vector (component initial 0) (component initial 1))))
      (when (> d max-d) (setf max-d d max-d-xy (vector (component initial 0) (component initial 1)))))
    (obj "nativeTimeS" (cl-mpm::sim-time sim) "plastifiedMPs" plastified "damagedMPs" damaged
         "toePlastifiedMPs" toe-plastic "toeDamagedMPs" toe-damage
         "maximumKappa" max-k "maximumDamage" max-d
         "maximumKappaInitialXY" max-k-xy "maximumDamageInitialXY" max-d-xy)))

(defun run-toe-profile (material cfg directory)
  (let* ((out (uiop:ensure-directory-pathname directory)) (vtk (merge-pathnames "vtk/" out))
         (sim nil) (ctx nil) (updates 0) (saved 0) (onsets nil)
         (manifest (obj "scenario" "clay-toe-profile" "status" "running" "complete" 'yason:false
           "config" cfg "particleCount" 0 "savedFrames" 0 "updates" 0 "timeS" 0d0 "nativeTimeS" 0d0
           "phase" "initialization" "equilibriumVerified" 'yason:false
           "geometry" "Upper7m at20deg/lower3m at40deg/H10/base8/crest24; geometric Saint-Jude-inspired comparison, NOT site reproduction"
           "trigger" "Gravity only, no notch/load/weakzone; same homogeneous prior-triaxial clay and positive quarter residual"
           "initialization" "Zero stress/kappa,2s gravity ramp; no geostatic equilibrium claim, no field reset or undrained switch"
           "apexConvention" "Explicit c0 HS gA=p volumetric apex extension, strict regular shear psi0"
           "damageDefinition" "D_phi=1-tan(phi)/tan(33.99deg),0..0.75; plastic kappa is separate, no strength loss before kappa.037"
           "historyFile" "history.csv" "particleFile" "material-state.csv" "dynamicVtkPattern" "vtk/particles_%04d.vtk"
           "scientificallyValidated" 'yason:false "landslideVerified" 'yason:false)))
    (ensure-directories-exist vtk)
    (labels ((progress (phase)
               (setf (gethash "phase" manifest) phase (gethash "savedFrames" manifest) saved
                     (gethash "updates" manifest) updates)
               (when sim (setf (gethash "timeS" manifest) (cl-mpm::sim-time sim)
                               (gethash "nativeTimeS" manifest) (cl-mpm::sim-time sim)))
               (write-json (merge-pathnames "manifest.json" out) manifest)))
      (let ((u::*proper-volume-domain* t) (*toe-failure-directory* out))
        (handler-case
          (progn
            (cl-mpm/utils:set-workers 1)
            (setf sim (build-toe-slope material cfg) ctx (capture-reference sim cfg)
                  (observation-context-failure-directory ctx) out
                  (observation-context-switch-native-time ctx) 0d0
                  (observation-context-switch-positions ctx) (map 'vector (lambda (p) (cl-mpm/utils:vector-copy (cl-mpm/particle:mp-position p))) (cl-mpm:sim-mps sim))
                  (observation-context-switch-kappa ctx) (map 'vector #'mc:particle-kappa (cl-mpm:sim-mps sim))
                  (observation-context-switch-work ctx) (map 'vector #'mc:particle-plastic-work (cl-mpm:sim-mps sim)))
            (setf (gethash "particleCount" manifest) (length (cl-mpm:sim-mps sim)))
            (unless (= (length (cl-mpm:sim-mps sim)) 15143) (error "Two-angle center-clip count must equal15143."))
            (configure-output sim)
            (cl-mpm/output:save-vtk-mesh (merge-pathnames "mesh.vtk" vtk) sim)
            (cl-mpm/scenario/urmi-damage40/output-streams:with-retained-output-file (history (merge-pathnames "history.csv" out))
              (cl-mpm/scenario/urmi-damage40/output-streams:with-retained-output-file (particles (merge-pathnames "material-state.csv" out))
                (write-headers history particles)
                (loop for frame below (value cfg "frames")
                      for target = (* (value cfg "duration") (/ frame (1- (value cfg "frames")))) do
                  (loop while (< (cl-mpm::sim-time sim) target) do
                    (when (>= updates (value cfg "maxDynamicUpdates")) (error "Toe-profile update budget reached."))
                    (let* ((time (cl-mpm::sim-time sim)) (ramp (value cfg "gravityRampDuration"))
                           (dt (min (stable-dt sim cfg) (- target time))))
                      (when (< time ramp) (setf dt (min dt (- ramp time))))
                      (unless (> (+ time dt) time) (error "Toe-profile timestep cannot advance."))
                      (setf (cl-mpm:sim-dt sim) dt
                            (cl-mpm:sim-gravity sim) (* (value cfg "gravity") (gs:ramp-factor (+ time dt) ramp))
                            (cl-mpm:sim-damping-factor sim) (if (< time ramp) .75d0 .02d0))
                      (cl-mpm:update-sim sim) (incf updates)
                      (when (zerop (mod updates 100)) (progress "gravity-ramp-or-motion"))))
                  (save-state sim ctx cfg (merge-pathnames (format nil "particles_~4,'0D.vtk" frame) vtk) frame 3 updates history particles)
                  (push (toe-onset sim ctx cfg) onsets)
                  (write-json (merge-pathnames "onset-history.json" out) (coerce (reverse onsets) 'vector))
                  (incf saved) (progress (if (< target 2d0) "gravity-ramp" "gravity-motion"))
                  (format t "~&[clay-toe-profile] frame~D/~D time=~,6F updates=~D~%" frame (1- (value cfg "frames")) (cl-mpm::sim-time sim) updates) (finish-output))))
            (setf (gethash "complete" manifest) t (gethash "status" manifest) "complete")
            (progress "finished") sim)
          (error (c) (setf (gethash "status" manifest) "failed" (gethash "error" manifest) (princ-to-string c))
            (progress (gethash "phase" manifest)) (error c)))))))

(in-package :cl-mpm/framework)
(defmethod compile-scenario ((scenario (eql :clay-toe-profile)) (case simulation))
  (let ((cfg (simulation-parameters case)))
    (unless (equalp cfg (cl-mpm/scenario/residual-clay-slope::toe-config))
      (error "Toe-profile recipe input differs from declared config."))
    (unless (eq (material-particle-class (simulation-material case))
                'cl-mpm/scenario/residual-clay-slope::particle-clay-toe)
      (error "Wrong toe-profile material class.")) cfg))
(defmethod execute-scenario ((scenario (eql :clay-toe-profile)) (case simulation) config directory)
  (declare (ignore scenario))
  (cl-mpm/scenario/residual-clay-slope::run-toe-profile (simulation-material case) config directory))
