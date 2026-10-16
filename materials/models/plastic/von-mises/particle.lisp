(in-package :cl-mpm/particle)

(declaim #.cl-mpm/settings:*optimise-setting*)



(defclass particle-vm (particle-elastic particle-plastic)
  ((rho
    :accessor mp-rho
    :initarg :rho
    )
   (rho-0
    :accessor mp-rho-0
    :initarg :rho
    )
   (rho-r
    :accessor mp-rho-r
    :initarg :rho-r
    )
   (yield-func
    :accessor mp-yield-func
    :type double-float
    :initform 0d0))
  (:documentation "A vm perfectly plastic material point"))

(defclass particle-vm-implicit (particle-vm)
  ()
  (:documentation "A vm perfectly plastic material point, except stores the algorithmic tangent"))

(defclass particle-vm-hardening (particle-vm)
  ()
  (:documentation "A VM plastic material point, with a secant hardening/softening algorithm"))

(defmethod constitutive-model ((mp particle-vm) strain dt)
  "Strain intergrated elsewhere, just using elastic tensor"
  (with-accessors ((de mp-elastic-matrix)
                   (dep mp-tangent-stiffness)
                   (stress mp-stress)
                   (rho mp-rho)
                   (soft mp-softening)
                   (plastic-strain mp-strain-plastic)
                   (ps-vm mp-strain-plastic-vm)
                   (ps-vm-1 mp-strain-plastic-vm-1)
                   (ps-vm-inc mp-strain-plastic-vm-inc)
                   (strain mp-strain)
                   (strain-n mp-strain-n)
                   (yield-func mp-yield-func)
                   (def mp-deformation-gradient)
                   (p-mod mp-p-modulus-0)
                   (E mp-e)
                   (nu mp-nu)
                   (enable-plasticity mp-enable-plasticity))
      mp
    (declare (double-float soft))
    ;;Train elastic strain - plus trail kirchoff stress
    (cl-mpm/constitutive::linear-elastic-mat strain de stress)
    (setf p-mod (cl-mpm/particle::compute-p-modulus mp))
    ;; (setf dep de)
    (when enable-plasticity
      (progn
        (multiple-value-bind (sig eps-e f inc pmod) (cl-mpm/ext::constitutive-vm stress strain de e nu rho)
          (declare (double-float f inc pmod ps-vm-1 ps-vm-inc))
          (setf stress sig
                ;; plastic-strain (cl-mpm/fastmaths:fast-.- strain eps-e plastic-strain)
                p-mod pmod
                yield-func f)
          (setf ps-vm-inc inc)
          (setf strain eps-e)
          (setf ps-vm (+ ps-vm-1 ps-vm-inc))
          ))
      )
    (when (> soft 0d0)
      (with-accessors ((rho-r mp-rho-r)
                       (rho-0 mp-rho-0))
          mp
        (declare (double-float rho-0 rho-r))
        (setf
         rho (+ rho-r (* (- rho-0 rho-r) (exp (- (* soft ps-vm))))))))
    stress))

(defmethod constitutive-model ((mp particle-vm-hardening) strain dt)
  "Strain intergrated elsewhere, just using elastic tensor"
  (with-accessors ((de mp-elastic-matrix)
                   (dep mp-tangent-stiffness)
                   (stress mp-stress)
                   (rho mp-rho)
                   (soft mp-softening)
                   (plastic-strain mp-strain-plastic)
                   (ps-vm mp-strain-plastic-vm)
                   (ps-vm-1 mp-strain-plastic-vm-1)
                   (ps-vm-inc mp-strain-plastic-vm-inc)
                   (strain mp-strain)
                   (strain-n mp-strain-n)
                   (yield-func mp-yield-func)
                   (def mp-deformation-gradient)
                   (p-mod mp-p-modulus-0)
                   (E mp-e)
                   (nu mp-nu)
                   (rho-r mp-rho-r)
                   (rho-0 mp-rho-0)
                   (enable-plasticity mp-enable-plasticity))
      mp
    (declare (double-float soft))
    ;;Train elastic strain - plus trail kirchoff stress
    (cl-mpm/constitutive::linear-elastic-mat strain de stress)
    (setf p-mod (cl-mpm/particle::compute-p-modulus mp))
    ;; (setf dep de)
    (when enable-plasticity
      (let ((new-stress (cl-mpm/utils:voigt-zeros))
            (new-strain (cl-mpm/utils:voigt-zeros)))
        (labels ((plastic (plastic-vm)
                   ;; (setf
                   ;;  rho (+ rho-r (* (- rho-0 rho-r) (exp (- (* soft plastic-vm))))))
                   (setf
                    rho (+ rho-0 (* soft plastic-vm)))
                   (cl-mpm/utils:voigt-copy-into stress new-stress)
                   (cl-mpm/utils:voigt-copy-into strain new-strain)
                   (multiple-value-bind (sig eps-e f inc pmod)
                       (cl-mpm/ext::constitutive-vm
                        new-stress
                        new-strain
                        de e nu rho)
                     (setf
                      new-stress sig
                      new-strain eps-e
                      p-mod pmod
                      yield-func f
                      ps-vm-inc inc
                      ps-vm (+ ps-vm-1 inc))
                     inc)))
          (cl-mpm/constitutive::secant-hardening
           #'plastic
           ps-vm-1
           #'identity))
        (cl-mpm/utils::voigt-copy-into new-stress stress)
        (cl-mpm/utils::voigt-copy-into new-strain strain))

      ;; (progn
      ;;   (multiple-value-bind (sig eps-e f inc pmod) (cl-mpm/ext::constitutive-vm stress strain de e nu rho)
      ;;     (declare (double-float f inc pmod ps-vm-1 ps-vm-inc))
      ;;     (setf stress sig
      ;;           ;; plastic-strain (cl-mpm/fastmaths:fast-.- strain eps-e plastic-strain)
      ;;           p-mod pmod
      ;;           yield-func f)
      ;;     (setf ps-vm-inc inc)
      ;;     (setf strain eps-e)
      ;;     (setf ps-vm (+ ps-vm-1 ps-vm-inc))
      ;;     ))
      )
    stress))


(defmethod constitutive-model ((mp particle-vm-implicit) strain-in dt)
  "Strain intergrated elsewhere, just using elastic tensor"
  (with-accessors ((de mp-elastic-matrix)
                   (dep mp-tangent-stiffness)
                   (stress mp-stress-kirchoff)
                   (rho mp-rho)
                   (soft mp-softening)
                   (plastic-strain mp-strain-plastic)
                   (ps-vm mp-strain-plastic-vm)
                   (ps-vm-1 mp-strain-plastic-vm-1)
                   (ps-vm-inc mp-strain-plastic-vm-inc)
                   (strain mp-strain)
                   (strain-n mp-strain-n)
                   (yield-func mp-yield-func)
                   (def mp-deformation-gradient)
                   (p-mod mp-p-modulus-0)
                   (E mp-e)
                   (nu mp-nu)
                   (enable-plasticity mp-enable-plasticity))
      mp
    ;;Train elastic strain - plus trail kirchoff stress
    (cl-mpm/constitutive::linear-elastic-mat strain de stress)
    (if (equal dep de)
      (setf dep (cl-mpm/utils::deep-copy de))
      (cl-mpm/utils::copy-into de dep))
    (setf p-mod (cl-mpm/particle::compute-p-modulus mp))
    (if enable-plasticity
        (multiple-value-bind (sig eps-e f inc pmod) (cl-mpm/ext::constitutive-vm-tangent
                                                     stress
                                                     strain
                                                     de
                                                     e nu
                                                     rho
                                                     dep)
          (setf stress sig
                ;; plastic-strain (cl-mpm/fastmaths:fast-.- strain eps-e plastic-strain)
                p-mod pmod
                yield-func f)
          (let ((p-mod-elastic (* 1d-6 (cl-mpm/particle::compute-p-modulus mp)))
                (probe-vec (cl-mpm/utils::voigt-zeros)))
            (setf pmod p-mod-elastic)
            (loop for d from 0 below 2
                  do (progn
                       (setf p-mod
                             (max p-mod
                                  (cl-mpm/utils:varef (cl-mpm/fastmaths::fast-@-tensor-voigt dep probe-vec)
                                                      d))))))
          (setf ps-vm-inc inc)
          (setf strain eps-e)
          (setf ps-vm (+ ps-vm-1 ps-vm-inc)))
      (progn
        ;; (setf p-mod (cl-mpm/particle::compute-p-modulus mp))
        ))
    stress))
