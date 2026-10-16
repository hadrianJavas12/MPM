;;;; Historical source-path compatibility; ASDF loads owner files directly.
(in-package :cl-user)
(let ((root (merge-pathnames "../../" (uiop:pathname-directory-pathname *load-truename*))))
  (dolist (relative '("materials/core/plastic-state.lisp" "src/numerics/integration/finite-difference-tangent.lisp" "materials/models/plastic/von-mises/particle.lisp" "materials/models/plastic/mohr-coulomb/particle.lisp" "materials/models/plastic/drucker-prager/particle.lisp"))
    (load (merge-pathnames relative root))))
