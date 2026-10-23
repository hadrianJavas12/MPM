;;;; Soil #2, Table 1 / Fig. 4: cohesion 30 -> 15 kPa over paper kps 0 -> .02.
(in-package :cl-mpm/models/wang2017)

(defun soil2-cohesion (kps)
  "Paper-coordinate cohesion in Pa. Pure evaluation, no particle/state mutation.
This is NOT a commitment to a reversal/irreversibility convention for a solver."
  (unless (handler-case
              (and (realp kps) (<= 0d0 kps most-positive-double-float))
            (arithmetic-error () nil))
    (error "Paper kps must be finite and nonnegative: ~S" kps))
  (if (>= kps .02d0) 15000d0
      (- 30000d0 (* 15000d0 (/ (float kps 1d0) .02d0)))))
