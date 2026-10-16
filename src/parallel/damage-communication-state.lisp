;; (defpackage :cl-mpm/models/damage
;;   (:use
;;    :cl
;;    :cl-mpm/utils
;;    :cl-mpm/particle)
;;   (:export))
;; (in-package :cl-mpm/models/damage)

(in-package :cl-mpm/particle)



(defclass particle-damage-mpi (particle-damage-fundemental)
    ((volume
      :accessor mp-volume
      :type double-float
      :initarg :volume
      :initform 1d0)
     (position
      :accessor mp-position
      :type MAGICL:MATRIX/DOUBLE-FLOAT
      :initform (cl-mpm/utils:vector-zeros)
      :initarg :position)
     (damage
      :accessor mp-damage
      :type DOUBLE-FLOAT
      :initarg :damage
      :initform 0d0)
     (true-local-length
      :accessor mp-true-local-length
      :type DOUBLE-FLOAT
      :initarg :local-length
      :initform 1d0)
     (local-damage-increment
      :accessor mp-local-damage-increment
      :type DOUBLE-FLOAT
      :initarg :damage-y
      :initform 0d0)
     (damage-y-local
      :accessor mp-damage-y-local
      :type DOUBLE-FLOAT
      :initform 0d0
      :initarg :damage-y)
     (damage-position
      :accessor mp-damage-position
      :initform nil)))
