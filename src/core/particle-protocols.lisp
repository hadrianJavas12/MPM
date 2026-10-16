(in-package :cl-mpm/particle)

(declaim (optimize (debug 0) (safety 0) (speed 3)))



(defmethod (setf mp-domain-size) :after (value (p particle))
  )

(defmethod initialize-instance :after ((p particle) &key)
  (with-accessors ((domain mp-domain-size)
                   (domain-true mp-true-domain)
                   (position mp-position)
                   (position-trial mp-position-trial)
                   (gravity-axis mp-gravity-axis))
      p
    ;;(cl-mpm/utils:matrix-copy-into position position-trial)
    (setf position-trial (cl-mpm/utils:vector-copy position))
    (setf gravity-axis (cl-mpm/utils::vector-copy gravity-axis))
    (unless domain-true
      (setf domain-true (cl-mpm/utils::matrix-eye 1d0))
      (setf
       (magicl:tref domain-true 0 0) (varef domain 0)
       (magicl:tref domain-true 1 1) (varef domain 1)
       (magicl:tref domain-true 2 2) (varef domain 2))
      )))

(defmethod reinitialize-instance :after ((p particle) &rest initargs &key)
  (with-accessors ((domain mp-domain-size)
                   (domain-true mp-true-domain)
                   (position mp-position)
                   (position-trial mp-position-trial)
                   (gravity-axis mp-gravity-axis))
      p
    (setf position-trial (cl-mpm/utils:vector-copy position))
    (unless domain-true
      (setf domain-true (cl-mpm/utils::matrix-eye 1d0))))
  )

(defclass particle-thermal (particle)
  (
   (temperature
    :accessor mp-temperature
    :type DOUBLE-FLOAT
    :initarg :temperature
    :initform 0d0)
   (heat-capacity
    :accessor mp-heat-capacity
    :type DOUBLE-FLOAT
    :initarg :heat-capacity
    :initform 0d0)
   (thermal-conductivity
    :accessor mp-thermal-conductivity
    :type DOUBLE-FLOAT
    :initarg :thermal-conductivity
    :initform 1d0)
   )
  (:documentation "A material point with a thermal properties"))



;; (defclass particle-thermoelastic-damage (particle-elastic particle-damage particle-thermal)
;;   ()
;;   (:documentation "A mp with elastic mechanics with variable thermal fields"))
;; (defclass particle-thermoviscoplastic-damage (particle-viscoplastic particle-damage particle-thermal)
;;   ()
;;   (:documentation "A mp with viscoplastic mechanics with variable thermal fields"))

;; (defclass particle-thermofluid-damage (particle-fluid particle-damage particle-thermal)
;;   ()
;;   (:documentation "A mp with viscoplastic mechanics with variable thermal fields"))
;; (defclass particle-viscoelastic-fracture (particle-viscoelastic particle-fracture)
;;   ()
;;   (:documentation "A viscoelastic mp with fracture mechanics"))


(defun make-particle (nD &optional (constructor 'particle) &rest args &key  (position nil) (volume 1) (mass 1) &allow-other-keys)
  (progn
    (if (eq position nil)
        (setf position (magicl:zeros (list nD 1)))
        (setf position (magicl:from-list (mapcar (lambda (x) (coerce x 'double-float)) position) (list nD 1))))
    (let ((stress-size 3))
      (let ((mp (apply #'make-instance constructor
                      :volume (coerce volume 'double-float)
                      :mass (coerce mass 'double-float)
                      :position position
                      args)))
        (progn
          (setf (mp-domain-size-0 mp) (magicl:scale (mp-domain-size-0 mp) 1d0))
          mp)))))

(defgeneric estimate-stiffness (mp)
    (:documentation "Estimate stiffness P-wave at current state"))


(defgeneric constitutive-model (mp elastic-trial-strain dt)
    (:documentation "Compute new stress state given elastic strain")
    (:method (mp strain dt)
        (magicl:scale strain 0)))

(defgeneric post-stress-step (mesh mp dt)
  (:documentation "This step gets called after full stress state resolved and allows for other processing"))

(defmethod post-stress-step (mesh mp dt)
  ())


;; (defclass particle-elastic-damage-ideal (particle-concrete)
;;   )




(defclass particle-damage-fundemental ()
  ())



(defgeneric reset-loadstep-mp (mp)
  (:documentation "Finalise a dynamic relaxation loadstep, setting converged values to previous values"))

(defmethod reset-loadstep-mp ((mp particle))
  (with-accessors ((strain cl-mpm/particle:mp-strain)
                   (strain-n cl-mpm/particle:mp-strain-n)
                   (disp cl-mpm/particle::mp-displacement-increment)
                   (def    cl-mpm/particle:mp-deformation-gradient)
                   (def-0 cl-mpm/particle::mp-deformation-gradient-0)
                   (df-inc    cl-mpm/particle::mp-deformation-gradient-increment)
                   (volume    cl-mpm/particle::mp-volume)
                   (volume-n    cl-mpm/particle::mp-volume-n)
                   (position    cl-mpm/particle::mp-position)
                   (position-trial    cl-mpm/particle::mp-position-trial)
                   (fric-force cl-mpm/particle::mp-penalty-frictional-force)
                   (fric-force-n cl-mpm/particle::mp-penalty-frictional-force-prev))
      mp
    (cl-mpm/utils:matrix-copy-into def-0 def)
    (cl-mpm/utils:matrix-copy-into (cl-mpm/utils:matrix-eye 1d0) df-inc)
    (cl-mpm/utils:voigt-copy-into strain-n strain)
    (cl-mpm/utils:vector-copy-into position position-trial)
    (cl-mpm/utils:vector-copy-into fric-force-n fric-force)
    (setf volume volume-n)
    ))

(defgeneric new-loadstep-mp (mp)
  (:documentation "Finalise a dynamic relaxation loadstep, setting converged values to previous values"))

(defmethod new-loadstep-mp ((mp particle))
  (with-accessors ((strain cl-mpm/particle:mp-strain)
                   (strain-n cl-mpm/particle:mp-strain-n)
                   (disp cl-mpm/particle::mp-displacement-increment)
                   (def    cl-mpm/particle:mp-deformation-gradient)
                   (def-0 cl-mpm/particle::mp-deformation-gradient-0)
                   (df-inc    cl-mpm/particle::mp-deformation-gradient-increment)
                   (volume    cl-mpm/particle::mp-volume)
                   (volume-n    cl-mpm/particle::mp-volume-n)
                   (position    cl-mpm/particle::mp-position)
                   (position-trial    cl-mpm/particle::mp-position-trial)
                   (fric-force cl-mpm/particle::mp-penalty-frictional-force)
                   (p-wave cl-mpm/particle::mp-p-modulus)
                   (fric-force-n cl-mpm/particle::mp-penalty-frictional-force-prev))
      mp
    (cl-mpm/utils:matrix-copy-into def def-0)
    (cl-mpm/utils:matrix-copy-into (cl-mpm/utils:matrix-eye 1d0) df-inc)
    (cl-mpm/utils:voigt-copy-into strain strain-n)
    (cl-mpm/utils:vector-copy-into fric-force fric-force-n)
    (cl-mpm/utils:vector-copy-into position position-trial)
    (setf p-wave (estimate-stiffness mp))
    (setf volume-n volume)))




(defgeneric compute-mp-energy-release (mp))
(defmethod compute-mp-energy-release ((mp cl-mpm/particle::particle))
  0d0)

