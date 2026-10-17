(in-package :cl-mpm/particle)

(declaim #.cl-mpm/settings:*optimise-setting*)



(defclass particle-dp (particle-mc)
  ())


(defmethod constitutive-model ((mp particle-dp) strain dt)
  "Strain intergrated elsewhere, just using elastic tensor"
  (with-accessors ((de mp-elastic-matrix)
                   (stress mp-stress)
                   (E mp-E)
                   (nu mp-nu)
                   (p-mod mp-p-modulus)
                   (def mp-deformation-gradient)
                   (phi mp-phi)
                   (psi mp-psi)
                   (c mp-c)
                   (plastic-strain mp-strain-plastic)
                   (ps-vm mp-strain-plastic-vm)
                   (strain mp-strain)
                   (yield-func mp-yield-func)
                   (soft mp-softening)
                   (enabled mp-enable-plasticity)
                   )
      mp
    (declare (double-float soft ps-vm E nu phi psi c))
    ;;Train elastic strain - plus trail kirchoff stress
    (cl-mpm/constitutive::linear-elastic-mat strain de stress)
    (when enabled
      (multiple-value-bind (sig eps-e f yield)
          (cl-mpm/constitutive::plastic-dp stress de strain E nu phi psi c)
          ;; (cl-mpm/ext::constitutive-drucker-prager strain de E nu phi psi c)
        (if yield
            (progn
              (setf stress sig
                    plastic-strain (cl-mpm/fastmaths:fast-.- strain eps-e)
                    yield-func f
                    )
              (setf strain eps-e))
          (progn
            (cl-mpm/fastmaths:fast-zero plastic-strain)
            (setf yield-func 0d0))))
      (incf ps-vm
            (multiple-value-bind (l v)
                (cl-mpm/utils:eig (cl-mpm/utils:voigt-to-matrix (cl-mpm/particle::mp-strain-plastic mp)))
              (destructuring-bind (s1 s2 s3) l
                (sqrt
                 (/ (+ (expt (- s1 s2) 2d0)
                       (expt (- s2 s3) 2d0)
                       (expt (- s3 s1) 2d0)
                       ) 2d0))))))
    (let ((K (/ e (* 3 (- 1d0 (* 2 nu)))))
          (G (/ e (* 2 (+ 1d0 nu)))))
      (declare (double-float K G p-mod))
      (when (> (cl-mpm/particle::mp-yield-func mp) 0d0)
        (setf K (* K (cos (cl-mpm/particle::mp-phi mp))))
        (setf G (* G (sin (cl-mpm/particle::mp-phi mp)))))
      (setf p-mod (* (expt (cl-mpm/fastmaths::det def) -2) (+ K (* 4/3 G)))))
    (when (> soft 0d0)
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
           phi (atan (+ (tan phi-r) (* (- (tan phi-0) (tan phi-r)) (exp (- (* soft ps-vm)))))))))
    stress))

;; (defmethod new-loadstep-mp ((mp particle-plastic))
;;   (with-accessors ((strain cl-mpm/particle:mp-strain)
;;                    (strain-n cl-mpm/particle:mp-strain-n)
;;                    (disp cl-mpm/particle::mp-displacement)
;;                    (def    cl-mpm/particle:mp-deformation-gradient)
;;                    (def-0 cl-mpm/particle::mp-deformation-gradient-0)
;;                    (df-inc    cl-mpm/particle::mp-deformation-gradient-increment)
;;                    )
;;       mp
;;     (cl-mpm/utils:matrix-copy-into def def-0)
;;     (cl-mpm/utils:matrix-copy-into (cl-mpm/utils:matrix-eye 1d0) df-inc)
;;     (cl-mpm/utils:voigt-copy-into strain strain-n)
;;     (cl-mpm/fastmaths:fast-zero disp)
;;     (break)
;;     ))
