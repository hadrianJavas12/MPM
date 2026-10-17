(in-package :cl-mpm/framework)
(let ((params (make-hash-table :test #'equal)))
  (setf (gethash "substeps" params) 40
        (gethash "elongatedShelfAspect" params) 4.0d0
        (gethash "runoutAspect" params) 4.5d0
        (gethash "settleSteps" params) 220
        (gethash "cflScale" params) 0.35d0)
  (setf *simulation*
        (make-simulation
         :scenario :cliff
         :parameters params
         :material (make-material :mc-hs
                                  :youngs-modulus 5.25d6
                                  :poisson-ratio 0.2d0
                                  :density 1917.07d0
                                  :evolution-law
                                  (cl-mpm/models/mc-evolution:make-urmi-evolution-law
                                   :variant :hs
                                   :prepeak-points '((0d0 15.0d0) (0.05d0 20.0d0))
                                   :prepeak-cohesion-points '((0d0 5000d0) (0.05d0 7000d0))
                                   :peak-kappa 0.05d0
                                   :residual-kappa 0.20d0
                                   :phi-peak-deg 20.0d0
                                   :phi-post-rupture-deg 16.0d0
                                   :phi-residual-deg 13.0d0
                                   :c-peak-pa 7000d0
                                   :c-post-rupture-pa 4000d0
                                   :c-residual-pa 2000d0
                                   :beta -5.0d0
                                   :postpeak-segments 8
                                   :psi 1.0d0
                                   :strain-assumption "Elongated Urmi-geometry long-duration cliff benchmark (Model HS Urmi Eq. 2 softening to c=2 kPa, phi=13 deg at kappa=0.20)"))
         :geometry (make-geometry :cliff
                                  :height 12d0
                                  :shelf-aspect 4.0d0
                                  :slope 72d0
                                  :base-height 4d0
                                  :notch-height 2.5d0
                                  :notch-depth 2.5d0)
         :boundary (make-boundary :rollers)
         :loading (make-loading :gravity)
         :solver (make-solver :explicit
                              :mesh-size 0.5d0
                              :mps-per-cell 2
                              :frames 80
                              :workers 12))))
