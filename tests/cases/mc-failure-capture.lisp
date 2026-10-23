;;;; NEGATIVE CLI fixture: a test-only scenario with an inadmissible pure return.
;;;; Zero MPM steps. Tests propagation/JSON retention, NOT a Wang physical case.
(in-package :cl-mpm/framework)
(defmethod compile-scenario ((scenario (eql :test-mc-failure-capture)) (case simulation))
  (declare (ignore case)) (make-hash-table :test 'equal))
(defmethod execute-scenario ((scenario (eql :test-mc-failure-capture))
                            (case simulation) config directory)
  (declare (ignore case config directory))
  (cl-mpm/models/mc-evolution:project-principal
   #(40d3 40d3 40d3) 20d6 .25d0 1.0123456789012345d0
   (cl-mpm/models/mc-evolution:make-evolution-law
    :variant :perfect :points '((0d0 35d0)) :cohesion 10d3 :psi 0d0
    :stress-measure :cauchy :strain-assumption "Synthetic CLI failure; zero MPM steps")
   0d0))
(setf *simulation*
      (make-simulation
       :scenario :test-mc-failure-capture :material (make-material :elastic)
       :geometry (make-geometry :cliff) :boundary (make-boundary :rollers)
       :loading (make-loading :gravity) :solver (make-solver :explicit)))
