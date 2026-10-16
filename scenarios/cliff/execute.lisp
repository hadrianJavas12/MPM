(in-package :cl-mpm/framework)

(defmethod execute-scenario ((scenario (eql :cliff)) (case simulation) config directory)
  (let ((material (resolve-material (simulation-material case) config
                                   '((:youngs-modulus "E" 5d6) (:poisson-ratio "nu" 0.49d0)
                                     (:density "density" 1800d0)
                                     (:plasticity "enablePlasticity" t))))
        (filter (geometry-filter (simulation-geometry case))))
    (when filter (error "Generic cliff filter uses the native geometry callback API; this clipping predicate is for triaxial."))
    (cl-mpm/framework/cliff:run
     config directory :cliff-builder
     (lambda (config)
       (cl-mpm/framework/cliff:make-cliff-sim
        config :particle-factory (unless (eq (component-kind material) :chalk)
                                   (cliff-particle-factory material)))))))
