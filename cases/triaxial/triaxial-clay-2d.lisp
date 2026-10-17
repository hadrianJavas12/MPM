;;;; 70 x 140 mm plane-strain specimen; SI units, compression-positive fraction.
(in-package :cl-mpm/framework)
(setf *simulation*
      (make-simulation
       :scenario :triaxial
       :parameters (read-parameters "calibration/triaxial-2d.json")
       :material (make-material :von-mises :youngs-modulus 5d6 :poisson-ratio 0.49d0
                                :density 1800d0 :undrained-strength 25d3)
       :geometry (make-geometry :rectangle :width 0.07d0 :height 0.14d0)
       :boundary (make-boundary :confinement :cell-pressure 50d3)
       :loading (make-loading :compression :target-strain 0.10d0)
       :solver (make-solver :explicit)))
