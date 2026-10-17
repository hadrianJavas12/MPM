;;;; Bounded serial initiation check; not a full collapse/run-out benchmark.
;;;; Accepted physics/equilibrium/stages; explicit stop at 4 physical seconds.
(in-package :cl-mpm/framework)
(setf *simulation*
      (make-simulation
       :scenario :joss
       :parameters (read-parameters "studio/reference/joss-bay-accepted-collapse.json" :schema t)
       :material (make-material :joss)
       :geometry (make-geometry :joss)
       :boundary (make-boundary :rollers)
       :loading (make-loading :gravity)
       :solver (make-solver :staged :workers 1 :simulation-time 4d0 :frames 10)))
