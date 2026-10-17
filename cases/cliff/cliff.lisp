(in-package :cl-mpm/framework)
(setf *simulation*
      (make-simulation
       :scenario :cliff
       :material (make-material :chalk)
       :geometry (make-geometry :cliff :height 10d0 :base-height 2d0)
       :boundary (make-boundary :rollers)
       :loading (make-loading :gravity)
       :solver (make-solver :explicit :mesh-size 2d0 :mps-per-cell 1 :frames 3 :workers 1)))
