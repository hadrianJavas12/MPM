;;;; Windows full-engine tests of the dedicated reference path. The coarse,
;;;; short run tests mechanics/integration; it does not reproduce the paper.
(in-package :cl-user)
(ql:quickload :cl-mpm-studio :silent t)
(in-package :cl-mpm-studio)

(defun reference-smoke-close (actual expected &optional (tolerance 1d-10))
  (assert (and (reference-finite-p actual)
               (<= (abs (- actual expected)) (* tolerance (max 1d0 (abs expected)))))
          () "Reference smoke mismatch: ~A vs ~A" actual expected))

(defun reference-smoke-output ()
  (let* ((args (cl-user::cl-mpm-script-args))
         (option (member "--output-dir" args :test #'equal)))
    (when option (assert (second option) () "--output-dir requires a directory"))
    (uiop:ensure-directory-pathname
     (cl-user::cl-mpm-path (if option (second option) "output/joss-reference-smoke/")))))

(defun reference-smoke-config ()
  (let ((config (load-config (asdf:system-relative-pathname "cl-mpm" "studio/reference/joss-bay-prose.json"))))
    (setf (gethash "meshSize" config) 1d0
          (gethash "mpsPerCell" config) 2
          (gethash "workers" config) 1
          (gethash "maxSteps" config) 2
          ;; Two recorded intervals can reach at most .02s, so .03s makes
          ;; frame-limit independent of the current numerical phase transition.
          (gethash "simulationTime" config) 0.03d0
          (gethash "accelerateInterval" config) 0.01d0
          (gethash "collapseInterval" config) 0.005d0
          ;; Explicitly coarser smoke convergence; the paper profile is 1e-4.
          (gethash "settleTolerance" config) 1d-2
          (gethash "settleMaxSteps" config) 20000)
    config))

(defun reference-smoke-statistics ()
  ;; Two synthetic physical nodes, with unequal mapped volumes, verify the
  ;; weighted quantities analytically rather than copying implementation logic.
  (let* ((sim (cl-mpm/setup::make-block 1d0 '(1 1) :sim-type 'joss-reference-sim))
         (nodes (cl-mpm/mesh::mesh-nodes (cl-mpm:sim-mesh sim))))
    (loop for i below (array-total-size nodes) do
      (setf (cl-mpm/mesh:node-active (row-major-aref nodes i)) nil))
    (loop for i from 0 below 2
          for mass in '(2d0 4d0) for volume in '(0.25d0 1d0)
          for velocity in '(2d0 1d0) for external in '(1d0 2d0)
          for internal in '(2d0 -2d0) for displacement in '(0.5d0 0.25d0) do
      (let ((node (row-major-aref nodes i)))
        (setf (cl-mpm/mesh:node-active node) t
              (cl-mpm/mesh:node-mass node) mass
              (cl-mpm/mesh::node-volume node) volume
              (cl-mpm/utils:varef (cl-mpm/mesh:node-velocity node) 0) velocity
              (cl-mpm/utils:varef (cl-mpm/mesh::node-external-force node) 0) external
              (cl-mpm/utils:varef (cl-mpm/mesh::node-internal-force node) 0) internal
              (cl-mpm/utils:varef (cl-mpm/mesh::node-displacment node) 0) displacement)))
    (cl-mpm::update-dynamic-stats sim)
    (reference-smoke-close (cl-mpm::sim-stats-energy sim) 3d0)
    (reference-smoke-close (cl-mpm::sim-stats-work sim) 0.625d0)
    (reference-smoke-close (cl-mpm::sim-stats-oobf sim) (/ 3d0 (sqrt 17d0)))
    (cl-mpm::update-dynamic-stats sim)
    (reference-smoke-close (cl-mpm::sim-stats-work sim) 1.25d0))
  (let ((config (reference-smoke-config)))
    (setf (gethash "meshSize" config) 0.5d0)
    (reference-smoke-close (reference-viscous-damping config 0.1d0)
                          (* 0.4d0 (/ pi 2d0) (sqrt (/ 1d9 1700d0))))
    (reference-smoke-close (reference-viscous-damping config 1d-4)
                          (* 4d-4 (/ pi 2d0) (sqrt (/ 1d9 1700d0))))))

(defun reference-smoke-dp-criterion (mp)
  ;; Uniaxial compression distinguishes author DP from tensile-equivalent MC.
  ;; The analytic DP value also catches a second conversion of the radian phi.
  (let* ((stress (cl-mpm/particle::mp-undamaged-stress mp))
         (original (loop for d below 6 collect (cl-mpm/utils:varef stress d)))
         (old-y (cl-mpm/particle::mp-damage-y-local mp))
         (old-inc (cl-mpm/particle::mp-local-damage-increment mp))
         (tangent (tan (deg->rad 50d0)))
         (expected (* 1d5 (/ (- 3d0 tangent) (+ 3d0 tangent)))))
    (unwind-protect
         (progn
           (dotimes (d 6) (setf (cl-mpm/utils:varef stress d) 0d0))
           (setf (cl-mpm/utils:varef stress 0) -1d5)
           (cl-mpm/damage::damage-model-calculate-y mp 1d-3)
           (reference-smoke-close (cl-mpm/particle::mp-damage-y-local mp) expected)
           (reference-smoke-close (cl-mpm/particle::mp-local-damage-increment mp) expected)
           ;; Hydrostatic compression has negative raw DP drive, clipped to zero.
           (dotimes (d 3) (setf (cl-mpm/utils:varef stress d) -1d5))
           (cl-mpm/damage::damage-model-calculate-y mp 1d-3)
           (reference-smoke-close (cl-mpm/particle::mp-damage-y-local mp) 0d0)
           (reference-smoke-close (cl-mpm/particle::mp-local-damage-increment mp) 0d0))
      (loop for value in original for d from 0 do
        (setf (cl-mpm/utils:varef stress d) value))
      (setf (cl-mpm/particle::mp-damage-y-local mp) old-y
            (cl-mpm/particle::mp-local-damage-increment mp) old-inc))))

(handler-case
    (let* ((config (reference-smoke-config))
           (output (reference-smoke-output)))
      (cl-mpm/utils:set-workers 1)
      (reference-smoke-statistics)
      (assert (eq (reference-next-state :accelerate 0d0 0d0 0.01d0) :accelerate))
      (assert (eq (reference-next-state :accelerate 0.011d0 0d0 0.01d0) :collapse))
      (assert (eq (reference-next-state :accelerate 0d0 0.011d0 0.01d0) :collapse))
      (assert (eq (reference-next-state :collapse 0.009d0 0.009d0 0.01d0) :accelerate))
      (assert (eq (reference-next-state :collapse 0.01d0 0d0 0.01d0) :collapse))
      (assert (eq (reference-next-state :accelerate 0.01d0 0.01d0 0.01d0) :accelerate))
      (when (equal (first (cl-user::cl-mpm-script-args)) "--unit-only")
        (format t "~&JOSS REFERENCE UNIT CHECKS PASSED (volume-weighted statistics, damping mapping and state thresholds)~%")
        (uiop:quit 0))
      (let* ((sim (make-joss-reference-sim config))
             (mp (aref (cl-mpm:sim-mps sim) 0))
             (dt (cl-mpm:sim-dt sim))
             (density (param config "density"))
             (height (param config "shelfHeight"))
             (upper (param config "upperVerticalHeight"))
             (lower (- height upper))
             (toe (* height (param config "shelfAspect")))
             (domain (* height (+ (param config "shelfAspect") (param config "runoutAspect"))))
             (slope (/ 1d0 (tan (deg->rad (param config "cliffSlope")))))
             (area (- (+ (* domain (param config "soilBoundary"))
                         (* toe height))
                      (* slope (+ (* 0.5d0 lower lower) (* lower upper)))
                      (/ (* 0.5d0 (expt (param config "notchDepth") 2)) (+ 1d0 slope)))))
        (assert (typep mp 'joss-reference-chalk))
        (reference-smoke-close (cl-mpm/particle::mp-c mp) 1965600d0)
        (reference-smoke-close (cl-mpm/particle::mp-phi mp) (deg->rad 50d0))
        (reference-smoke-close (cl-mpm/particle::mp-friction-angle mp) (deg->rad 50d0))
        (reference-smoke-close (cl-mpm/particle::mp-initiation-stress mp) 18926.452181842527d0)
        (reference-smoke-close (cl-mpm/particle::mp-ductility mp) 535.9975505618717d0)
        (reference-smoke-close (cl-mpm/particle::mp-delay-exponent mp) 2d0)
        (reference-smoke-close (cl-mpm/particle::mp-shear-residual-ratio mp) 0.51d0)
        (assert (not (cl-mpm/particle::mp-enable-plasticity mp)))
        (assert (not (cl-mpm/particle::mp-enable-damage mp)))
        (reference-smoke-dp-criterion mp)
        (assert (plusp (count 1 (cl-mpm:sim-mps sim) :key #'cl-mpm/particle::mp-index)))
        (assert (plusp (count 0 (cl-mpm:sim-mps sim) :key #'cl-mpm/particle::mp-index)))
        (loop for particle across (cl-mpm:sim-mps sim) do
          (assert (= (cl-mpm/particle::mp-index particle)
                     (if (<= (cl-mpm/utils:varef (cl-mpm/particle:mp-position particle) 1)
                             (param config "soilBoundary")) 1 0)))
          (assert (not (cl-mpm/particle::mp-enable-damage particle)))
          (assert (not (cl-mpm/particle::mp-enable-plasticity particle)))
          (assert (reference-solid-p config
                    (cl-mpm/utils:varef (cl-mpm/particle:mp-position particle) 0)
                    (cl-mpm/utils:varef (cl-mpm/particle:mp-position particle) 1))))
        (multiple-value-bind (mass damage-mass) (reference-summary sim)
          (declare (ignore damage-mass))
          (reference-smoke-close mass (* area density) 1d-2)
          (format t "~&Reference geometry: ~D MPs, mass ~,8F kg/m; analytic ~,8F kg/m~%"
                  (length (cl-mpm:sim-mps sim)) mass (* area density)))
        (setf (cl-mpm::sim-mass-scale sim) 1d4)
        (reference-smoke-close (cl-mpm/setup:estimate-elastic-dt sim :dt-scale 0.5d0) (* 100d0 dt))
        (setf (cl-mpm::sim-mass-scale sim) 1d0)
        (let ((initial-mass (reference-summary sim)))
          (cl-mpm:update-sim sim)
          (reference-smoke-close (reference-summary sim) initial-mass)
          (reference-check-finite sim)))
      ;; Bounded failure is part of the contract; never silently start a
      ;; fracture run from an unconverged initial stress field.
      (let ((failure-config (reference-smoke-config)) (rejected nil))
        (setf (gethash "settleMaxSteps" failure-config) 1
              (gethash "settleTolerance" failure-config) 1d-20)
        (handler-case
            (run-joss-reference failure-config
              (merge-pathnames "expected-failure/" output))
          (error (e)
            (assert (search "did not converge" (princ-to-string e)))
            (setf rejected t)))
        (assert rejected))
      (let* ((run-output (merge-pathnames "run/" output))
             (run-sim (run-joss-reference config run-output)))
        (loop for particle across (cl-mpm:sim-mps run-sim) do
          (let ((cliff (not (= (cl-mpm/particle::mp-index particle) 1))))
            (assert (eq (cl-mpm/particle::mp-enable-damage particle) (and cliff (param config "enableDamage"))))
            (assert (eq (cl-mpm/particle::mp-enable-plasticity particle) (and cliff (param config "enablePlasticity"))))
            (unless cliff (assert (= (cl-mpm/particle:mp-damage particle) 0d0)))))
        (let* ((metadata (read-json-file (merge-pathnames "reference-metadata.json" run-output)))
               (material (gethash "effectiveMaterial" metadata)))
          (assert (gethash "plottingCompleted" metadata))
          (assert (= (gethash "plottedFrames" metadata) 2))
          (assert (null (gethash "plottingError" metadata)))
          (assert (equal (gethash "statisticNorm" metadata) "aggregate-projected-L2"))
          (assert (equal (gethash "damageCriterion" metadata) "author-Joss-Drucker-Prager"))
          (assert (= (gethash "protectedBaseParticles" metadata)
                     (count 1 (cl-mpm:sim-mps run-sim) :key #'cl-mpm/particle::mp-index)))
          (assert (equal (gethash "termination" metadata) "frame-limit"))
          ;; JSON decimal parsing may round via a single float; the original
          ;; initialized material fields are already checked more strictly above.
          (reference-smoke-close (float (gethash "damageInitiationStress" material) 1d0) 18926.452181842527d0 1d-6)
          (reference-smoke-close (float (gethash "ductility" material) 1d0) 535.9975505618717d0 1d-6)
          (reference-smoke-close (float (gethash "settleDampingFactor" metadata) 1d0)
                                 (reference-viscous-damping config 0.1d0) 1d-6)
          (dotimes (frame 2)
            (assert (png-file-complete-p (numbered (merge-pathnames "frames/" run-output) "frame" (1+ frame) "png"))))))
      (format t "~&JOSS REFERENCE SMOKE PASSED (coarse h=1m, two short frames; not a paper benchmark)~%")
      (uiop:quit 0))
  (error (e)
    (format *error-output* "~&JOSS REFERENCE SMOKE FAILED: ~A~%" e)
    (uiop:quit 1)))
