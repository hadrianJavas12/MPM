;;;; Compatibility names for the independently loadable framework Joss backend.
(in-package :cl-mpm-studio)

;; Historical names identify the same classes and methods, without a copy
;; or a method installed on any original engine class.
(eval-when (:load-toplevel :execute)
  (dolist (name '(joss-reference-chalk joss-reference-sim joss-reference-aggregate-sim))
    (setf (find-class name)
          (find-class (find-symbol (symbol-name name) :cl-mpm/framework/cliff))))
  (dolist (name '(reference-cohesion reference-friction reference-dilation
                  reference-tensile reference-compression reference-shear
                  reference-finite-p reference-critical-damping reference-viscous-damping
                  reference-aggregate-statistics reference-energy-ratio
                  reference-next-state reference-zero-velocities
                  reference-face-x reference-solid-p reference-surface-height
                  reference-domain-corners reference-clip-geometry
                  make-joss-reference-sim reference-summary reference-effective-material
                  reference-check-finite reference-csv-number reference-write-row
                  run-joss-reference))
    (setf (fdefinition name)
          (fdefinition (find-symbol (symbol-name name) :cl-mpm/framework/cliff)))))
