(in-package :cl-mpm/particle)

(declaim (optimize (debug 0) (safety 0) (speed 3)))


(defclass particle-damage (particle particle-damage-fundemental)
  ((local-damage
    :accessor mp-local-damage
    :type DOUBLE-FLOAT
    :initform 0d0)
   (local-damage-increment
    :accessor mp-local-damage-increment
    :type DOUBLE-FLOAT
    :initarg :damage-y
    :initform 0d0)
   (damage-increment
    :accessor mp-damage-increment
    :type DOUBLE-FLOAT
    :initform 0d0)
   (undamaged-stress
    :accessor mp-undamaged-stress
    :type MAGICL:MATRIX/DOUBLE-FLOAT
    :initform (cl-mpm/utils:voigt-zeros))
   (initiation-stress
    :accessor mp-initiation-stress
    :type DOUBLE-FLOAT
    :initarg :initiation-stress
    :initform 0d0)
   (critical-stress
    :accessor mp-critical-stress
    :type DOUBLE-FLOAT
    :initarg :critical-stress
    :initform 0d0)
   (damage-rate
    :accessor mp-damage-rate
    :type DOUBLE-FLOAT
    :initarg :damage-rate
    :initform 0d0)
   (critical-damage
    :accessor mp-critical-damage
    :type DOUBLE-FLOAT
    :initarg :critical-damage
    :initform 1d0)
   (damage-ybar
    :accessor mp-damage-ybar
    :type DOUBLE-FLOAT
    :initform 0d0
    :initarg :damage-ybar
    )
   (damage-ybar-prev
    :accessor mp-damage-ybar-prev
    :type DOUBLE-FLOAT
    :initform 0d0
    :initarg :damage-ybar-prev)
   (damage-y-local
    :accessor mp-damage-y-local
    :type DOUBLE-FLOAT
    :initform 0d0
    :initarg :damage-y
    )
   (damage-y-local-prev
    :accessor mp-damage-y-local-prev
    :type DOUBLE-FLOAT
    :initform 0d0
    :initarg :damage-y)
   (time-averaged-ybar
    :accessor mp-time-averaged-ybar
    :initform 1d0)
   (time-averaged-damage-inc
    :accessor mp-time-averaged-damage-inc
    :initform 1d0)
   (time-averaged-counter
    :accessor mp-time-averaged-counter
    :initform 0d0)
   (local-length
    :accessor mp-local-length
    :type DOUBLE-FLOAT
    :initarg :local-length
    :initform 1d0)
   (local-length-damaged
    :accessor mp-local-length-damaged
    :type DOUBLE-FLOAT
    :initarg :local-length-damaged
    :initform 1d0)
   (true-local-length
    :accessor mp-true-local-length
    :type DOUBLE-FLOAT
    :initarg :local-length
    :initform 1d0)
   (damage-position
    :accessor mp-damage-position
    ;:type MAGICL:MATRIX/DOUBLE-FLOAT
    :initform nil
    ;:initform (cl-mpm/utils::vector-zeros)
    )
   (damage-model
    :accessor mp-damage-model
    :initarg :damage-model)
   (enable-damage
    :accessor mp-enable-damage
    :initarg :enable-damage
    :initform t)
   (damage-domain-update-rate
    :accessor mp-damage-domain-update-rate
    :initarg :damage-domain-rate
    :initform 0d0))
  (:documentation "A material point with a damage tensor"))

(defmethod new-loadstep-mp ((mp particle-damage))
  (with-accessors ((strain cl-mpm/particle:mp-strain)
                   (strain-n cl-mpm/particle:mp-strain-n)
                   (disp cl-mpm/particle::mp-displacement-increment)
                   (def    cl-mpm/particle:mp-deformation-gradient)
                   (def-0 cl-mpm/particle::mp-deformation-gradient-0)
                   (df-inc    cl-mpm/particle::mp-deformation-gradient-increment)
                   (ybar    cl-mpm/particle::mp-damage-ybar)
                   (ybar-prev    cl-mpm/particle::mp-damage-ybar-prev)
                   (damage    cl-mpm/particle::mp-damage)
                   (damage-n    cl-mpm/particle::mp-damage-n)
                   (y    cl-mpm/particle::mp-damage-y-local)
                   (y-prev    cl-mpm/particle::mp-damage-y-local-prev)
                   (volume    cl-mpm/particle::mp-volume)
                   (volume-n    cl-mpm/particle::mp-volume-n)
                   )
      mp
    ;; (cl-mpm/utils:matrix-copy-into def def-0)
    ;; (cl-mpm/utils:matrix-copy-into (cl-mpm/utils:matrix-eye 1d0) df-inc)
    ;; (cl-mpm/utils:voigt-copy-into strain strain-n)
    ;; (cl-mpm/fastmaths:fast-zero disp)
    (setf ybar-prev ybar)
    (setf y-prev y)
    (setf damage-n damage)
    ;; (setf volume-n volume)
    (call-next-method)))
