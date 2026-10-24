;;;; Same 100 mm input; explicit residual-plateau-only signed-history scope.
;;;; Same rate/material/geometry/solver; extend travel to 100 mm (10 physical s).
(in-package :cl-mpm/framework)
(let ((parameters (make-hash-table :test 'equal)))
  (setf (gethash "settleMaxUpdates" parameters) 30000
        (gethash "settleMinUpdates" parameters) 1000
        (gethash "settleTolerance" parameters) 1d-3
        (gethash "settleHoldChecks" parameters) 5
        (gethash "penaltyScale" parameters) 20d0)
  (setf *simulation*
        (make-simulation
         :scenario :slope-descent :parameters parameters
         :material (make-material
                    :native :youngs-modulus 20d6 :poisson-ratio .25d0
                    :density (/ 20000d0 9.80665d0)
                    :particle-class 'cl-mpm/models/wang2017-apex:particle-wang2017-soil2-apex-residual
                    :initargs (list :evolution-law
                                    (cl-mpm/models/wang2017-apex:make-soil2-apex-residual-law)))
         :geometry (make-geometry :slope :width 20d0 :height 10d0
                                  :crest-length 10d0 :slope 60d0 :base-height 5d0)
         :boundary (make-boundary :rollers)
         :loading (make-loading :prescribed-descent :velocity .01d0
                                :target-displacement .10d0 :patch-start 7d0 :patch-length 3d0)
         :solver (make-solver :explicit :mesh-size 1d0 :mps-per-cell 2
                             :workers 1 :time-step-scale .2d0
                             :frames 101 :max-updates 45000))))
