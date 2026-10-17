(defpackage :cl-mpm/particle
  (:use :cl
        :cl-mpm/utils)
  (:export
    #:make-particle
    #:make-particle-elastic
    #:make-particle-elastic-damage
    #:mp-mass
    #:mp-volume
    #:mp-position
    #:mp-velocity
    #:mp-stress
    #:mp-strain
    #:mp-strain-n
    #:mp-strain-rate
    #:mp-vorticity
    #:mp-gravity
    #:mp-body-force
    #:mp-damage
    #:mp-temperature
    #:mp-heat-capacity
    #:mp-critical-stress
    #:mp-deformation-gradient
    #:mp-penalty-contact
    #:mp-penalty-frictional-force
    #:constitutive-model
    #:particle
    #:particle-damage
    #:post-stress-step
    ))

(in-package :cl-mpm/particle)

(declaim (optimize (debug 0) (safety 0) (speed 3)))

(declaim (inline make-node-cache))
(defstruct (node-cache
            (:constructor make-node-cache
                (node
                 weight
                 grads
                 weight-fbar
                 grads-fbar)))
  (node nil :type (or null cl-mpm/mesh::node))
  (weight 0d0 :type double-float)
  (grads (cl-mpm/utils::make-gradients 0d0 0d0 0d0) :type cl-mpm/utils::gradients)
  (weight-fbar 0d0 :type double-float)
  (grads-fbar (cl-mpm/utils::make-gradients 0d0 0d0 0d0) :type cl-mpm/utils::gradients))

(defun make-empty-node-cache ()
  (make-node-cache nil 0d0 (cl-mpm/utils::make-gradients 0d0 0d0 0d0) 0d0 (cl-mpm/utils::make-gradients 0d0 0d0 0d0)))
(defun reset-mp-node-cache (mp)
  (setf (fill-pointer (cl-mpm/particle::mp-cached-nodes mp)) 0))

;(defun make-node-cache (&key node weight grads weight-fbar grads-fbar))

;; (defun push-mp-cache-node (mp &key node weight grads weight-fbar grads-fbar)
;;   (declare (particle mp))
;;   (with-slots ((nc cached-nodes))
;;       mp
;;     (when (< (fill-pointer nc) (array-total-size nc))
;;       ()
;;       ))

;;   )

