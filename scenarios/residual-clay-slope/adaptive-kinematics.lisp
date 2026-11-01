;;;; Explicit scenario-owned time integration policy. Original USF methods unchanged.
(in-package :cl-mpm/scenario/residual-clay-slope)

(defclass clay-adaptive-sim (u::urmi-proper-sim)
  ((config :accessor adaptive-config)
   (pending :initform nil :accessor adaptive-pending)
   (record :initform nil :accessor adaptive-step-record)
   (limited-steps :initform 0 :accessor adaptive-limited-steps)))

(defun adaptive-clay-config ()
  (let ((cfg (single-slope-config 60d0)))
    (setf (gethash "adaptiveKinematics" cfg) t
          (gethash "maximumGradientIncrement" cfg) .1d0)
    cfg))

(defun gradient-infinity-norm (matrix)
  (loop for i below 2 maximize
    (loop for j below 2 sum (abs (magicl:tref matrix i j)))))

(defun kinematic-dt-bound (requested elastic h cfl speed rate limit)
  ;; ||dt L||_inf < 1 makes I+dt L nonsingular, connected to I with positive det.
  ;; c = CFL*h/elastic preserves the existing elastic bound at zero speed.
  (unless (every (lambda (x) (and (gs::finite-p x) (> x 0d0)))
                 (list requested elastic h cfl limit))
    (error "Invalid adaptive step inputs."))
  (unless (and (<= limit .5d0) (gs::finite-p speed) (>= speed 0d0)
               (gs::finite-p rate) (>= rate 0d0))
    (error "Invalid adaptive speed/gradient bound."))
  (min requested (/ (* cfl h) (+ (/ (* cfl h) elastic) speed))
       (if (> rate 0d0) (/ limit rate) requested)))

(defmethod cl-mpm:update-sim :around ((sim clay-adaptive-sim))
  (unless (and (not (cl-mpm::sim-enable-fbar sim))
               (= (cl-mpm/mesh:mesh-nd (cl-mpm:sim-mesh sim)) 2))
    (error "Adaptive clay policy requires 2D USF without Fbar."))
  (setf (adaptive-pending sim) t)
  (unwind-protect (call-next-method) (setf (adaptive-pending sim) nil)))

(defmethod cl-mpm::update-nodes :around ((sim clay-adaptive-sim))
  ;; USF first call: velocities mapped, mass filtered and essential BC applied;
  ;; no constitutive/history/position update yet. Second call uses the SAME dt.
  (when (adaptive-pending sim)
    (let* ((mesh (cl-mpm:sim-mesh sim)) (cfg (adaptive-config sim))
           (requested (cl-mpm:sim-dt sim)) (elastic (stable-dt sim cfg))
           (rate 0d0) (speed 0d0) (limiting-id -1))
      (cl-mpm::iterate-over-nodes-serial mesh
        (lambda (node)
          (when (cl-mpm/mesh:node-active node)
            (setf speed (max speed (loop for i below 2 maximize
               (abs (component (cl-mpm/mesh:node-velocity node) i))))))))
      ;; Scratch stretch tensors only; the unchanged stress method recomputes
      ;; them from nodal displacements after the selected dt is applied.
      (loop for mp across (cl-mpm:sim-mps sim) do
        (cl-mpm::calculate-strain-rate mesh mp 1d0 nil)
        (let ((norm (gradient-infinity-norm (cl-mpm/particle::mp-stretch-tensor mp))))
          (unless (gs::finite-p norm) (error "Nonfinite current grid velocity gradient."))
          (when (> norm rate) (setf rate norm limiting-id (cl-mpm/particle::mp-unique-index mp)))))
      (let* ((dt (kinematic-dt-bound requested elastic (value cfg "meshSize")
                   (value cfg "timeStepScale") speed rate (value cfg "maximumGradientIncrement")))
             (time (cl-mpm::sim-time sim)))
        (unless (> (+ time dt) time) (error "Adaptive timestep cannot advance native time."))
        (when (< dt requested) (incf (adaptive-limited-steps sim)))
        (setf (cl-mpm:sim-dt sim) dt
              (cl-mpm:sim-gravity sim) (* (value cfg "gravity")
                (gs:ramp-factor (+ time dt) (value cfg "gravityRampDuration")))
              (adaptive-step-record sim)
              (obj "requestedDtS" requested "selectedDtS" dt "elasticDtS" elastic
                   "maxNodalSpeedInfinityMPerS" speed "maxGradientInfinityPerS" rate
                   "gradientIncrementBound" (* dt rate) "limitingParticleId" limiting-id
                   "limitedSteps" (adaptive-limited-steps sim)))
        (setf (adaptive-pending sim) nil))))
  (call-next-method))

(in-package :cl-mpm/framework)
(defmethod compile-scenario ((scenario (eql :clay-single-slope60-adaptive)) (case simulation))
  (let ((cfg (simulation-parameters case)))
    (unless (equalp cfg (cl-mpm/scenario/residual-clay-slope::adaptive-clay-config))
      (error "Adaptive60degree recipe differs from declared inputs.")) cfg))
(defmethod execute-scenario ((scenario (eql :clay-single-slope60-adaptive)) (case simulation) cfg directory)
  (declare (ignore scenario))
  (cl-mpm/scenario/residual-clay-slope::run-toe-profile (simulation-material case) cfg directory))
