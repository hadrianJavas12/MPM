;;;; Historical source-path compatibility; ASDF loads owner files directly.
(in-package :cl-user)
(let ((root (merge-pathnames "../../" (uiop:pathname-directory-pathname *load-truename*))))
  (dolist (relative '("materials/models/damage/evolution/delayed-rate.lisp" "src/numerics/integration/delayed-steppers.lisp"))
    (load (merge-pathnames relative root))))
