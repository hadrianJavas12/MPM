;;;; Native triaxial scenario: material.lisp
(in-package :cl-mpm/calibration/triaxial)

(defun material-initargs (config)
  "Configure the existing native VM class; never replace its constitutive law."
  (let ((su (num config "undrainedStrengthPa" 25d3)))
    (list :E (num config "youngsModulusPa" 5d6)
          :nu (num config "poissonRatio" 0.49d0)
          :rho (* (sqrt (/ 8d0 3d0)) su)
          :rho-r (* (sqrt (/ 8d0 3d0)) su) :softening 0d0
          :enable-plasticity (value config "enablePlasticity" t))))

(defun initialize-prestress (sim config)
  "F=I defines the specimen after isotropic cell-pressure application."
  (let ((p (num config "cellPressurePa" 50d3))
        (e (num config "youngsModulusPa" 5d6))
        (nu (num config "poissonRatio" 0.49d0)))
    (loop for mp across (cl-mpm:sim-mps sim) do
      (dotimes (i 3)
        (setf (component (cl-mpm/particle:mp-strain mp) i)
              (/ (* (- p) (- 1d0 (* 2d0 nu))) e)
              (component (cl-mpm/particle:mp-strain-n mp) i)
              (/ (* (- p) (- 1d0 (* 2d0 nu))) e)
              (component (cl-mpm/particle:mp-stress mp) i) (- p)
              (component (cl-mpm/particle::mp-stress-kirchoff mp) i) (- p))))))
