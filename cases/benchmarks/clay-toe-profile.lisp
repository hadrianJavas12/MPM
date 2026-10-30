(let ((system "cl-mpm-framework/clay-toe-profile"))
  (when (and (boundp 'cl-user::*native-snapshot-context*) cl-user::*native-snapshot-context*)
    (cl-user::snapshot-check-plan system))
  (ql:quickload system :silent t))
(in-package :cl-mpm/framework)
(let* ((cfg (cl-mpm/scenario/residual-clay-slope::toe-config))
       (law (cl-mpm/scenario/residual-clay-slope::make-law cfg)))
  (setf *simulation*
    (make-simulation :scenario :clay-toe-profile :parameters cfg
      :material (make-material :native :youngs-modulus 20d6 :poisson-ratio .2d0 :density 2000d0
                  :particle-class 'cl-mpm/scenario/residual-clay-slope::particle-clay-toe
                  :initargs (list :evolution-law law :enable-plasticity t))
      :geometry (make-geometry :slope :height 10d0 :crest-length 24d0 :slope 20d0 :base-height 8d0)
      :boundary (make-boundary :rollers) :loading (make-loading :gravity)
      :solver (make-solver :explicit :mesh-size .5d0 :mps-per-cell 2 :workers 1
                  :time-step-scale .2d0 :frames 17 :max-updates 80000 :damping .02d0))))