(defclass particle ()
  ((position
    :accessor mp-position
    :type MAGICL:MATRIX/DOUBLE-FLOAT
    :initform (cl-mpm/utils:vector-zeros)
    :initarg :position)
   (size
    :accessor mp-domain-size
    :type magicl:matrix/double-float
    :initarg :size
    :initform (cl-mpm/utils:vector-zeros))
   (true-domain
    :accessor mp-true-domain
    :type (or magicl:matrix/double-float null)
    :initarg :true-domain
    :initform nil
    ;; (cl-mpm/utils::matrix-eye 1d0)
    )
   (mass
     :accessor mp-mass
     :type double-float
     :initarg :mass
     :initform 1d0)
   (velocity
    :accessor mp-velocity
    :type MAGICL:MATRIX/DOUBLE-FLOAT
    :initarg :velocity
    :initform (cl-mpm/utils:vector-zeros))
   (velocity-gradient
    :accessor mp-velocity-gradient
    :type MAGICL:MATRIX/DOUBLE-FLOAT
    :initform (cl-mpm/utils:matrix-zeros))
   (acceleration
    :accessor mp-acceleration
    :type MAGICL:MATRIX/DOUBLE-FLOAT
    :initform (cl-mpm/utils:vector-zeros))
   (volume
    :accessor mp-volume
    :type double-float
    :initarg :volume
    :initform 1d0)
   (index
     :accessor mp-index
     :type integer
     :initform -1
     :initarg :index)
   (unique-index
    :accessor mp-unique-index
    :type integer
    :initform -1
    :initarg :unique-index)
   (mpi-index
    :accessor mp-mpi-index
    :type integer
    :initform -1
    :initarg :mpi-index)
   (mesh-index
    :accessor mp-mesh-index
    :type integer
    :initform 0
    :initarg :mesh-index)
   (volume-0
    :accessor mp-volume-0
    :type double-float
    ;;By specifying both :volume and :volume-0 as initargs, it will capture volume by default
    ;;but it also allows for direct specification
    :initarg :volume
    :initarg :volume-0
    :initform 1d0)
   (volume-n
    :accessor mp-volume-n
    :type double-float
    ;;By specifying both :volume and :volume-0 as initargs, it will capture volume by default
    ;;but it also allows for direct specification
    :initarg :volume
    :initarg :volume-n
    :initform 1d0)
   (size-0
    :accessor mp-domain-size-0
    :type magicl:matrix/double-float
    :initarg :size-0
    :initform (cl-mpm/utils:vector-zeros))
   (stress
     :accessor mp-stress
     :type MAGICL:MATRIX/DOUBLE-FLOAT
     :initarg :stress
     :initform (cl-mpm/utils::voigt-zeros))
   (stress-kirchoff
    :accessor mp-stress-kirchoff
    :type MAGICL:MATRIX/DOUBLE-FLOAT
    :initarg :stress
    :initform (cl-mpm/utils:voigt-zeros))
   (stress-eigenvalues
    :initform nil
    :accessor mp-stress-eigenvalues)
   (stress-eigenvectors
    :initform nil
    :accessor mp-stress-eigenvectors)
   (strain-n
    :accessor mp-strain-n
    :type MAGICL:MATRIX/DOUBLE-FLOAT
    :initform (cl-mpm/utils:voigt-zeros))
   (strain
     :accessor mp-strain
     :type MAGICL:MATRIX/DOUBLE-FLOAT
     :initarg :strain
     :initform (cl-mpm/utils:voigt-zeros))
   (trial-elastic-strain
     :accessor mp-trial-elastic-strain
     :type MAGICL:MATRIX/DOUBLE-FLOAT
     :initform (cl-mpm/utils:voigt-zeros))
   (stretch-tensor
    :accessor mp-stretch-tensor
    :type MAGICL:MATRIX/DOUBLE-FLOAT
    :initform (cl-mpm/utils::matrix-zeros))
   (stretch-tensor-fbar
    :accessor mp-stretch-tensor-fbar
    :type MAGICL:MATRIX/DOUBLE-FLOAT
    :initform (cl-mpm/utils::matrix-zeros))
   (strain-rate
     :accessor mp-strain-rate
     :type MAGICL:MATRIX/DOUBLE-FLOAT
     :accessor mp-strain-rate
     :initarg :strain-rate
     :initform (cl-mpm/utils:voigt-zeros))
   (velocity-rate
    :accessor mp-velocity-rate
    :type MAGICL:MATRIX/DOUBLE-FLOAT
    :accessor mp-velocity-rate
    :initform (cl-mpm/utils::voigt-zeros))
   (eng-strain-rate
    :accessor mp-eng-strain-rate
    :type MAGICL:MATRIX/DOUBLE-FLOAT
    :initform (cl-mpm/utils:voigt-zeros))
   (vorticity
    :accessor mp-vorticity
    :type MAGICL:MATRIX/DOUBLE-FLOAT
    :initform (cl-mpm/utils::voigt-zeros))
   (deformation-gradient
     :accessor mp-deformation-gradient
     :type MAGICL:MATRIX/DOUBLE-FLOAT
     :initarg :deformation-gradient
     :initform (cl-mpm/utils:matrix-eye 1d0))
   (deformation-gradient-0
       :accessor mp-deformation-gradient-0
       :type MAGICL:MATRIX/DOUBLE-FLOAT
       :initarg :deformation-gradient
       :initform (cl-mpm/utils:matrix-eye 1d0))
   (deformation-gradient-increment
       :accessor mp-deformation-gradient-increment
       :type MAGICL:MATRIX/DOUBLE-FLOAT
       :initarg :deformation-gradient-increment
       :initform (cl-mpm/utils:matrix-eye 1d0))
   (deformation-gradient-increment-inverse
       :accessor mp-deformation-gradient-increment-inverse
       :type MAGICL:MATRIX/DOUBLE-FLOAT
       :initform (cl-mpm/utils:matrix-eye 1d0))

   (deformation-jacobian-strain
       :accessor mp-deformation-jacobian-strain
       :type double-float
       :initform 1d0)
   (deformation-gradient-strain-increment
       :accessor mp-deformation-gradient-strain-increment
       :type MAGICL:MATRIX/DOUBLE-FLOAT
       :initform (cl-mpm/utils:matrix-eye 1d0))
   (deformation-gradient-strain-increment-inverse
       :accessor mp-deformation-gradient-strain-increment-inverse
       :type MAGICL:MATRIX/DOUBLE-FLOAT
       :initform (cl-mpm/utils:matrix-eye 1d0))
   (gravity
     :type double-float
     :accessor mp-gravity
     :initform 0d0;-9.8d0
     :initarg :gravity
     )
   (pressure
    :type double-float
    :accessor mp-pressure
    :initform 0d0
    )
   (pressure-datum
    :type double-float
    :accessor mp-pressure-datum
    :initform 0d0)
   (pressure-head
    :type double-float
    :accessor mp-pressure-head
    :initform 0d0)
   (boundary
    :type double-float
    :accessor mp-boundary
    :initform 0d0)
   (gravity-axis
    :type magicl:matrix/double-float
    :accessor mp-gravity-axis
    :initform (vector-from-list '(0d0 1d0 0d0))
    :initarg :gravity-axis)
   (body-force
     :accessor mp-body-force
     :type MAGICL:MATRIX/DOUBLE-FLOAT
     :initarg :body-force
     :initform (cl-mpm/utils::vector-zeros))
   (displacement-increment
    :accessor mp-displacement-increment
    :type MAGICL:MATRIX/DOUBLE-FLOAT
    :initform (cl-mpm/utils::vector-zeros))
   (position-trial
    :accessor mp-position-trial
    ;; :initarg :position
    :type MAGICL:MATRIX/DOUBLE-FLOAT
    :initform (cl-mpm/utils:vector-zeros))
   (displacement
    :accessor mp-displacement
    :type MAGICL:MATRIX/DOUBLE-FLOAT
    :initform (cl-mpm/utils::vector-zeros))
   (cached-nodes
    :accessor mp-cached-nodes
    :initarg :nc
    :initform (make-array 8 :fill-pointer 0 :element-type 'node-cache :initial-element (make-empty-node-cache)))
   (p-modulus
    :accessor mp-p-modulus
    :initform 1d0
    )
   (p-modulus-0
    :accessor mp-p-modulus-0
    :initform 1d0)
   (damage
    :accessor mp-damage
    :type DOUBLE-FLOAT
    :initarg :damage
    :initform 0d0)
   (damage-n
    :accessor mp-damage-n
    :type DOUBLE-FLOAT
    :initarg :damage
    :initform 0d0)
   (damage-prev-trial
    :accessor mp-damage-prev-trial
    :type DOUBLE-FLOAT
    :initarg :damage
    :initform 0d0)
   (j-fbar
    :accessor mp-j-fbar
    :initform 1d0)
   (split-depth
    :accessor mp-split-depth
    :type integer
    :initarg :split-depth
    :initform 0)
   (single-particle
    :accessor mp-single-particle
    :type boolean
    :initform nil)
   (fbar-j
    :accessor mp-debug-j
    :type double-float
    :initform 0d0)
   (fbar-j-gather
    :accessor mp-debug-j-gather
    :type double-float
    :initform 0d0)
   (penalty-frictional-force
    :accessor mp-penalty-frictional-force
    :type MAGICL:MATRIX/DOUBLE-FLOAT
    :initform (cl-mpm/utils::vector-zeros))
   (penalty-frictional-force-prev
    :accessor mp-penalty-frictional-force-prev
    :type MAGICL:MATRIX/DOUBLE-FLOAT
    :initform (cl-mpm/utils::vector-zeros))
   (penalty-normal-force
    :accessor mp-penalty-normal-force
    :type double-float
    :initform 0d0)
   (penalty-friction-stick
    :accessor mp-penalty-friction-stick
    :type boolean
    :initform nil)
   ;;This reports whether we had contact over the course of the last timestep
   (penalty-contact-step
    :accessor mp-penalty-contact-step
    :type boolean
    :initform nil)
   ;;This is for keeping track of whether we will be having contact coming up
   (penalty-contact
    :accessor mp-penalty-contact
    :type boolean
    :initform nil)
   (penalty-energy
    :accessor mp-penalty-energy
    :type double-float
    :initform 0d0
    )
   (penalty-stiffness
    :accessor mp-penalty-stiffness
    :type double-float
    :initform 0d0)
   (penalty-contact-point
    :accessor mp-penalty-contact-point
    :type MAGICL:MATRIX/DOUBLE-FLOAT
    :initform (cl-mpm/utils::vector-zeros))
   )
  (:documentation "A single material point"))
