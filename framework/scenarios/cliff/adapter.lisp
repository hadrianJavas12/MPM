;;;; Public composition of the retained cliff/Joss recipes; no UI dependency.
(in-package :cl-mpm/framework)

(defun cliff-configuration (case joss-p)
  (let* ((config (cl-mpm/framework/config:load-config))
         (material (simulation-material case)) (geometry (simulation-geometry case))
         (solver (simulation-solver case)) (boundary (simulation-boundary case)))
    (maphash (lambda (key value) (setf (gethash key config) value))
             (simulation-parameters case))
    (check-kind material (if joss-p '(:joss) '(:chalk :von-mises :elastic :native)))
    (check-kind geometry (if joss-p '(:joss) '(:cliff)))
    (check-kind boundary '(:rollers))
    (check-kind (simulation-loading case) '(:gravity))
    (check-kind solver (if joss-p '(:staged) '(:explicit)))
    (when (and joss-p (geometry-filter geometry))
      (error "The Joss reference recipe requires its dedicated clipping geometry."))
    (overlay config material '((:youngs-modulus "E") (:poisson-ratio "nu") (:density "density")))
    (overlay config geometry '((:height "shelfHeight") (:shelf-aspect "shelfAspect")
                               (:slope "cliffSlope") (:base-height "soilBoundary")
                               (:notch-height "notchHeight") (:notch-depth "notchDepth")))
    (overlay config solver '((:mesh-size "meshSize") (:mps-per-cell "mpsPerCell")
                             (:workers "workers") (:frames "maxSteps")
                             (:time-step-scale "timeStepScale") (:simulation-time "simulationTime")))
    (unless (member (component-kind material) '(:chalk :joss))
      (setf (gethash "enableDamage" config) nil
            (gethash "enablePlasticity" config) (not (eq (component-kind material) :elastic)))
      ;; Keep numerical metadata consistent with the native material factory.
      (setf (gethash "E" config) (option material :youngs-modulus 5d6)
            (gethash "nu" config) (option material :poisson-ratio 0.49d0)
            (gethash "density" config) (option material :density 1800d0)))
    (setf (gethash "scenario" config) (if joss-p "joss-bay" "cliff")
          (gethash "constitutiveModel" config) "chalk")
    ;; Same canonical coercion/ranges as the old native launcher.
    (maphash (lambda (key spec)
               (let ((value (gethash key config)))
                 (when (keywordp value) (setf value (string-downcase value)))
                 (setf (gethash key config) (cl-mpm/framework/config:coerce-param spec value))))
             (cl-mpm/framework/config:schema))
    config))

(defmethod compile-scenario ((scenario (eql :cliff)) (case simulation))
  (cliff-configuration case nil))
(defmethod compile-scenario ((scenario (eql :joss)) (case simulation))
  (cliff-configuration case t))

(defmethod execute-scenario ((scenario (eql :joss)) (case simulation) config directory)
  (declare (ignore case))
  (cl-mpm/framework/cliff:run-joss-reference config directory))

(defun cliff-particle-factory (material)
  (lambda (config block-size h)
    (let* ((counts (mapcar (lambda (s) (max 1 (round (* s (gethash "mpsPerCell" config)) h))) block-size))
           (args (append (material-particle-initargs material)
                         (list :gravity -9.8d0 :gravity-axis
                               (cl-mpm/utils:vector-from-list '(0d0 1d0 0d0))))))
      (cl-mpm/setup::make-mps-from-list
       (apply #'cl-mpm/setup::make-block-mps-list '(0d0 0d0) block-size counts
              (option material :density 1800d0) (material-particle-class material) args)))))

(defmethod execute-scenario ((scenario (eql :cliff)) (case simulation) config directory)
  (let ((material (simulation-material case)) (filter (geometry-filter (simulation-geometry case))))
    (when filter (error "Generic cliff filter uses the native geometry callback API; this clipping predicate is for triaxial."))
    (cl-mpm/framework/cliff:run
     config directory :cliff-builder
     (lambda (config)
       (cl-mpm/framework/cliff:make-cliff-sim
        config :particle-factory (unless (eq (component-kind material) :chalk)
                                   (cliff-particle-factory material)))))))
