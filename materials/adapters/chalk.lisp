(in-package :cl-mpm/framework/cliff)

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
