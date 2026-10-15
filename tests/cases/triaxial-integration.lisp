;;;; Bounded public-CLI integration case. Full numerical regression is separate.
;;;; Same material/geometry/confinement as cases/triaxial-clay-2d.lisp;
;;;; shorten the requested loading program, without changing computed fields.
(in-package :cl-mpm/framework)
(setf *simulation*
      (make-simulation
       :scenario :triaxial
       :parameters (read-parameters "calibration/triaxial-2d.json")
       :material (make-material :von-mises :youngs-modulus 5d6 :poisson-ratio 0.49d0
                                :density 1800d0 :undrained-strength 25d3)
       :geometry (make-geometry :rectangle :width 0.07d0 :height 0.14d0)
       :boundary (make-boundary :confinement :cell-pressure 50d3)
       :loading (make-loading :compression :duration 0.0003d0 :ramp-duration 0.00005d0
                              :target-strain 0.0001d0)
       :solver (make-solver :explicit :frames 2 :max-updates 1000)))
