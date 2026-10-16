;;;; Historical source-path compatibility; ASDF loads owner files directly.
(in-package :cl-user)
(let ((root (merge-pathnames "../" (uiop:pathname-directory-pathname *load-truename*))))
  (dolist (relative '("src/core/particle-base.lisp" "src/core/particle-protocols.lisp" "materials/models/elastic/particle.lisp" "src/numerics/tensors/particle-objectivity.lisp" "materials/models/fluid/particle.lisp" "materials/models/viscoelastic/particle.lisp" "materials/models/viscoplastic/particle.lisp" "materials/models/damage/particle.lisp"))
    (load (merge-pathnames relative root))))
