;;;; Bounded public-CLI initiation check. Full collapse regression is separate.
;;;; Preserve accepted material/geometry/equilibrium/phase parameters; stop at 4 s.
(in-package :cl-mpm/framework)
(setf *simulation*
      (make-simulation
       :scenario :joss
       :parameters (read-parameters "studio/reference/joss-bay-accepted-collapse.json" :schema t)
       :material (make-material :joss)
       :geometry (make-geometry :joss)
       :boundary (make-boundary :rollers)
       :loading (make-loading :gravity)
       :solver (make-solver :staged :simulation-time 4d0 :frames 10)))
