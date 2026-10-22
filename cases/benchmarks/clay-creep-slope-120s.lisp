;;;; Duration-only extension of clay-creep-slope.lisp; explicit for frozen provenance.
;;;; Same physical material/geometry/loading/solver; 0.5s output cadence retained.
;;;; Motion is unconstrained by the historical 0.005m/s / 0.1m reference values.
(in-package :cl-mpm/framework)
(let ((parameters (make-hash-table :test 'equal)))
  (setf (gethash "duration" parameters) 120d0)
  (setf *simulation*
        (make-simulation
         :scenario :slope-creep :parameters parameters
         :material (make-material
                    :native :youngs-modulus 20d6 :poisson-ratio .25d0
                    :density (/ 20000d0 9.80665d0)
                    :particle-class 'cl-mpm/models/clay-creep:particle-clay-creep
                    :initargs (list :creep-law
                                    (cl-mpm/models/clay-creep:make-clay-creep-law
                                     :yield-peak (* (sqrt 3d0) 30d3)
                                     :yield-residual (* (sqrt 3d0) 6d3)
                                     :softening-kappa .01d0 :viscosity 5d7)))
         :geometry (make-geometry :slope :width 20d0 :height 10d0 :crest-length 10d0
                                  :slope 60d0 :base-height 5d0)
         :boundary (make-boundary :rollers)
         :loading (make-loading :gravity)
         :solver (make-solver :explicit :mesh-size 1d0 :mps-per-cell 2
                             :workers 1 :time-step-scale .2d0
                             :frames 241 :max-updates 150000))))
