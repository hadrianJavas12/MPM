;;;; Explicit opt-in class; inherited state/transport/rollback remains unchanged.
(in-package :cl-mpm/models/wang2017-apex)

(defun make-soil2-apex-law ()
  "Same paper strength curve; the declared composite apex flow is additional."
  (mc-evolution:make-evolution-law
   :variant :hs :points '((0d0 35d0)) :psi 0d0 :stress-measure :cauchy
   :cohesion-points '((0d0 30000d0) (.02d0 15000d0)) :peak-kappa .02d0
   :strain-assumption "Wang2017 signed spatial Ep with incremental polar corotation; monotonic scope; explicit composite hydrostatic-apex volumetric flow gA=p, not strict psi0 or exact paper finite-strain formulation"))

(defclass particle-wang2017-soil2-apex (native:particle-wang2017-soil2) ()
  (:default-initargs :evolution-law (make-soil2-apex-law))
  (:documentation "Opt-in Soil2 composite apex extension: psi0 shear plus volumetric gA=p at the hydrostatic apex; not an unchanged paper material."))

(defmethod native:native-material-variant ((mp particle-wang2017-soil2-apex))
  "composite-apex")

(defmethod native:project-point-variant ((variant (eql :composite-apex)) trial e nu j history basis)
  (project-paper-principal-with-apex trial e nu j history basis))

(defmethod native:project-native-point ((mp particle-wang2017-soil2-apex) trial e nu j history basis)
  (native:project-point-variant :composite-apex trial e nu j history basis))
