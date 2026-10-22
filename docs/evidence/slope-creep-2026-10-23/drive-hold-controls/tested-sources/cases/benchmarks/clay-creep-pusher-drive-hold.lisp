;;;; Loading experiment: 0.02m/s to 0.1m travel, then stationary driver to 10s.
;;;; Soil motion remains free; same assumed material/geometry as previous pilots.
(in-package :cl-mpm/framework)
(let ((parameters (make-hash-table :test 'equal)))
  (setf (gethash "duration" parameters) 10d0)
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
         :loading (make-loading :crest-pusher :velocity .02d0 :travel .1d0
                                :patch-start 7d0 :patch-length 3d0 :penalty-scale 5d0)
         :solver (make-solver :explicit :mesh-size 1d0 :mps-per-cell 2
                             :workers 1 :time-step-scale .2d0
                             :frames 101 :max-updates 30000))))
