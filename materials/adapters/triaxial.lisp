(in-package :cl-mpm/calibration/triaxial)

(defun material-initargs (config)
  "Configure the existing native VM class; never replace its constitutive law."
  (let ((su (num config "undrainedStrengthPa" 25d3)))
    (list :E (num config "youngsModulusPa" 5d6)
          :nu (num config "poissonRatio" 0.49d0)
          :rho (* (sqrt (/ 8d0 3d0)) su)
          :rho-r (* (sqrt (/ 8d0 3d0)) su) :softening 0d0
          :enable-plasticity (value config "enablePlasticity" t))))
