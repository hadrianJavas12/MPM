;;;; Reference damping and adaptive phase rules.
;;;; Extracted without changing the existing numerical expressions.
(in-package :cl-mpm/framework/cliff)

(defun reference-critical-damping (config)
  "Paper Eq.24 for this 2D reference: beta_crit=(pi/2)*sqrt(E/(rho*h^2))."
  (* (/ pi 2d0)
     (sqrt (/ (param config "E")
              (* (param config "density") (expt (param config "meshSize") 2))))))

(defun reference-viscous-damping (config fraction)
  "Core uses -damping*M*v; paper uses -2*beta*M*v, so damping is 2*beta."
  (* 2d0 fraction (reference-critical-damping config)))

(defun reference-next-state (state epsilon oobf tolerance)
  "Algorithm 1: strict exceedance enters collapse; both strictly below leave it."
  (unless (and (reference-finite-p epsilon) (reference-finite-p oobf))
    (error "Nonfinite adaptive mass-scaling criterion"))
  (ecase state
    (:accelerate (if (or (> epsilon tolerance) (> oobf tolerance)) :collapse :accelerate))
    (:collapse (if (and (< epsilon tolerance) (< oobf tolerance)) :accelerate :collapse))))

(defun reference-zero-velocities (sim)
  (cl-mpm::iterate-over-mps
   (cl-mpm:sim-mps sim)
   (lambda (mp) (cl-mpm/fastmaths::fast-zero (cl-mpm/particle:mp-velocity mp))))
  (cl-mpm::iterate-over-nodes
   (cl-mpm:sim-mesh sim)
   (lambda (node) (cl-mpm/fastmaths::fast-zero (cl-mpm/mesh:node-velocity node)))))
