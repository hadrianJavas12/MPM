;;;; Historical standalone native triaxial API; actual owners are outside framework.
(in-package :cl-user)
(let ((root (merge-pathnames "../" (uiop:pathname-directory-pathname *load-truename*))))
  (dolist (relative '("src/simulation/compatibility/triaxial-package.lisp"
                     "scenarios/triaxial/state.lisp"
                     "src/simulation/config/legacy-triaxial-values.lisp"
                     "scenarios/triaxial/config.lisp"
                     "src/output/legacy-triaxial-json.lisp"
                     "materials/adapters/diagnostics-call.lisp"
                     "src/numerics/legacy-tensors.lisp"
                     "src/measurements/legacy-particle.lisp"
                     "scenarios/triaxial/stress-measures.lisp"
                     "src/measurements/legacy-stress.lisp"
                     "materials/adapters/triaxial.lisp"
                     "materials/adapters/legacy-triaxial.lisp"
                     "scenarios/triaxial/geometry.lisp"
                     "src/boundaries/pressure/isotropic.lisp"
                     "scenarios/triaxial/measurements.lisp"
                     "scenarios/triaxial/mpm.lisp"
                     "scenarios/triaxial/homogeneous.lisp"
                     "scenarios/triaxial/controls.lisp"
                     "scenarios/triaxial/runner.lisp"))
    (load (merge-pathnames relative root))))
