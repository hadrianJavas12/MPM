;;;; Historical source-path compatibility; ASDF loads owner files directly.
(in-package :cl-user)
(let ((root (merge-pathnames "../" (uiop:pathname-directory-pathname *load-truename*))))
  (dolist (relative '("materials/core/constitutive-package.lisp" "src/numerics/tensors/constitutive-primitives.lisp" "materials/models/elastic/constitutive.lisp" "materials/models/fluid/constitutive.lisp" "materials/models/viscoelastic/maxwell/constitutive.lisp" "materials/models/damage/constitutive.lisp" "materials/models/viscoplastic/glen/constitutive.lisp" "materials/models/plastic/von-mises/constitutive.lisp" "materials/models/plastic/mohr-coulomb/constitutive.lisp" "materials/models/plastic/drucker-prager/constitutive.lisp" "materials/models/plastic/von-mises/evolution/secant-hardening.lisp"))
    (load (merge-pathnames relative root))))
