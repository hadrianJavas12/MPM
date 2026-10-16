;;;; Historical source-path compatibility; ASDF loads owner files directly.
(in-package :cl-user)
(let ((root (merge-pathnames "../../" (uiop:pathname-directory-pathname *load-truename*))))
  (dolist (relative '("src/numerics/tensors/damage-primitives.lisp" "materials/models/damage/legacy-state-evolution.lisp" "src/damage/nonlocal/legacy.lisp" "materials/models/concrete/evolution/native-hooks.lisp"))
    (load (merge-pathnames relative root))))
