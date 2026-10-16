(in-package :cl-mpm/constitutive)

(declaim #.cl-mpm/settings:*optimise-setting*)



(declaim (ftype (function (double-float double-float) double-float) vm-yield-func))
(defun vm-yield-func (j2 rho)
  (declare (double-float j2 rho))
  (- (/ (the double-float (sqrt (* 2d0 j2))) rho) 1d0))

(defun vm-derivatives (sig rho)
  (declare (double-float rho))
  (let* ((s (deviatoric-voigt sig))
         (j2 (the double-float (voigt-j2 s)))
         (dj2 (cl-mpm/fastmaths::fast-.* s (cl-mpm/utils::voigt-from-list '(1d0 1d0 1d0 2d0 2d0 2d0))))
         (ddj2 (magicl:block-matrix (list
                                     (magicl:.- (magicl:eye 3) (magicl:const (/ 1d0 3d0) '(3 3)))
                                     (magicl:zeros '(3 3))
                                     (magicl:zeros '(3 3))
                                     (magicl:eye 3 :value 2d0)) '(2 2)))
         (df (magicl:scale dj2 (the double-float (/ 1d0 (the double-float (* rho (the double-float (sqrt (the double-float (* 2d0 j2))))))))))
         (ddf (magicl:scale!
               (magicl:.-
                (magicl:scale ddj2 (/ 1d0 (the double-float (sqrt (* 2d0 j2)))))
                (magicl:scale! (magicl:@ dj2 (magicl:transpose dj2)) (/ 1d0 (the double-float (expt (* 2d0 j2) 3/2))))
                )
               (/ 1d0 rho))))
    (values df ddf)))
(defun vm-plastic (stress de trial-elastic-strain rho e nu)
  (declare (double-float e nu rho))
  (let* ((tol 1d-9)
         (max-iter 5)
         ;; (sig stress)
         (sig (cl-mpm/utils::voigt-copy stress))
         (s (deviatoric-voigt stress))
         (j2 (voigt-j2 s))
         (f (vm-yield-func j2 rho))
         (inc 0d0)
         (K (/ e (* 3 (- 1d0 (* 2 nu)))))
         (G (/ e (* 2 (+ 1d0 nu))))
         (p-mod (+ K (* 4/3 G))))
    (declare (dynamic-extent s ))
    (if (> f tol)
      (let ((eps-e (cl-mpm/utils::voigt-copy trial-elastic-strain))
            (df (cl-mpm/utils:voigt-zeros))
            (ddf (cl-mpm/utils:matrix-zeros)))
        ;; (declare (dynamic-extent df ddf))
        (multiple-value-bind (ndf nddf) (vm-derivatives sig rho)
          (setf df ndf
                ddf nddf))
        ;;Plastic deformation is occuring
        (let* ((b (magicl:from-list (list 0d0 0d0 0d0 0d0 0d0 0d0 f) '(7 1) :type 'double-float))
               (dgam 0d0))
          (loop for iters from 0 to max-iter
                when (or (> (b-norm b) tol)
                         (> (abs (varef b 6)) tol))
                  do
                     (progn
                       ;;Calculate backstress
                       (let* ((A (magicl:block-matrix
                                  (list
                                   (cl-mpm/fastmaths::fast-.+ (magicl:eye 6)
                                              (magicl:scale! (magicl:@ ddf de) dgam))
                                   df
                                   (magicl:@ (magicl:transpose df) de)
                                   (magicl:zeros '(1 1))
                                   )
                                  '(2 2)
                                  ))
                              (dx (magicl:scale! (magicl:@ (magicl:inv A) b) -1d0)))
                         ;;Add just the 6 components of stress
                         (loop for i from 0 below 6
                               do (incf (varef eps-e i) (varef dx i)))
                         (incf dgam (varef dx 6))
                         (setf sig (magicl:@ de eps-e))
                         (setf s (deviatoric-voigt sig))
                         (setf j2 (voigt-j2 s))
                         (setf f (vm-yield-func j2 rho))
                         (multiple-value-bind (ndf nddf) (vm-derivatives sig rho)
                           (setf df ndf
                                 ddf nddf))
                         (let ((b-eps (cl-mpm/fastmaths::fast-.+
                                       (cl-mpm/fastmaths::fast-.+ eps-e (magicl:scale trial-elastic-strain -1d0))
                                       (magicl:scale! df dgam)))
                               (b-f (vm-yield-func j2 rho)))
                           (loop for i from 0 below 6
                                 do (setf (magicl:tref b i 0) (magicl:tref b-eps i 0)))
                           (setf (magicl:tref b 6 0) b-f)))
                       ))
          (setf inc (the double-float
                           (cl-mpm/fastmaths::voigt-von-mises
                            (cl-mpm/fastmaths::fast-.--voigt
                             eps-e
                             trial-elastic-strain))))
          (values sig eps-e f inc K)
          ))
      (values sig trial-elastic-strain f inc p-mod))))

(defun plastic-vm-tangent (stress de trial-elastic-strain rho e nu)
  (declare (double-float e nu rho))
  (let* ((trial-elastic-strain (swizzle-voigt->coombs trial-elastic-strain))
         (stress (magicl:@ de trial-elastic-strain)))
    (let* ((tol 1d-9)
           (max-iter 5)
           ;; (sig stress)
           (sig (cl-mpm/utils::voigt-copy stress))
           (s (deviatoric-voigt sig))
           (j2 (voigt-j2 s))
           (f (vm-yield-func j2 rho))
           (inc 0d0)
           (K (/ e (* 3 (- 1d0 (* 2 nu)))))
           (G (/ e (* 2 (+ 1d0 nu))))
           (p-mod (+ K (* 4/3 G)))
           (dep (cl-mpm/utils::deep-copy de)))
      (declare (dynamic-extent s ))
      (if (> f tol)
          (let ((eps-e (cl-mpm/utils::voigt-copy trial-elastic-strain))
                (df (cl-mpm/utils:voigt-zeros))
                (ddf (cl-mpm/utils:matrix-zeros)))
            ;; (declare (dynamic-extent df ddf))
            (multiple-value-bind (ndf nddf) (vm-derivatives sig rho)
              (setf df ndf
                    ddf nddf))
            ;;Plastic deformation is occuring
            (let* ((b (magicl:from-list (list 0d0 0d0 0d0 0d0 0d0 0d0 f) '(7 1) :type 'double-float))
                   (dgam 0d0))
              (loop for iters from 0 to max-iter
                    when (or (> (b-norm b) tol)
                             (> (abs (varef b 6)) tol))
                      do
                         (progn
                           ;;Calculate backstress
                           (let* ((A (magicl:block-matrix
                                      (list
                                       (cl-mpm/fastmaths::fast-.+ (magicl:eye 6)
                                                                  (magicl:scale! (magicl:@ ddf de) dgam))
                                       df
                                       (magicl:@ (magicl:transpose df) de)
                                       (magicl:zeros '(1 1))
                                       )
                                      '(2 2)
                                      ))
                                  (dx (magicl:scale! (magicl:@ (magicl:inv A) b) -1d0)))
                             ;;Add just the 6 components of stress
                             (loop for i from 0 below 6
                                   do (incf (varef eps-e i) (varef dx i)))
                             (incf dgam (varef dx 6))
                             (setf sig (magicl:@ de eps-e))
                             (setf s (deviatoric-voigt sig))
                             (setf j2 (voigt-j2 s))
                             (setf f (vm-yield-func j2 rho))
                             (multiple-value-bind (ndf nddf) (vm-derivatives sig rho)
                               (setf df ndf
                                     ddf nddf))
                             (let ((b-eps (cl-mpm/fastmaths::fast-.+
                                           (cl-mpm/fastmaths::fast-.+ eps-e (magicl:scale trial-elastic-strain -1d0))
                                           (magicl:scale df dgam)))
                                   (b-f (vm-yield-func j2 rho)))
                               (loop for i from 0 below 6
                                     do (setf (magicl:tref b i 0) (magicl:tref b-eps i 0)))
                               (setf (magicl:tref b 6 0) b-f)))))
              ;; (pprint
              ;;  (magicl:block-matrix
              ;;   (list
              ;;    (cl-mpm/fastmaths::fast-.+
              ;;     (magicl:inv De)
              ;;     (magicl:scale ddf dgam))
              ;;    df
              ;;    (magicl:transpose df)
              ;;    (magicl:from-diag (list 0d0)))
              ;;   (list 2 2))
              ;;  )
              (let ((B (magicl:inv
                        (magicl:block-matrix
                         (list
                          (cl-mpm/fastmaths::fast-.+
                           (magicl:inv De)
                           (magicl:scale! ddf dgam))
                          df
                          (magicl:transpose df)
                          (magicl:from-diag (list 0d0)))
                         (list 2 2)))))
                ;; (pprint B)
                (setf dep (magicl:slice B '(0 0) '(6 6))))
              (setf inc (the double-float
                             (cl-mpm/fastmaths::voigt-von-mises
                              (cl-mpm/fastmaths::fast-.--voigt
                               eps-e
                               trial-elastic-strain))))
              (values (swizzle-coombs->voigt sig)
                      (swizzle-coombs->voigt eps-e)
                      f inc K dep)
              ))
          (values (swizzle-coombs->voigt sig)
                  (swizzle-coombs->voigt trial-elastic-strain) f inc p-mod
                  (cl-mpm/utils::deep-copy de))))))
