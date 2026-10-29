(let ((system "cl-mpm-framework/residual-clay-hs-apex"))
  (when (and (boundp 'cl-user::*native-snapshot-context*) cl-user::*native-snapshot-context*)
    (cl-user::snapshot-check-plan system))
  (ql:quickload system :silent t))
(in-package :cl-mpm/framework)
(let* ((cfg (read-parameters "studio/reference/residual-clay-slope-quarter.json"))
       (law (cl-mpm/scenario/residual-clay-slope::make-law cfg)))
  (setf (gethash "explicitHsApex" cfg) t)
  (setf *simulation*
    (make-simulation :scenario :residual-clay-slope-quarter :parameters cfg
      :material (make-material :native :youngs-modulus 20d6 :poisson-ratio .2d0 :density 2000d0
                  :particle-class 'cl-mpm/models/mc-hs-apex:particle-mc-hs-apex
                  :initargs (list :evolution-law law :enable-plasticity t))
      :geometry (make-geometry :slope :width (+ 24d0 (/ 10d0 (tan (* pi (/ 40d0 180d0)))))
                  :height 10d0 :crest-length 24d0 :slope 40d0 :base-height 8d0)
      :boundary (make-boundary :rollers) :loading (make-loading :gravity)
      :solver (make-solver :explicit :mesh-size .5d0 :mps-per-cell 2 :workers 1
                  :time-step-scale .2d0 :frames 41 :max-updates 80000 :damping .02d0))))
