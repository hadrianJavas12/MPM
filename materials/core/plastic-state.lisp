;; (defpackage :cl-mpm/models/plastic
;;   (:use :cl
;;    :cl-mpm/utils)
;;   (:export
;;    )
;;   )
;; (in-package :cl-mpm/models/plastic)
(in-package :cl-mpm/particle)
(declaim #.cl-mpm/settings:*optimise-setting*)

(defclass particle-plastic (particle)
  ((enable-plasticity
    :accessor mp-enable-plasticity
    :initarg :enable-plasticity
    :initform t
    )
   (strain-plastic-vm-1
    :accessor mp-strain-plastic-vm-1
    :type DOUBLE-FLOAT
    :initform 0d0)
   (strain-plastic-vm
    :accessor mp-strain-plastic-vm
    :type DOUBLE-FLOAT
    :initform 0d0)
   (strain-plastic-vm-inc
    :accessor mp-strain-plastic-vm-inc
    :type DOUBLE-FLOAT
    :initform 0d0)
   (strain-plastic
    :accessor mp-strain-plastic
    :type MAGICL:MATRIX/DOUBLE-FLOAT
    :initarg :strain-plastic
    :initform (cl-mpm/utils:voigt-zeros))
   (yield-func
    :accessor mp-yield-func
    :type double-float
    :initform 0d0)
   (softening
    :accessor mp-softening
    :initarg :softening
    :initform 0d0)
   (plastic-iterations
    :accessor mp-plastic-iterations
    :initform 0)))

(defmethod cl-mpm/particle::reset-loadstep-mp ((mp particle-plastic))
  (with-accessors ((ps-vm-1 mp-strain-plastic-vm-1)
                   (ps-vm mp-strain-plastic-vm)
                   )
      mp
    (declare (double-float ps-vm ps-vm-1))
    (setf ps-vm ps-vm-1))
  (call-next-method))
(defmethod cl-mpm/particle::new-loadstep-mp ((mp particle-plastic))
  (with-accessors ((ps-vm-1 mp-strain-plastic-vm-1)
                   (ps-vm-inc mp-strain-plastic-vm-inc)
                   (ps-vm mp-strain-plastic-vm)
                   )
      mp
    (declare (double-float ps-vm ps-vm-1 ps-vm-inc))
    (setf ps-vm-1 ps-vm))
  (call-next-method))
