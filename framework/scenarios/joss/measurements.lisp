;;;; Temporary historical source-path compatibility; actual owners are outside framework.
(in-package :cl-user)
(let ((root (merge-pathnames "../../../"
              (uiop:pathname-directory-pathname *load-truename*))))
  (dolist (relative '("scenarios/joss/measurements.lisp" "materials/diagnostics/chalk-reference.lisp" "scenarios/joss/validation.lisp"))
    (load (merge-pathnames relative root))))
