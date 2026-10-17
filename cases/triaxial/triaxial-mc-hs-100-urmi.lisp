(in-package :cl-mpm/framework)
(setf *simulation*
      (make-simulation
       :scenario :triaxial
       :parameters (read-parameters "calibration/triaxial-demo.json")
       :material (make-material :mc-hs
                                :youngs-modulus 20d6
                                :poisson-ratio 0.2d0
                                :density 2000d0
                                :evolution-law
                                (cl-mpm/models/mc-evolution:make-urmi-evolution-law
                                 :variant :hs
                                 :prepeak-points '((0d0 0d0) (0.0068d0 27.10d0) (0.037d0 33.99d0))
                                 :peak-kappa 0.037d0
                                 :residual-kappa 0.20d0
                                 :phi-peak-deg 33.99d0
                                 :phi-post-rupture-deg 27.62d0
                                 :phi-residual-deg 16.34d0
                                 :c-peak-pa 0d0
                                 :beta -25d0
                                 :postpeak-segments 8
                                 :strain-assumption "Urmi et al. (2024) Eq. 2 exponential-linear softening on Residual Soil"))
       :geometry (make-geometry :cylinder :diameter 0.07d0 :height 0.14d0)
       :boundary (make-boundary :confinement :cell-pressure 100d3 :penalty-scale 10d0)
       :loading (make-loading :compression :target-strain 0.11d0 :duration 0.044d0 :ramp-duration 0.005d0)
       :solver (make-solver :explicit :mesh-size 0.01d0 :mps-per-cell 1 :frames 24
                            :time-step-scale 0.25d0 :damping 150d0 :workers 4)))
