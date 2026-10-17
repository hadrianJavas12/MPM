;;;; Two native updates with a distinct constitutive class in the same cliff recipe.
;;;; Integration evidence only; this small gravity case is not a calibrated cliff.
(in-package :cl-mpm/framework)
(let ((parameters (make-hash-table :test 'equal)))
  (setf (gethash "substeps" parameters) 2)
  (setf *simulation*
        (make-simulation
         :scenario :cliff
         :parameters parameters
         :material (make-material :native
                    :particle-class 'cl-mpm/particle::particle-mc
                    :youngs-modulus 5d6 :poisson-ratio 0.3d0 :density 1800d0
                    :initargs (list :phi (/ pi 6d0) :psi 0d0 :c 5000d0 :softening 0d0))
         :geometry (make-geometry :cliff :height 10d0 :base-height 2d0)
         :boundary (make-boundary :rollers)
         :loading (make-loading :gravity)
         :solver (make-solver :explicit :mesh-size 2d0 :mps-per-cell 1
                              :workers 1 :frames 1))))
