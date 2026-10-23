;;;; Wang et al. (2017), Section 2 / Table 1 Soil#1 / Figures 2 and 3.
;;;; Relief height is NOT dimensioned in Fig.2: 10 m is a provisional assumption.
;;;; Full physical-speed target: 0.1 m / 1e-4 m/s = 1000 s; no mass scaling.
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
                    :native :youngs-modulus 20d6 :poisson-ratio 0.25d0
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
         :loading (make-loading :prescribed-descent :velocity 1d-4
                                :target-displacement 0.1d0 :patch-start 7d0 :patch-length 3d0)
         :solver (make-solver :explicit :mesh-size 1d0 :mps-per-cell 2
                             :workers 1 :time-step-scale 0.2d0
                             :frames 51 :max-updates 5000000))))
