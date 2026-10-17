(in-package :cl-mpm/framework)
(setf *simulation*
      (make-simulation
       :scenario :triaxial
       :parameters (read-parameters "calibration/triaxial-demo.json")
       :material (make-material :mc-h
                                :youngs-modulus 20d6
                                :poisson-ratio 0.2d0
                                :density 2000d0
                                :evolution-law
                                (cl-mpm/models/mc-evolution:make-evolution-law
                                 :variant :h
                                 :points '((0d0 0d0)
                                           (0.0068d0 27.10d0)
                                           (0.037d0 33.99d0)
                                           (0.10d0 27.62d0)
                                           (0.20d0 16.34d0))
                                 :cohesion 0d0
                                 :psi 0d0
                                 :peak-kappa 0.037d0
                                 :strain-assumption "Residual soil triaxial kappa_eq table (Model H plateau after kappa=0.037)"))
       :geometry (make-geometry :cylinder :diameter 0.07d0 :height 0.14d0)
       :boundary (make-boundary :confinement :cell-pressure 200d3 :penalty-scale 10d0)
       :loading (make-loading :compression :target-strain 0.11d0 :duration 0.044d0 :ramp-duration 0.005d0)
       :solver (make-solver :explicit :mesh-size 0.01d0 :mps-per-cell 1 :frames 24
                            :time-step-scale 0.25d0 :damping 150d0 :workers 4)))
