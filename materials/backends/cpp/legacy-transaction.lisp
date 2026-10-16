(in-package :cl-mpm/ext)

(declaim (optimize (debug 0) (safety 0) (speed 3)))



;; (sb-ext:restrict-compiler-policy 'speed  3 3)
;; (sb-ext:restrict-compiler-policy 'debug  0 0)
;; (sb-ext:restrict-compiler-policy 'safety 0 0)

(handler-case
    (progn
      (define-foreign-library cl-mpm-cpp
        (:unix "kirchoff.so")
        (t (:default "kirchoff")))

      (use-foreign-library cl-mpm-cpp)


      (defcfun "Kirchoff_Strain_Update" :bool
        (strain-ptr :pointer)
        (df-ptr :pointer))


      (defcfun "CppDruckerPrager" :bool
        (strain-ptr :pointer)
        (E :double)
        (nu :double)
        (phi :double)
        (psi :double)
        (c :double))

      (defcfun "CppMohrCoulomb" :bool
        (strain-ptr :pointer)
        (f-ptr :pointer)
        (ps-ptr :pointer)
        (p-mod-ptr :pointer)
        (E :double)
        (nu :double)
        (phi :double)
        (psi :double)
        (c :double))

      (defcfun "CppViscoelastic" :bool
        (strain-ptr :pointer)
        (E :double)
        (nu :double)
        (viscosity :double)
        (dt :double))


      (defcfun "CppVonMises" :bool
        (strain-ptr :pointer)
        (f-ptr :pointer)
        (ps-ptr :pointer)
        (p-mod-ptr :pointer)
        (E :double)
        (nu :double)
        (rho :double))

      (defcfun "CppVonMisesTangent" :bool
        (strain-ptr :pointer)
        (dep-ptr :pointer)
        (f-ptr :pointer)
        (ps-ptr :pointer)
        (p-mod-ptr :pointer)
        (E :double)
        (nu :double)
        (rho :double))

      (defcfun "MatrixSqrt" :bool
        (input-ptr :pointer)
        (output-ptr :pointer))


      (defcfun "dr_make_sim" :bool
        (h :double)
        (e-x :int)
        (e-y :int)
        (e-z :int))

      (defcfun "dr_make_mp" :bool
        (position :pointer)
        (strain_n :pointer)
        (de :pointer)
        (l_n :pointer)
        )

      (defcfun "test" :void
        (flags :pointer))
      (format t "~&Using accelerated kirchoff update~%")
      (defun kirchoff-expt-step (strain-matrix df-matrix)
        (magicl.cffi-types:with-array-pointers ((sp (magicl::matrix/double-float-storage strain-matrix))
                                                (dfp (magicl::matrix/double-float-storage df-matrix)))
          (unless (kirchoff-strain-update sp dfp)
            (error "Kirchoff strain update failed - eigensolver error ~A ~A" strain-matrix df-matrix)))
        (values))

      (defun constitutive-drucker-prager (stress strain de E nu phi psi c)
        (declare (double-float E nu phi psi c))
        (let ((str (cl-mpm/utils::voigt-copy strain)))
          (magicl.cffi-types:with-array-pointers ((sp (cl-mpm/utils:fast-storage strain)))
            (unless (CppDruckerPrager sp E nu phi psi c)
              (error "Drucker-Prager failed")))
          (cl-mpm/fastmaths::@-tensor-voigt-lisp de strain stress)
          (values stress
                  strain
                  0d0
                  ;; 0d0
                  (cl-mpm/fastmaths::voigt-j2
                   (cl-mpm/utils::deviatoric-voigt
                    (cl-mpm/fastmaths:fast-.- str strain)))
                  (cl-mpm/utils::calculate-p-wave-modulus E nu))))

      (defun constitutive-vm (stress strain de E nu rho)
        (declare (double-float E nu rho))
        (static-vectors:with-static-vector (f-arr 1 :element-type 'double-float)
          (static-vectors:with-static-vector (ps-arr 1 :element-type 'double-float)
            (static-vectors:with-static-vector (p-mod-arr 1 :element-type 'double-float)
              (magicl.cffi-types:with-array-pointers ((sp (cl-mpm/utils:fast-storage strain))
                                                      (f-arr-p f-arr)
                                                      (ps-arr-p ps-arr)
                                                      (p-mod-arr-p p-mod-arr)
                                                      )
                (if (CppVonMises sp f-arr-p ps-arr-p p-mod-arr-p E nu rho)
                    (progn
                      (values (cl-mpm/fastmaths::fast-@-tensor-voigt de strain stress)
                              strain
                              (aref f-arr 0)
                              (aref ps-arr 0)
                              (aref p-mod-arr 0)))
                    (values stress
                            strain
                            (aref f-arr 0)
                            (aref ps-arr 0)
                            (aref p-mod-arr 0))))))))

      (defun constitutive-vm-tangent (stress strain de E nu rho dep)
        (declare (double-float E nu rho))
        (static-vectors:with-static-vector (f-arr 1 :element-type 'double-float)
          (static-vectors:with-static-vector (ps-arr 1 :element-type 'double-float)
            (static-vectors:with-static-vector (p-mod-arr 1 :element-type 'double-float)
              (magicl.cffi-types:with-array-pointers ((sp (cl-mpm/utils:fast-storage strain))
                                                      (depp (cl-mpm/utils:fast-storage dep))
                                                      (f-arr-p f-arr)
                                                      (ps-arr-p ps-arr)
                                                      (p-mod-arr-p p-mod-arr))
                (if (CppVonMisesTangent sp depp f-arr-p ps-arr-p p-mod-arr-p E nu rho)
                    (progn
                      (values (cl-mpm/fastmaths::fast-@-tensor-voigt de strain stress)
                              strain
                              (aref f-arr 0)
                              (aref ps-arr 0)
                              (aref p-mod-arr 0)))
                    (values stress
                            strain
                            (aref f-arr 0)
                            (aref ps-arr 0)
                            (aref p-mod-arr 0))))))))

      (defun constitutive-mohr-coulomb (stress de strain E nu phi psi c)
        "Mohr-coulomb, in-place update strain, return a new stress, yield function and ps inc"
        (declare (double-float E nu phi psi c))
        (let ((str
                strain
                ;; (cl-mpm/utils::voigt-copy strain)
                )
              )
          (static-vectors:with-static-vector (f-arr 1 :element-type 'double-float)
            (static-vectors:with-static-vector (ps-arr 1 :element-type 'double-float)
              (static-vectors:with-static-vector (p-mod-arr 1 :element-type 'double-float)
                (magicl.cffi-types:with-array-pointers ((sp (cl-mpm/utils:fast-storage str))
                                                        (f-arr-p f-arr)
                                                        (ps-arr-p ps-arr)
                                                        (p-mod-arr-p p-mod-arr)
                                                        )
                  (if (CppMohrCoulomb sp f-arr-p ps-arr-p p-mod-arr-p E nu phi psi c)
                      (progn
                        (values (cl-mpm/fastmaths::fast-@-tensor-voigt de str stress)
                                str
                                (aref f-arr 0)
                                (aref ps-arr 0)
                                (aref p-mod-arr 0)))
                      (values stress
                              strain
                              (aref f-arr 0)
                              (aref ps-arr 0)
                              (aref p-mod-arr 0))))))))
        )
      (defun constitutive-viscoelastic (stress strain de E nu dt viscosity)
        "Mohr-coulomb, in-place update strain, return a new stress, yield function and ps inc"
        (declare (double-float E nu viscosity dt))
        (magicl.cffi-types:with-array-pointers ((sp (cl-mpm/utils:fast-storage strain)))
          (if (CppViscoelastic sp E nu viscosity dt)
              (progn
                (cl-mpm/constitutive::linear-elastic-mat strain de stress)
                ;; (cl-mpm/fastmaths::fast-@-tensor-voigt de strain stress)
                strain)
              strain)))
      (defun matrix-sqrt (mat)
        (let ((output (cl-mpm/utils:matrix-zeros)))
          (magicl.cffi-types:with-array-pointers ((sp (cl-mpm/utils:fast-storage mat))
                                                  (sp-out (cl-mpm/utils:fast-storage output)))
            (MatrixSqrt sp sp-out))
          output)))

    (cffi::load-foreign-library-error (c)
      (progn
        (format t "~&~A~%" c)
        (format t "~&No accelerated kirchoff update~%")
        ;;Use a lisp fallback
        (defun kirchoff-expt-step (strain df)
          (kirchoff-expt-step-lisp strain df))
        (defun constitutive-drucker-prager (stress de strain E nu phi psi c)
          (cl-mpm/constitutive::mc-plastic stress
                                           de
                                           strain
                                           E
                                           nu
                                           phi
                                           psi
                                           c))
        (defun constitutive-mohr-coulomb (stress de strain E nu phi psi c)
          (cl-mpm/constitutive::mc-plastic stress
                                           de
                                           strain
                                           E
                                           nu
                                           phi
                                           psi
                                           c))
        (defun constitutive-viscoelastic (stress de strain E nu dt viscosity))
        (defun matrix-sqrt (mat)
          (multiple-value-bind (l v) (cl-mpm/utils::eig mat)
            (magicl:@
             v
             (cl-mpm/utils::matrix-from-list
              (list (the double-float (sqrt (the double-float (nth 0 l)))) 0d0 0d0
                    0d0 (the double-float (sqrt (the double-float (nth 1 l)))) 0d0
                    0d0 0d0 (the double-float (sqrt (the double-float (nth 2 l))))))
             (magicl:transpose v))
            )))))
