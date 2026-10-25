;;;; Optional subclass; reuse the complete owned MC native transaction.
(in-package :cl-mpm/models/mc-composite-apex)

(defun %reference-law ()
  "Explicit default only; benchmark cases supply their own reduced law."
  (mc:make-evolution-law
   :variant :perfect :points '((0d0 20d0)) :cohesion 10000d0
   :psi 0d0 :stress-measure :cauchy
   :strain-assumption "Existing accumulated J2 increment; perfect MC psi0 shear with explicit additional hydrostatic-apex volumetric flow g_A=p"))

(defclass particle-mc-composite-apex (mc:particle-mc-evolution) ()
  (:default-initargs :evolution-law (%reference-law))
  (:documentation "Opt-in perfect Cauchy MC with additional g_A=p apex flow.
Regular shear remains psi0, but apex plastic volume is positive. This is an
explicit constitutive extension, not unchanged strict MC or a Soil2 model."))

(defmethod initialize-instance :around
    ((mp particle-mc-composite-apex) &rest initargs
     &key e nu evolution-law (kappa 0d0) &allow-other-keys)
  (declare (ignore initargs))
  ;; Run before inherited elastic initialization performs its divisions.
  (%checked-material-parameters e nu evolution-law kappa)
  (call-next-method))

(defmethod reinitialize-instance :around
    ((mp particle-mc-composite-apex) &rest initargs
     &key (e nil e-p) (nu nil nu-p) (evolution-law nil law-p)
       (kappa nil kappa-p) &allow-other-keys)
  (declare (ignore initargs))
  ;; Validate prospective values without changing an existing owned state.
  (%checked-material-parameters
   (if e-p e (cl-mpm/particle::mp-E mp))
   (if nu-p nu (cl-mpm/particle::mp-nu mp))
   (if law-p evolution-law (mc:particle-evolution-law mp))
   (if kappa-p kappa (mc:particle-kappa mp)))
  (call-next-method))

(defmethod mc:project-particle-principal
    ((mp particle-mc-composite-apex) trial e nu j law old-kappa)
  (project-principal-with-apex trial e nu j law old-kappa))

(defun particle-last-apex-active (mp)
  "Last accepted return mode, retained after load-step commit; a Boolean."
  (let ((last (mc:particle-last-projection mp)))
    (and (typep last 'apex-projection)
         (eq (apex-projection-branch last) :hydrostatic-apex))))

(defun particle-last-apex-multiplier (mp)
  "Actual last lambda_A=q, separate from six shear multipliers; zero otherwise."
  (if (particle-last-apex-active mp)
      (apex-projection-apex-multiplier (mc:particle-last-projection mp))
      0d0))
