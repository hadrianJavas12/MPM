(in-package :cl-mpm/framework)
(let ((params (make-hash-table :test #'equal)))
  (setf (gethash "substeps" params) 25)
  (setf *simulation*
        (make-simulation
         :scenario :cliff
         :parameters params
         :material (make-material :mc-h
                                  :youngs-modulus 5.25d6
                                  :poisson-ratio 0.2d0
                                  :density 1917.07d0
                                  :evolution-law
                                  (cl-mpm/models/mc-evolution:make-evolution-law
                                   :variant :h
                                   :points '((0d0 15.0d0)
                                             (0.05d0 20.0d0)
                                             (0.20d0 13.0d0))
                                   :cohesion-points '((0d0 5000d0)
                                                      (0.05d0 7000d0)
                                                      (0.20d0 2000d0))
                                   :psi 1.0d0
                                   :peak-kappa 0.05d0
                                   :strain-assumption "Zhan et al. (2012) cliff benchmark (Model H plateau at c=7 kPa, phi=20 deg after kappa=0.05)"))
         :geometry (make-geometry :cliff
                                  :height 12d0
                                  :shelf-aspect 1.5d0
                                  :slope 72d0
                                  :base-height 4d0
                                  :notch-height 2.5d0
                                  :notch-depth 2.5d0)
         :boundary (make-boundary :rollers)
         :loading (make-loading :gravity)
         :solver (make-solver :explicit
                              :mesh-size 0.5d0
                              :mps-per-cell 2
                              :frames 35
                              :workers 4))))
