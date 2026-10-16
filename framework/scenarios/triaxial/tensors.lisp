;;;; Temporary historical source-path compatibility; actual owners are outside framework.
(in-package :cl-user)
(let ((root (merge-pathnames "../../../"
              (uiop:pathname-directory-pathname *load-truename*))))
  (dolist (relative '("src/numerics/legacy-tensors.lisp" "src/measurements/legacy-particle.lisp" "scenarios/triaxial/stress-measures.lisp" "src/measurements/legacy-stress.lisp"))
    (load (merge-pathnames relative root))))
