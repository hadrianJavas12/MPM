(let ((system "cl-mpm-framework/residual-clay-slope"))
  (when (and (boundp 'cl-user::*native-snapshot-context*) cl-user::*native-snapshot-context*)
    (cl-user::snapshot-check-plan system))
  (ql:quickload system :silent t))
(in-package :cl-mpm/framework)
(let ((cfg (read-parameters "studio/reference/residual-clay-slope-quarter.json")))
  (setf *simulation*
    (make-simulation :scenario :residual-clay-slope-quarter :parameters cfg
      :material (make-material :mc-hs :youngs-modulus 20d6 :poisson-ratio .2d0 :density 2000d0
                  :evolution-law (cl-mpm/scenario/residual-clay-slope::make-law cfg))
      :geometry (make-geometry :slope :width (+ 24d0 (/ 10d0 (tan (* pi (/ 40d0 180d0)))))
                  :height 10d0 :crest-length 24d0 :slope 40d0 :base-height 8d0)
      :boundary (make-boundary :rollers) :loading (make-loading :gravity)
      :solver (make-solver :explicit :mesh-size .5d0 :mps-per-cell 2 :workers 1
                  :time-step-scale .2d0 :frames 41 :max-updates 80000 :damping .02d0))))
