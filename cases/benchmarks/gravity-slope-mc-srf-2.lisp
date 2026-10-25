;;;; GL D1-inspired geometry adaptation; independent dynamic MC SSR trial.
;;;; Full Xie Figure7 polygon is not visually verified; no exact-reproduction claim.
(in-package :cl-mpm/framework)
(let* ((srf 2d0)
       (phi-deg (* (/ 180d0 pi) (atan (/ (tan (* 20d0 (/ pi 180d0))) srf))))
       (law (cl-mpm/models/mc-evolution:make-evolution-law
             :variant :perfect :points (list (list 0d0 phi-deg))
             :cohesion (/ 10000d0 srf) :psi 0d0 :stress-measure :cauchy
             :strain-assumption "Constant perfect-plastic MC; no paper softening coordinate fitted"))
       (parameters (make-hash-table :test 'equal)))
  (loop for (key value) on
        (list "domainWidth" 80d0 "domainHeight" 15d0 "duration" 6d0
              "gravityRampDuration" 2d0 "gravity" -9.80665d0
              "strengthReductionFactor" srf "referenceCohesionPa" 10000d0
              "referenceFrictionDeg" 20d0
              "geometryProvenance" "GL-D1-inspired adaptation; Xie Figure7 polygon not visually verified")
        by #'cddr do (setf (gethash key parameters) value))
  (setf *simulation*
        (make-simulation
         :scenario :gravity-slope :parameters parameters
         :material (make-material :native :youngs-modulus 100d6 :poisson-ratio .3d0
                    :density (/ 20000d0 9.80665d0)
                    :particle-class 'cl-mpm/models/mc-evolution:particle-mc-evolution
                    :initargs (list :evolution-law law))
         :geometry (make-geometry :slope :width 32d0 :height 10d0 :base-height 0d0
                                  :crest-length 12d0 :slope (* (/ 180d0 pi) (atan .5d0)))
         :boundary (make-boundary :rollers) :loading (make-loading :gravity)
         :solver (make-solver :explicit :mesh-size 1d0 :mps-per-cell 2 :workers 1
                             :time-step-scale .2d0 :frames 61 :max-updates 60000
                             :damping 0d0))))
