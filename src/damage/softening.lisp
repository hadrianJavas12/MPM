;;;; Historical source-path compatibility; ASDF loads owner files directly.
(in-package :cl-user)
(let ((root (merge-pathnames "../../" (uiop:pathname-directory-pathname *load-truename*))))
  (dolist (relative '("materials/models/damage/evolution/responses.lisp" "materials/models/concrete/evolution/softening.lisp" "materials/models/chalk/evolution/softening.lisp"))
    (load (merge-pathnames relative root))))
