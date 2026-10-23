;;;; NEGATIVE CLI fixture: intentionally inadmissible initial tensile strain.
;;;; Tests error retention only. This is NOT a Wang slope or physical benchmark.
(in-package :cl-mpm/framework)
(let ((parameters (make-hash-table :test 'equal)))
  (setf (gethash "substeps" parameters) 1)
  (setf *simulation*
        (make-simulation
         :scenario :cliff :parameters parameters
         :material
         (make-material
          :native :particle-class 'cl-mpm/models/mc-evolution:particle-mc-evolution
          :youngs-modulus 20d6 :poisson-ratio .25d0 :density 1800d0
          :initargs
          (list :strain (cl-mpm/utils:voigt-from-list '(.01d0 .01d0 .01d0 0d0 0d0 0d0))
                :evolution-law
                (cl-mpm/models/mc-evolution:make-evolution-law
                 :variant :perfect :points '((0d0 35d0)) :cohesion 30d3 :psi 0d0
                 :stress-measure :cauchy
                 :strain-assumption "Synthetic CLI retention fixture, intentionally inadmissible tension")))
         :geometry (make-geometry :cliff :height 10d0 :base-height 2d0)
         :boundary (make-boundary :rollers) :loading (make-loading :gravity)
         :solver (make-solver :explicit :mesh-size 2d0 :mps-per-cell 1
                              :workers 1 :frames 1))))
