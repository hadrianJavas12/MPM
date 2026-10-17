(in-package :cl-mpm/particle)

(declaim (optimize (debug 0) (safety 0) (speed 3)))



(defclass particle-viscoplastic (particle-elastic)
  ((visc-factor
    :accessor mp-visc-factor
    :initarg :visc-factor)
   (visc-power
    :accessor mp-visc-power
    :initarg :visc-power)
   (true-visc
    :accessor mp-true-visc
    :initform 0d0)
   (time-averaged-visc
    :accessor mp-time-averaged-visc
    :initform 0d0)
   )
  (:documentation "A visco-plastic material point"))

(defmethod constitutive-model ((mp particle-viscoplastic) strain dt)
  "Function for modeling stress intergrated viscoplastic norton-hoff material"
  (with-slots ((E E)
               (nu nu)
               (de elastic-matrix)
               (visc-factor visc-factor)
               (visc-power visc-power)
               (strain-rate strain-rate) ;Note strain rate is actually strain increment through dt
               (velocity-rate velocity-rate) ;Note strain rate is actually strain increment through dt
               (strain-plastic strain-plastic)
               (def deformation-gradient)
               (vorticity vorticity)
               (D stretch-tensor)
               (stress stress)
               (temp true-visc)
               (eng-strain-rate eng-strain-rate)
               )
      mp
    (declare (double-float E visc-factor visc-power))
    (let* ((eng-strain-rate (cl-mpm/fastmaths::fast-.* (magicl:map (lambda (x) (* x (exp x))) strain) velocity-rate
                                                  (cl-mpm/utils:voigt-from-list '(1d0 1d0 1d0 0.5d0 0.5d0 0.5d0))))
          (viscosity (cl-mpm/constitutive::glen-viscosity-strain eng-strain-rate visc-factor visc-power))
          ;(viscosity (cl-mpm/constitutive::glen-viscosity-stress stress visc-factor visc-power))
          )
      ;; stress
      (setf temp viscosity)
      (cl-mpm/fastmaths::fast-.+
       stress
       (objectify-stress-logspin
        (if (> viscosity 0d0)
            (cl-mpm/constitutive::maxwell strain-rate stress E nu de viscosity dt)
            (cl-mpm/constitutive::linear-elastic-mat strain-rate de))
        stress
        def
        vorticity
        D
        )))))
