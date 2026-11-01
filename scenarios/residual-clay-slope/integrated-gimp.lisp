;;;; Opt-in exact box average of the linear grid basis, including large domains.
;;;; No engine shape function, particle domain, material or force is overwritten.
(in-package :cl-mpm/scenario/residual-clay-slope)

(defclass clay-integrated-gimp-sim (clay-adaptive-sim)
  ((ordinal :initform 0 :accessor integrated-ordinal)
   (trace :initform nil :accessor integrated-trace)
   (stages :initform nil :accessor integrated-stages)
   (cache-report :initform nil :accessor integrated-cache-report)))

(defun integrated-clay-config ()
  (let ((cfg (adaptive-clay-config)))
    (setf (gethash "integratedGimp" cfg) t) cfg))

(defun hat-primitive (x h)
  "Integral from -infinity to x of max(0,1-|x|/h)."
  (cond ((<= x (- h)) 0d0)
        ((< x 0d0) (/ (expt (+ x h) 2) (* 2d0 h)))
        ((< x h) (- (+ (* .5d0 h) x) (/ (* x x) (* 2d0 h))))
        (t h)))

(defun box-gimp (x l h)
  (unless (and (every #'gs::finite-p (list x l h)) (> l 0d0) (> h 0d0))
    (error "Invalid integrated GIMP coordinates/domain."))
  ;; Retain native arithmetic exactly in its small-domain validity region.
  (if (<= l (* .5d0 h)) (cl-mpm/shape-function::shape-gimp x l h)
      (/ (- (hat-primitive (+ x l) h) (hat-primitive (- x l) h)) (* 2d0 l))))

(defun box-gimp-gradient (x l h)
  (if (<= l (* .5d0 h)) (cl-mpm/shape-function::shape-gimp-dsvp x l h)
      (/ (- (max 0d0 (- 1d0 (/ (abs (+ x l)) h)))
            (max 0d0 (- 1d0 (/ (abs (- x l)) h)))) (* 2d0 l))))

(defun fill-integrated-cache (mesh mp)
  "Install native node-cache records; reset-grid preserves these node objects."
  (let* ((cache (cl-mpm/particle::mp-cached-nodes mp))
         (p (cl-mpm/particle:mp-position mp)) (d (cl-mpm/particle::mp-domain-size mp))
         (h (cl-mpm/mesh:mesh-resolution mesh))
         (x (component p 0)) (y (component p 1))
         (lx (* .5d0 (component d 0))) (ly (* .5d0 (component d 1))))
    (setf (fill-pointer cache) 0)
    (unless (and (every #'gs::finite-p (list x y lx ly)) (> lx 0d0) (> ly 0d0))
      (error "Invalid integrated GIMP particle domain/position."))
    (if (and (<= lx (* .5d0 h)) (<= ly (* .5d0 h)))
        (cl-mpm::create-node-cache mesh mp (lambda (&rest ignored) (declare (ignore ignored))))
        (loop for i from (max 0 (floor (- x lx) h))
              to (min (1- (array-dimension (cl-mpm/mesh::mesh-nodes mesh) 0)) (ceiling (+ x lx) h)) do
          (loop for j from (max 0 (floor (- y ly) h))
                to (min (1- (array-dimension (cl-mpm/mesh::mesh-nodes mesh) 1)) (ceiling (+ y ly) h)) do
            (let ((id (list i j 0)))
              (when (cl-mpm/mesh:in-bounds mesh id)
                (let* ((dx (- x (* i h))) (dy (- y (* j h)))
                       (wx (box-gimp dx lx h)) (wy (box-gimp dy ly h)) (w (* wx wy)))
                  (when (> w 0d0)
                    (let ((g (cl-mpm/utils::make-gradients
                              (* (box-gimp-gradient dx lx h) wy)
                              (* (box-gimp-gradient dy ly h) wx) 0d0)))
                      ;; Fbar is disabled for this scenario; do not use surrogate
                      ;; Fbar weights in a future enabled-Fbar case.
                      (vector-push-extend (cl-mpm/particle::make-node-cache
                        (cl-mpm/mesh:get-node mesh id) w g 0d0
                        (cl-mpm/utils::make-gradients 0d0 0d0 0d0)) cache)))))))))
    (values (loop for nc across cache sum (cl-mpm/particle::node-cache-weight nc))
            (or (> lx (* .5d0 h)) (> ly (* .5d0 h))))))

(defun integrated-mp-record (mp)
  (obj "id" (cl-mpm/particle::mp-unique-index mp)
       "position" (copy-seq (cl-mpm/utils:fast-storage (cl-mpm/particle:mp-position mp)))
       "velocity" (copy-seq (cl-mpm/utils:fast-storage (cl-mpm/particle:mp-velocity mp)))
       "F" (copy-seq (cl-mpm/utils:fast-storage (cl-mpm/particle:mp-deformation-gradient mp)))
       "domain" (copy-seq (cl-mpm/utils:fast-storage (cl-mpm/particle::mp-domain-size mp)))
       "J" (cl-mpm/fastmaths:det-3x3 (cl-mpm/particle:mp-deformation-gradient mp))
       "volume" (cl-mpm/particle:mp-volume mp) "mass" (cl-mpm/particle:mp-mass mp)
       "kappa" (mc:particle-kappa mp) "work" (mc:particle-plastic-work mp)))

(defun integrated-directory (sim)
  (toe-particle-failure-directory (aref (cl-mpm:sim-mps sim) 0)))

(defun save-integrated-trace (sim &optional failure)
  (let ((dir (integrated-directory sim)))
    (when dir
      (write-json (merge-pathnames (if failure "actual-step-failure.json" "step-trace.json") dir)
        (obj "schema" "cl-mpm.integrated-gimp.step-trace.v1"
             "scope" "Actual current and last10step diagnostics; no restart/rollback or constitutive trial"
             "stepOrdinal" (integrated-ordinal sim) "nativeTimeS" (cl-mpm::sim-time sim)
             "failure" (or failure 'yason:false)
             "adaptiveStep" (adaptive-step-record sim)
             "currentForceStages" (integrated-stages sim)
             "cache" (integrated-cache-report sim)
             "lastSteps" (coerce (reverse (integrated-trace sim)) 'vector))))))

(defun check-integrated-centers (sim stage)
  (let ((cfg (adaptive-config sim)))
    (loop for mp across (cl-mpm:sim-mps sim) do
      (let ((x (component (cl-mpm/particle:mp-position mp) 0))
            (y (component (cl-mpm/particle:mp-position mp) 1)))
        (unless (and (gs::finite-p x) (gs::finite-p y)
                     (<= 0d0 x (value cfg "domainWidth")) (<= 0d0 y (value cfg "domainHeight")))
          (save-integrated-trace sim (obj "stage" stage "reason" "Particle center outside grid/nonfinite"
                                         "particle" (integrated-mp-record mp)))
          (error "Integrated GIMP per-step center guard ID~D at ~S,~S; actual-step-failure.json retained."
                 (cl-mpm/particle::mp-unique-index mp) x y))))))

(defmethod cl-mpm:update-sim :around ((sim clay-integrated-gimp-sim))
  (setf (integrated-stages sim) nil)
  (check-integrated-centers sim "before-step")
  (let ((large 0) (sum-error 0d0))
    (loop for mp across (cl-mpm:sim-mps sim) do
      (multiple-value-bind (sum changed) (fill-integrated-cache (cl-mpm:sim-mesh sim) mp)
        (when changed (incf large)) (setf sum-error (max sum-error (abs (- sum 1d0))))
        (unless (> sum 0d0)
          (save-integrated-trace sim (obj "stage" "before-step-cache" "reason" "No positive grid support"
                                         "particle" (integrated-mp-record mp)))
          (error "Particle has no positive integrated GIMP grid support."))))
    (setf (integrated-cache-report sim) (obj "largeDomainParticles" large "maxWeightSumErrorOnFiniteGrid" sum-error)))
  (incf (integrated-ordinal sim))
  (handler-bind ((error (lambda (condition)
                   (ignore-errors (save-integrated-trace sim
                     (obj "stage" "native-step-error" "reason" (princ-to-string condition)))))))
    (call-next-method))
  (push (obj "stepOrdinal" (integrated-ordinal sim) "nativeTimeS" (cl-mpm::sim-time sim)
             "dtS" (cl-mpm:sim-dt sim) "forceStages" (integrated-stages sim)
             "particle7699" (integrated-mp-record (aref (cl-mpm:sim-mps sim) 7699)))
        (integrated-trace sim))
  (when (> (length (integrated-trace sim)) 10) (setf (integrated-trace sim) (subseq (integrated-trace sim) 0 10)))
  (check-integrated-centers sim "after-completed-native-step")
  (when (or (zerop (mod (integrated-ordinal sim) 100))
            (>= (cl-mpm::sim-time sim) (value (adaptive-config sim) "duration")))
    (save-integrated-trace sim)))

(defun force-stage-summary (sim &optional rank-by-force)
  (let ((maximum -1d0) (record nil) (speed 0d0))
    (cl-mpm::iterate-over-nodes-serial (cl-mpm:sim-mesh sim)
      (lambda (node)
        (when (cl-mpm/mesh:node-active node)
          (let* ((a (cl-mpm/fastmaths::mag (cl-mpm/mesh:node-acceleration node)))
                 (metric (if rank-by-force
                    (/ (sqrt (loop for i below 2 sum
                      (expt (+ (component (cl-mpm/mesh::node-internal-force node) i)
                               (component (cl-mpm/mesh::node-external-force node) i)) 2)))
                       (cl-mpm/mesh:node-mass node)) a)))
            (setf speed (max speed (cl-mpm/fastmaths::mag (cl-mpm/mesh:node-velocity node))))
            (when (> metric maximum)
              (setf maximum metric record (obj "mass" (cl-mpm/mesh:node-mass node)
                "position" (copy-seq (cl-mpm/utils:fast-storage (cl-mpm/mesh::node-position node)))
                "velocity" (copy-seq (cl-mpm/utils:fast-storage (cl-mpm/mesh:node-velocity node)))
                "acceleration" (copy-seq (cl-mpm/utils:fast-storage (cl-mpm/mesh:node-acceleration node)))
                "internalForce" (copy-seq (cl-mpm/utils:fast-storage (cl-mpm/mesh::node-internal-force node)))
                "externalForce" (copy-seq (cl-mpm/utils:fast-storage (cl-mpm/mesh::node-external-force node))))))))))
    (obj "maxNodalSpeed" speed "selectionMetric" (if rank-by-force "rawForceOverMass" "actualAcceleration")
         "selectionMaximum" maximum "selectedNode" record)))

(defmethod cl-mpm::update-node-forces :around ((sim clay-integrated-gimp-sim))
  (let ((before (force-stage-summary sim t)))
    (call-next-method)
    (setf (integrated-stages sim) (obj "beforeForces" before "afterForces" (force-stage-summary sim)))))

(in-package :cl-mpm/framework)
(defmethod compile-scenario ((scenario (eql :clay-single-slope60-integrated)) (case simulation))
  (let ((cfg (simulation-parameters case)))
    (unless (equalp cfg (cl-mpm/scenario/residual-clay-slope::integrated-clay-config))
      (error "Integrated GIMP60degree recipe differs from declared inputs.")) cfg))
(defmethod execute-scenario ((scenario (eql :clay-single-slope60-integrated)) (case simulation) cfg directory)
  (declare (ignore scenario))
  (cl-mpm/scenario/residual-clay-slope::run-toe-profile (simulation-material case) cfg directory))
