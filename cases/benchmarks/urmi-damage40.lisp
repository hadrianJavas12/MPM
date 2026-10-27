;;;; Optional owned unnotched soil MC case; neither Joss chalk nor literal Urmi calibration.
(let ((system "cl-mpm-framework/urmi-damage40"))
  (when (and (boundp 'cl-user::*native-snapshot-context*) cl-user::*native-snapshot-context*)
    (cl-user::snapshot-check-plan system))
  (ql:quickload system :silent t))
(in-package :cl-mpm/framework)
(setf *simulation* (make-simulation :scenario :urmi-damage40
  :parameters (read-parameters "studio/reference/urmi-damage40.json")
  :material (make-material :native :youngs-modulus 10773000d0 :poisson-ratio .33d0
    :density (/ 17000d0 9.80665d0) :particle-class 'cl-mpm/models/mc-evolution:particle-mc-evolution
    :initargs (list :evolution-law (cl-mpm/scenario/urmi-damage40::drained-law)))
  :geometry (make-geometry :slope :width (+ 12d0 (/ 10d0 (tan (* pi (/ 40d0 180d0)))))
    :height 10d0 :crest-length 12d0 :slope 40d0 :base-height 4d0)
  :boundary (make-boundary :rollers) :loading (make-loading :gravity)
  :solver (make-solver :explicit :mesh-size .5d0 :mps-per-cell 2 :workers 1
    :time-step-scale .2d0 :frames 301 :max-updates 200000 :damping 0d0)))
