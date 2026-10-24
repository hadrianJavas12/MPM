;;;; Opt-in literal signed history on the exactly constant residual strength tail.
(in-package :cl-mpm/models/wang2017-apex)

(defun make-soil2-apex-residual-law ()
  "Same numerical law and apex flow; extend history scope only on its residual tail."
  (mc-evolution:make-evolution-law
   :variant :hs :points '((0d0 35d0)) :psi 0d0 :stress-measure :cauchy
   :cohesion-points '((0d0 30000d0) (.02d0 15000d0)) :peak-kappa .02d0
   :strain-assumption "Wang signed spatial Ep with incremental polar corotation and explicit volumetric apex flow; residual-only signed-history reversal with exactly unchanged strength, no maximum/healing; not an exact paper finite-strain formulation"))

(defclass particle-wang2017-soil2-apex-residual (particle-wang2017-soil2-apex) ()
  (:default-initargs :evolution-law (make-soil2-apex-residual-law))
  (:documentation "Explicit history-scope extension: literal signed kps may decrease only within the exactly constant residual-strength tail. Strict and original apex defaults stay unchanged."))

(defmethod native:native-material-variant ((mp particle-wang2017-soil2-apex-residual))
  "composite-apex-residual")

(defmethod native:native-history-policy ((mp particle-wang2017-soil2-apex-residual))
  "Residual-tail-only signed-history reversal with exactly unchanged law values; original1e-13 roundoff guard elsewhere; no max or strength recovery")

(defmethod native:project-point-variant ((variant (eql :composite-apex-residual))
                                       trial e nu j history basis)
  (project-paper-principal-with-apex trial e nu j history basis))

(defmethod native:project-native-point ((mp particle-wang2017-soil2-apex-residual)
                                      trial e nu j history basis)
  (native:project-point-variant :composite-apex-residual trial e nu j history basis))

(defmethod native:validate-history-transition ((variant (eql :composite-apex-residual)) old new)
  (if (< new (- old native::+history-decrease-tolerance+))
      (let* ((law (make-soil2-apex-residual-law))
             (tail (car (last (mc-evolution:law-breakpoints law)))))
        ;; No tolerance is added at the plateau boundary or to strength equality.
        ;; The actual tensor-derived history is retained; no max is constructed.
        (unless (and (>= old tail) (>= new tail)
                     (equalp (multiple-value-list (mc-evolution:law-values law old))
                             (multiple-value-list (mc-evolution:law-values law new))))
          (call-next-method)))
      (call-next-method)))
