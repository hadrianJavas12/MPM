(in-package :cl-mpm/particle)

(declaim #.cl-mpm/settings:*optimise-setting*)



(defclass particle-mc (particle-elastic particle-plastic)
  ((phi
    :accessor mp-phi
    :initarg :phi
    :initform 0d0
    )
   (psi
    :accessor mp-psi
    :initarg :psi
    :initform 0d0
    )
   (c
    :accessor mp-c
    :initarg :c
    :initform 0d0
    )
   (phi-0
    :accessor mp-phi-0
    :initarg :phi
    :initform 0d0
    )
   (psi-0
    :accessor mp-psi-0
    :initarg :psi
    :initform 0d0
    )
   (c-0
    :accessor mp-c-0
    :initarg :c
    :initform 0d0
    )
   (phi-r
    :accessor mp-phi-r
    :initarg :phi-r
    :initform 0d0
    )
   (psi-r
    :accessor mp-psi-r
    :initarg :psi-r
    :initform 0d0
    )
   (c-r
    :accessor mp-c-r
    :initarg :c-r
    :initform 0d0
    )
   )

  (:documentation "A mohr-coloumb perfectly plastic material point"))

(defmethod constitutive-model ((mp particle-mc) strain dt)
  "Strain intergrated elsewhere, just using elastic tensor"
  (with-accessors ((de mp-elastic-matrix)
                   (stress mp-stress)
                   (E mp-E)
                   (nu mp-nu)
                   (phi mp-phi)
                   (psi mp-psi)
                   (c mp-c)
                   (plastic-strain mp-strain-plastic)
                   (ps-vm mp-strain-plastic-vm)
                   (ps-vm-1 mp-strain-plastic-vm-1)
                   (ps-vm-inc mp-strain-plastic-vm-inc)
                   (strain mp-strain)
                   (yield-func mp-yield-func)
                   (soft mp-softening)
                   (p-mod mp-p-modulus)
                   (def mp-deformation-gradient)
                   (enabled mp-enable-plasticity)
                   (p-wave-0 cl-mpm/particle::mp-p-modulus-0)
                   )
      mp
    (declare (double-float soft ps-vm ps-vm-1 ps-vm-inc E nu phi psi c))
    ;;Train elastic strain - plus trail kirchoff stress

    ;; (setf p-mod
    ;;       (* (expt (cl-mpm/fastmaths::det def) -2)
    ;;                (cl-mpm/particle::compute-p-modulus mp)))
    (setf p-wave-0 (cl-mpm/particle::compute-p-modulus mp))
    (setf stress (cl-mpm/constitutive::linear-elastic-mat strain de stress))
    (when enabled
      (let ((f-r t)
            (ps-inc-i 0d0))
        (loop for i from 0 to 0;to 50
              while (and f-r
                         ;; (if (= ps-inc-i 0d0)
                         ;;     t
                         ;;     (/ (abs (- ps-vm-inc ps-inc-i)) ps-inc-i))
                         )
              do
                 (progn
                   (setf ps-inc-i ps-vm-inc)
                   (multiple-value-bind (sig eps-e f inc pmod)
                       (cl-mpm/ext::constitutive-mohr-coulomb stress
                                                              de
                                                              strain
                                                              E
                                                              nu
                                                              phi
                                                              psi
                                                              c)
                       ;; (cl-mpm/constitutive::mc-plastic stress
                       ;;                                 de
                       ;;                                 strain
                       ;;                                 E
                       ;;                                 nu
                       ;;                                 phi
                       ;;                                 psi
                       ;;                                 c)
                     (declare (double-float f inc))
                     (setf f-r (> f 1d-5))
                     (setf
                      stress sig
                      strain eps-e
                      yield-func f
                      p-wave-0 pmod)
                     (setf ps-vm-inc inc)
                     (setf ps-vm (+ ps-vm-1 inc)))
                   (setf (mp-plastic-iterations mp) i)
                   ;; (let ((K (/ e (* 3 (- 1d0 (* 2 nu)))))
                   ;;       (G (/ e (* 2 (+ 1d0 nu)))))
                   ;;   (declare (double-float K G p-mod))
                   ;;   (when (> (cl-mpm/particle::mp-yield-func mp) 0d0)
                   ;;     (setf K (* K (cos (cl-mpm/particle::mp-phi mp))))
                   ;;     (setf G (* G (sin (cl-mpm/particle::mp-phi mp))))
                   ;;     (setf p-wave-0 (* (+ K (* 4/3 G))))))
                   (when soft
                     (unless (= soft 0d0)
                       (with-accessors ((c-0 mp-c-0)
                                        (phi-0 mp-phi-0)
                                        (psi-0 mp-psi-0)
                                        (c-r mp-c-r)
                                        (phi-r mp-phi-r)
                                        (psi-r mp-psi-r))
                           mp
                         (declare (double-float c-0 c-r phi-0 phi-r psi-0 psi-r))
                         (setf
                          c (+ c-r (* (- c-0 c-r) (exp (- (* soft ps-vm)))))
                          phi (atan (+ (tan phi-r) (* (- (tan phi-0) (tan phi-r)) (exp (- (* soft ps-vm))))))))
                       ))))))
    ;; (cl-mpm/particle::update-p-modulus mp)
    stress))
