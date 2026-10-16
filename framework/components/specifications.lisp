;;;; Historical source-path compatibility; ASDF loads the new owner directly.
(in-package :cl-user)
(let ((root (merge-pathnames "../../" (uiop:pathname-directory-pathname *load-truename*))))
  (dolist (relative '("src/simulation/components/base.lisp" "materials/core/definition.lisp" "src/simulation/components/specifications.lisp"))
    (load (merge-pathnames relative root))))
