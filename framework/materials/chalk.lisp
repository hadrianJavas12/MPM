;;;; Dedicated Joss chalk law; engine defaults are unchanged.
;;;; Extracted without changing the existing numerical expressions.
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

(defun make-joss-chalk-mps (config size counts damage-angle initiation ductility)
  "Native reference material construction, separate from geometry and solver."
  (cl-mpm/setup::make-mps-from-list
   (cl-mpm/setup::make-block-mps-list
    '(0d0 0d0) size counts (param config "density") 'joss-reference-chalk
    :E (param config "E") :nu (param config "nu")
    :friction-angle (deg->rad damage-angle)
    :residual-friction (deg->rad 30d0) :oversize 0.99d0
    :initiation-stress initiation :ductility ductility
    :local-length (param config "nonlocalLength")
    :delay-time (param config "delayTime")
    :delay-exponent (param config "damageDelayExponent")
    :reference-cohesion (param config "cohesion")
    :reference-friction (deg->rad (param config "frictionAngle"))
    :reference-dilation (deg->rad (param config "dilatancyAngle"))
    :reference-tensile (param config "residualTensileRatio")
    :reference-compression (param config "residualCompressionRatio")
    :reference-shear (param config "residualShearRatio")
    :index 0 :enable-damage nil :enable-plasticity nil
    :gravity -9.8d0 :gravity-axis (cl-mpm/utils:vector-from-list '(0d0 1d0 0d0)))))

(defun make-chalk-mps (config block-size h
                       &key (particle-type 'cl-mpm/particle::particle-chalk-delayed))
  "Material points filling BLOCK-SIZE with particle-chalk-delayed."
  (let* ((mps-per-cell (param config "mpsPerCell"))
         (friction (param config "frictionAngle"))
         (counts (mapcar (lambda (s) (max 1 (round (* s mps-per-cell) h))) block-size)))
    (cl-mpm/setup::make-mps-from-list
     (cl-mpm/setup::make-block-mps-list
      (list 0d0 0d0)
      block-size
      counts
      (param config "density")
      particle-type
      :E (param config "E")
      :nu (param config "nu")
      :enable-plasticity (param config "enablePlasticity")
      :enable-damage (param config "enableDamage")
      :friction-angle friction
      :phi (deg->rad friction)
      :psi (deg->rad (param config "dilatancyAngle"))
      :c (param config "cohesion")
      :initiation-stress (param config "initiationStress")
      :delay-time (param config "delayTime")
      :ductility (param config "ductility")
      :critical-damage 1d0
      :damage-domain-rate 0.5d0
      :local-length (param config "nonlocalLength")
      :local-length-damaged 1d-9
      :gravity -9.8d0
      :gravity-axis (cl-mpm/utils:vector-from-list '(0d0 1d0 0d0))))))
