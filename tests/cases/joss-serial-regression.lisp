;;;; Full fresh-start control for numerical reproducibility.
;;;; Same accepted physics and staged loading; only the worker count is one.
;;;; Set OPENBLAS_NUM_THREADS=1 and OMP_NUM_THREADS=1 before starting SBCL.
(in-package :cl-mpm/framework)
(setf *simulation*
      (make-simulation
       :scenario :joss
       :parameters (read-parameters "studio/reference/joss-bay-accepted-collapse.json" :schema t)
       :material (make-material :joss)
       :geometry (make-geometry :joss)
       :boundary (make-boundary :rollers)
       :loading (make-loading :gravity)
       :solver (make-solver :staged :workers 1)))
