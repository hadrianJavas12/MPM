;;;; Historical source-path compatibility; ASDF loads the new owners directly.
(in-package :cl-user)
(let ((root (merge-pathnames "../../" (uiop:pathname-directory-pathname *load-truename*))))
  (dolist (relative '("materials/core/diagnostics-interface.lisp" "materials/diagnostics/native.lisp" "src/measurements/material-output.lisp"))
    (load (merge-pathnames relative root))))
