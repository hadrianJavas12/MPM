;;;; Historical source-path compatibility; ASDF loads owner files directly.
(in-package :cl-user)
(let ((root (merge-pathnames "../../" (uiop:pathname-directory-pathname *load-truename*))))
  (dolist (relative '("src/parallel/damage-communication-state.lisp" "materials/models/damage/legacy-particles.lisp"))
    (load (merge-pathnames relative root))))
