(in-package :cl-mpm/constitutive)

(declaim #.cl-mpm/settings:*optimise-setting*)



(defun eos-cole (density rest-density stiffness power)
  "Cole equation of state for pressure"
  (* stiffness (- (expt (/ density rest-density) power) 1)))

(defun eos-ideal-gas (density rest-density rest-pressure adiabatic-index)
  "Ideal gas law equation of state for pressure"
  (* rest-pressure (expt (/ density rest-density) adiabatic-index)))


(defun newtonian-fluid (strain pressure viscosity)
  "A newtonian fluid model"
  (let* ((strain-matrix (voight-to-matrix strain))
         (dev-strain (matrix-to-voight (magicl:.- strain-matrix (magicl:eye 2 :value (/ (magicl:trace strain-matrix) 3))))))
    (magicl:.- (magicl:from-list (list (- pressure) (- pressure) 0d0) '(3 1))
               (magicl:scale dev-strain viscosity))))
