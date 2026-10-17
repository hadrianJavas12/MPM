;;;; Retained accepted fresh-start recipe; explicit staged solver and protected base.
(in-package :cl-mpm/framework)
(setf *simulation*
      (make-simulation
       :scenario :joss
       :parameters (read-parameters "studio/reference/joss-bay-accepted-collapse.json" :schema t)
       :material (make-material :joss)
       :geometry (make-geometry :joss)
       :boundary (make-boundary :rollers)
       :loading (make-loading :gravity)
       :solver (make-solver :staged)))
