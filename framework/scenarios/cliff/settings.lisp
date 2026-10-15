;;;; Legacy chalk solver settings and unit conversion.
;;;; Extracted without changing the existing numerical expressions.
(in-package :cl-mpm/framework/cliff)

(defparameter *runout-aspect* 2d0
  "Length of the empty runout region, as a multiple of the cliff height.")

(defparameter *mass-scale* 1d4
  "Mass scaling factor (quasi-static acceleration), as in the upstream example.")

(defun deg->rad (deg) (* deg (/ pi 180d0)))

(defun configure-solver (sim config h)
  "Solver flags, mass scaling, time step and fixed outer boundaries."
  (setf (cl-mpm:sim-allow-mp-split sim) t
        (cl-mpm::sim-enable-damage sim) (param config "enableDamage")
        (cl-mpm::sim-nonlocal-damage sim) t
        (cl-mpm::sim-enable-fbar sim) t
        (cl-mpm::sim-allow-mp-damage-removal sim) nil
        (cl-mpm::sim-mp-damage-removal-instant sim) nil
        (cl-mpm::sim-mass-filter sim) 1d-15
        (cl-mpm::sim-mass-scale sim) *mass-scale*
        (cl-mpm:sim-damping-factor sim) (* 1d-1 *mass-scale*))
  (let ((mp0 (aref (cl-mpm:sim-mps sim) 0)))
    (setf (cl-mpm:sim-dt sim)
          (* h (sqrt *mass-scale*)
             (sqrt (/ (param config "density")
                      (cl-mpm/particle::mp-p-modulus mp0))))))
  ;; Rollers on the sides, fixed base, free top.
  (setf (cl-mpm:sim-bcs sim)
        (cl-mpm/bc::make-outside-bc-var
         (cl-mpm:sim-mesh sim)
         (lambda (i) (cl-mpm/bc::make-bc-fixed i '(0 nil nil)))
         (lambda (i) (cl-mpm/bc::make-bc-fixed i '(0 nil nil)))
         (lambda (i) (cl-mpm/bc::make-bc-fixed i '(0 0 nil)))
         (lambda (i) (cl-mpm/bc::make-bc-fixed i '(0 0 nil)))
         (lambda (i) (cl-mpm/bc::make-bc-fixed i '(nil nil 0)))
         (lambda (i) (cl-mpm/bc::make-bc-fixed i '(nil nil 0)))))
  sim)
