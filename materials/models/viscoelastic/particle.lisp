(in-package :cl-mpm/particle)

(declaim (optimize (debug 0) (safety 0) (speed 3)))



(defclass particle-viscoelastic (particle-elastic)
  (
   (viscosity
    :accessor mp-viscosity
    :initarg :viscosity)
   )
  (:documentation "A visco-elastic material point"))

(defmethod constitutive-model ((mp particle-viscoelastic) strain dt)
  "Function for modelling stress intergrated viscoelastic maxwell material"
  (with-slots ((E E)
               (nu nu)
               (viscosity viscosity)
               (strain-rate strain-rate) ;Note strain rate is actually strain increment through dt
               (vorticity vorticity)
               (stress stress))
      mp
    (cl-mpm/constitutive:maxwell strain-rate stress E nu viscosity dt vorticity)))
