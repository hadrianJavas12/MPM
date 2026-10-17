(in-package :cl-mpm/particle)

(declaim (optimize (debug 0) (safety 0) (speed 3)))



(defclass particle-fluid (particle)
  ((rest-density
    :accessor mp-rest-density
    :initarg :rest-density
    )
   (stiffness
    :accessor mp-stiffness
    :initarg :stiffness)
   (adiabatic-index
    :accessor mp-adiabatic-index
    :initarg :adiabatic-index)
   (viscosity
    :accessor mp-viscosity
    :initarg :viscosity))
  (:documentation "A fluid material point"))

(defmethod constitutive-model ((mp particle-fluid) strain dt)
  "Strain intergrated elsewhere, just using elastic tensor"
  (with-slots ((viscosity viscosity)
               (mass mass)
               (volume volume)
               (rest-density rest-density)
               (stiffness stiffness)
               (adiabatic-index adiabatic-index)
               )
      mp
    (let* ((density (/ mass volume))
           (pressure (* stiffness (expt (- (/ density rest-density) 1) adiabatic-index))))
      (cl-mpm/constitutive:newtonian-fluid strain pressure viscosity))))
