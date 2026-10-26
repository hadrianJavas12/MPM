;;;; Fresh 4s equilibrium/activation smoke, not a continuation of the full run.
(let ((system "cl-mpm-framework/damage-slope40"))
  (when (and (boundp 'cl-user::*native-snapshot-context*) cl-user::*native-snapshot-context*)
    (cl-user::snapshot-check-plan system))
  (ql:quickload system :silent t))

(in-package :cl-mpm/framework)
(setf *simulation*
      (damage-slope40-smoke-case
       (make-simulation
        :scenario :damage-slope40
        :parameters (read-parameters "studio/reference/damage-slope40.json")
        :material (make-material :joss)
        :geometry (make-geometry :joss :height 10d0 :shelf-aspect 2.39175359259421d0
                                 :slope 40d0 :base-height 1d0 :notch-height 0d0 :notch-depth 0d0)
        :boundary (make-boundary :rollers) :loading (make-loading :gravity)
        :solver (make-solver :staged :mesh-size .5d0 :mps-per-cell 2 :workers 1
                            :time-step-scale .5d0 :simulation-time 60d0 :frames 1500))))
