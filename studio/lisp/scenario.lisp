;;;; Compatibility adapter. Headless scenario ownership lives in framework/.
(in-package :cl-mpm-studio)

(defparameter *runout-aspect* 2d0)
(defparameter *mass-scale* 1d4)

(defun deg->rad (degrees)
  (cl-mpm/framework/cliff::deg->rad degrees))

(defun make-chalk-mps (config block-size h)
  (cl-mpm/framework/cliff::make-chalk-mps
   config block-size h
   :particle-type (if (eq (param config "constitutiveModel") :custom)
                      'studio-custom-chalk
                      'cl-mpm/particle::particle-chalk-delayed)))

(defun configure-solver (sim config h)
  (let ((cl-mpm/framework/cliff::*mass-scale* *mass-scale*))
    (cl-mpm/framework/cliff::configure-solver sim config h)))

(defun cut-cliff-face (sim config shelf-length soil)
  (cl-mpm/framework/cliff::cut-cliff-face sim config shelf-length soil))

(defun cut-toe-notch (sim config shelf-length soil)
  (cl-mpm/framework/cliff::cut-toe-notch sim config shelf-length soil))

(defun make-cliff-sim (config)
  "Retain the trusted custom-model contract while delegating native assembly."
  (let ((cl-mpm/framework/cliff::*runout-aspect* *runout-aspect*)
        (cl-mpm/framework/cliff::*mass-scale* *mass-scale*))
    (cl-mpm/framework/cliff:make-cliff-sim
     config
     :particle-type (if (eq (param config "constitutiveModel") :custom)
                        'studio-custom-chalk
                        'cl-mpm/particle::particle-chalk-delayed)
     :custom-validator #'ensure-custom-model)))
