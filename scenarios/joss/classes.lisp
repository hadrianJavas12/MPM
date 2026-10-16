;;;; Dedicated reference simulation classes.
;;;; Extracted without changing the existing numerical expressions.
(in-package :cl-mpm/framework/cliff)

(defclass joss-reference-sim (cl-mpm/damage::mpm-sim-damage) ())

(defclass joss-reference-aggregate-sim
    (joss-reference-sim cl-mpm/aggregate::mpm-sim-aggregated) ()
  (:documentation "Reference-only cut-cell stabilization through the author's aggregate solver."))
