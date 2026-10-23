;;;; Controlled rate comparison to fast-005; no material/apex convention change.
;;;; 0.002 m/s is 20x paper, not a reference-speed reproduction. Relief10m assumed.
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
                    :particle-class 'cl-mpm/models/mc-evolution:particle-mc-evolution
                    :initargs
                    (list :evolution-law
                          (cl-mpm/models/mc-evolution:make-evolution-law
                           :variant :perfect :points '((0d0 35d0))
                           :cohesion 30d3 :psi 0d0 :stress-measure :cauchy
                           :strain-assumption "Wang2017 Table1 Soil1: constant strength; no evolution coordinate fitted")))
         :geometry (make-geometry :slope :width 20d0 :height 10d0
                                  :crest-length 10d0 :slope 60d0 :base-height 5d0)
         :boundary (make-boundary :rollers)
         :loading (make-loading :prescribed-descent :velocity 2d-3
                                :target-displacement .1d0 :patch-start 7d0 :patch-length 3d0)
         :solver (make-solver :explicit :mesh-size 1d0 :mps-per-cell 2
                             :workers 1 :time-step-scale .2d0
                             ;; Same saved cadence .2s; computational cap scales with duration.
                             :frames 251 :max-updates 375000))))
