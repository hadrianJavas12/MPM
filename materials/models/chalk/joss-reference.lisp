(in-package :cl-mpm/framework/cliff)

(defclass joss-reference-chalk (cl-mpm/particle::particle-chalk-delayed)
  ((plastic-cohesion :initarg :reference-cohesion :reader reference-cohesion)
   (plastic-friction :initarg :reference-friction :reader reference-friction)
   (plastic-dilation :initarg :reference-dilation :reader reference-dilation)
   (tensile-ratio :initarg :reference-tensile :reader reference-tensile)
   (compression-ratio :initarg :reference-compression :reader reference-compression)
   (shear-ratio :initarg :reference-shear :reader reference-shear)))

(defmethod initialize-instance :after ((mp joss-reference-chalk) &key)
  ;; The inherited frictional constructor recalculates cohesion/phi/residual
  ;; shear. Restore the explicitly prescribed reference parameters afterwards.
  (setf (cl-mpm/particle::mp-c mp) (reference-cohesion mp)
        (cl-mpm/particle::mp-phi mp) (reference-friction mp)
        (cl-mpm/particle::mp-psi mp) (reference-dilation mp)
        (cl-mpm/particle::mp-k-tensile-residual-ratio mp) (reference-tensile mp)
        (cl-mpm/particle::mp-k-compressive-residual-ratio mp) (reference-compression mp)
        (cl-mpm/particle::mp-shear-residual-ratio mp) (reference-shear mp)))

(defmethod cl-mpm/damage::damage-model-calculate-y ((mp joss-reference-chalk) dt)
  (declare (ignore dt))
  ;; Author Joss example's DP driving stress; stored friction angle is radians.
  ;; Frozen-state comparison and a short physical pilot support this adaptation,
  ;; but do not establish full fracture/run-out agreement with the reference.
  (let ((value (max 0d0 (cl-mpm/damage::drucker-prager-criterion
                         (cl-mpm/particle::mp-undamaged-stress mp)
                         (cl-mpm/particle::mp-friction-angle mp)))))
    (setf (cl-mpm/particle::mp-damage-y-local mp) value
          (cl-mpm/particle::mp-local-damage-increment mp) value)))

(defmethod cl-mpm::update-particle (mesh (mp joss-reference-chalk) dt)
  (cl-mpm::update-particle-kirchoff mesh mp dt)
  (cl-mpm::update-domain-det mesh mp))
