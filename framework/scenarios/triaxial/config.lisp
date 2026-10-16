;;;; Temporary historical source-path compatibility; actual owners are outside framework.
(in-package :cl-user)
(let ((root (merge-pathnames "../../../"
              (uiop:pathname-directory-pathname *load-truename*))))
  (dolist (relative '("src/simulation/config/legacy-triaxial-values.lisp" "scenarios/triaxial/config.lisp" "src/output/legacy-triaxial-json.lisp" "materials/adapters/diagnostics-call.lisp"))
    (load (merge-pathnames relative root))))
