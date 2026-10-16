(in-package :cl-mpm/constitutive)

(declaim #.cl-mpm/settings:*optimise-setting*)





(defun mc-yield-func (stress phi c)
  (let* ((k (/ (+ 1d0 (sin phi)) (- 1d0 (sin phi))))
         (sigc (* 2d0 c (sqrt k)))
         (f (- (* k (magicl:tref stress 0 0)) (magicl:tref stress 2 0) sigc)))
    f))

(defun fast-mc (stress phi c)
  (multiple-value-bind (s1 s2 s3) (cl-mpm/utils::principal-stresses-3d stress)
      (mc-yield-func (cl-mpm/utils:vector-from-list (list s1 s2 s3)) phi c)))


;; (defun plastic-dp (trial-elastic-strain de E nu phi psi c)
;;   (cl-mpm/ext::constitutive-drucker-prager trial-elastic-strain de E nu phi psi c))

(declaim (notinline  mc-plastic))
(defun mc-plastic (stress de trial-elastic-strain E nu phi psi c)
  (declare (optimize (speed 3) (safety 0) (debug 0)))
  (declare (double-float E nu phi psi c)
           (magicl:matrix/double-float stress de trial-elastic-strain))
  (let* ((tol 1d-9)
         (initial-f 0d0))
    (let (;(f-dp (dp-yield-mc-circumscribe stress phi c))
          (f-dp (fast-mc stress phi c))
          (pmod (/ (* (- 1d0 nu) E) (* (+ 1d0 nu) (- 1d0 (* 2d0 nu))))))
      ;;Early check for if we should yield - DP eval is much faster?
      (if (> f-dp tol)
          (multiple-value-bind (l v) (cl-mpm/utils::eig (cl-mpm/utils:voigt-to-matrix trial-elastic-strain))
            (let* ((l-sort (sort (mapcar #'cons l (list 0 1 2)) #'> :key #'car))
                   (l (mapcar #'car l-sort))
                   (v (magicl:block-matrix (list
                                            (cl-mpm/utils::matrix-column v (cdr (nth 0 l-sort)))
                                            (cl-mpm/utils::matrix-column v (cdr (nth 1 l-sort)))
                                            (cl-mpm/utils::matrix-column v (cdr (nth 2 l-sort)))) '(1 3))))
              (let* ((De3
                       (cl-mpm/fastmaths::fast-scale!
                        (cl-mpm/utils:matrix-from-list (list
                                                        (- 1d0 nu) nu nu
                                                        nu (- 1d0 nu) nu
                                                        nu nu (- 1d0 nu)))
                        (/ E (* (+ 1d0 nu) (- 1d0 (* 2d0 nu))))))
                     (epsTr (cl-mpm/utils:vector-from-list l))
                     (sig (cl-mpm/utils:@-mat-vec De3 epsTr))
                     (f (mc-yield-func sig phi c))
                     (initial-f f))
                ;; (when (and
                ;;        (> f tol)
                ;;        (not (> f-dp tol)))
                ;;   (error "DP misses mc case ~E ~E" f f-dp))
                (if (> f tol)
                    (let* (
                           (Ce (magicl:inv De3))
                           (eps-e (cl-mpm/utils::vector-copy epsTr))
                           ;; (eps-e epsTr)
                           (k (/ (+ 1 (sin phi)) (- 1d0 (sin phi))))
                           (sigc (* 2d0 c (sqrt k)))
                           (m (/ (+ 1 (sin psi)) (- 1d0 (sin psi))))
                           (siga (magicl:scale!
                                  (cl-mpm/utils:vector-from-list (list 1d0 1d0 1d0))
                                  (/ sigc (- k 1d0))
                                  ))
                           (r1 (vector-from-list (list 1d0 1d0 k)))
                           (r2 (vector-from-list (list 1d0 k k)))
                           (rg1 (vector-from-list (list 1d0 1d0 m)))
                           (rg2 (vector-from-list (list 1d0 m m)))
                           (df (vector-from-list (list k 0d0 -1d0)))
                           (dg (vector-from-list (list m 0d0 -1d0)))
                           (rp (magicl:scale! (cl-mpm/utils:@-mat-vec De3 dg)
                                              (/ 1d0 (the double-float
                                                          (magicl:tref (magicl:@ (magicl:transpose dg) De3 df) 0 0)
                                                          ))))
                           (t1 (/ (magicl:tref (magicl:@ (magicl:transpose rg1) Ce (magicl:.- sig siga)) 0 0)
                                  (magicl:tref (magicl:@ (magicl:transpose rg1) Ce r1) 0 0)))
                           (t2 (/ (magicl:tref (magicl:@
                                                (magicl:transpose rg2)
                                                Ce (magicl:.- sig siga)) 0 0)
                                  (magicl:tref (magicl:@ (magicl:transpose rg2) Ce r2) 0 0)))
                           (f12 (magicl:tref (magicl:@ (magicl:transpose! (cl-mpm/fastmaths::cross-product rp r1))
                                                       (magicl:.- sig siga)) 0 0))
                           (f13 (magicl:tref (magicl:@ (magicl:transpose! (cl-mpm/fastmaths::cross-product rp r2))
                                                       (magicl:.- sig siga)) 0 0))
                           (path :no-return)
                           (Q
                             (magicl:transpose!
                              (magicl:block-matrix
                               (list
                                (cl-mpm/fastmaths::fast-.* (cl-mpm/utils::matrix-column v 0)
                                                           (cl-mpm/utils::matrix-column v 0))

                                (cl-mpm/fastmaths::fast-.* (cl-mpm/utils::matrix-column v 1)
                                                           (cl-mpm/utils::matrix-column v 1))
                                (cl-mpm/fastmaths::fast-.* (cl-mpm/utils::matrix-column v 2)
                                                           (cl-mpm/utils::matrix-column v 2))

                                (magicl:scale!
                                 (cl-mpm/fastmaths::fast-.* (cl-mpm/utils::matrix-column v 0)
                                                            (cl-mpm/utils::matrix-column v 1)) 2d0)
                                (magicl:scale!
                                 (cl-mpm/fastmaths::fast-.* (cl-mpm/utils::matrix-column v 1)
                                                            (cl-mpm/utils::matrix-column v 2)) 2d0)
                                (magicl:scale!
                                 (cl-mpm/fastmaths::fast-.* (cl-mpm/utils::matrix-column v 2)
                                                            (cl-mpm/utils::matrix-column v 0)) 2d0)

                                (cl-mpm/fastmaths::fast-.* (cl-mpm/utils::matrix-column v 0)
                                                           (rotate-vector (cl-mpm/utils::matrix-column v 0)))
                                (cl-mpm/fastmaths::fast-.* (cl-mpm/utils::matrix-column v 1)
                                                           (rotate-vector (cl-mpm/utils::matrix-column v 1)))
                                (cl-mpm/fastmaths::fast-.* (cl-mpm/utils::matrix-column v 2)
                                                           (rotate-vector (cl-mpm/utils::matrix-column v 2)))

                                (magicl:scale! (cl-mpm/fastmaths::fast-.+
                                                (cl-mpm/fastmaths::fast-.*
                                                 (cl-mpm/utils::matrix-column v 0)
                                                 (rotate-vector (cl-mpm/utils::matrix-column v 1)))
                                                (cl-mpm/fastmaths::fast-.*
                                                 (cl-mpm/utils::matrix-column v 1)
                                                 (rotate-vector (cl-mpm/utils::matrix-column v 0)))) 1d0)

                                (magicl:scale! (cl-mpm/fastmaths::fast-.+
                                                (cl-mpm/fastmaths::fast-.*
                                                 (cl-mpm/utils::matrix-column v 1)
                                                 (rotate-vector (cl-mpm/utils::matrix-column v 2)))
                                                (cl-mpm/fastmaths::fast-.*
                                                 (cl-mpm/utils::matrix-column v 2)
                                                 (rotate-vector (cl-mpm/utils::matrix-column v 1)))) 1d0)
                                (magicl:scale! (cl-mpm/fastmaths::fast-.+
                                                (cl-mpm/fastmaths::fast-.*
                                                 (cl-mpm/utils::matrix-column v 2)
                                                 (rotate-vector (cl-mpm/utils::matrix-column v 0)))
                                                (cl-mpm/fastmaths::fast-.*
                                                 (cl-mpm/utils::matrix-column v 0)
                                                 (rotate-vector (cl-mpm/utils::matrix-column v 2)))) 1d0)
                                ) '(2 6))))
                           (psinc 0d0)
                           )
                      (declare (double-float t1 t2 f12 f13))
                      (cond
                        ((and
                          (> t1 tol)
                          (> t2 tol)
                          )
                         ;;Apex stress return
                         (setf sig siga)
                         (setf path :apex)
                         )
                        ((and
                          (< f12 tol)
                          (< f13 tol)
                          )
                         (setf sig (cl-mpm/fastmaths::fast-.+ siga (magicl:scale! r1 t1)))
                         (setf path :line-1)
                         ;;line 1
                         )
                        ((and
                          (> f12 tol)
                          (> f13 tol)
                          )
                         (setf sig (cl-mpm/fastmaths::fast-.+ siga (magicl:scale! r2 t2)))
                         ;;line 2
                         (setf path :line-2)
                         )
                        (t
                         (setf sig (magicl:.- sig (magicl:scale! rp f)))
                         (setf path :main)
                                        ;main
                         )
                        )
                      (setf eps-e (cl-mpm/fastmaths::fast-@-matrix-vector Ce sig eps-e))

                      (setf f (mc-yield-func sig phi c))
                      (when (> f (* 10000d0 tol))
                        (error "Mohr-coloumb return misscalculated on path: ~A with an error of f: ~F" path f))
                      (setf psinc (the double-float
                                       (cl-mpm/fastmaths::vector-principal-von-mises
                                        (cl-mpm/fastmaths::fast-.--vector
                                         eps-e
                                         epstr))))
                      ;; (break)
                      (let ((pad-eps
                              (cl-mpm/utils:voigt-from-list
                               (list
                                (varef eps-e 0)
                                (varef eps-e 1)
                                (varef eps-e 2)
                                0d0
                                0d0
                                0d0))))
                        (setf eps-e (magicl:linear-solve Q pad-eps)))
                      (setf sig (cl-mpm/fastmaths::fast-@-tensor-voigt de eps-e))
                      (values
                       (swizzle-coombs->voigt sig stress)
                       (swizzle-coombs->voigt eps-e trial-elastic-strain)
                       ;; sig
                       ;; eps-e
                       initial-f
                       ;; 0d0
                       psinc
                       pmod
                       ))
                    ;;No MC yield - just return
                    (values stress
                            trial-elastic-strain
                            initial-f
                            0d0
                            pmod)))))
          ;;No DP yield - just return
          (values stress
                  trial-elastic-strain
                  f-dp
                  0d0
                  pmod)))))
(defun mc-plastic-terzaghi (stress de trial-elastic-strain E nu phi psi c pore-pressure)
  (declare (optimize (speed 3) (safety 0) (debug 0)))
  (declare (double-float E nu phi psi c)
           (magicl:matrix/double-float stress de trial-elastic-strain))
  (let* ((tol 1d-9)
         (initial-f 0d0))
    (let ((f-dp (dp-yield-mc-circumscribe
                 (cl-mpm/fastmaths:fast-.+ stress (cl-mpm/utils::voigt-eye pore-pressure))
                 phi c)))
      ;;Early check for if we should yield - DP eval is much faster?
      (if (> f-dp tol)
          (multiple-value-bind (l v) (cl-mpm/utils::eig (cl-mpm/utils:voigt-to-matrix trial-elastic-strain))
            (let* ((l-sort (sort (mapcar #'cons l (list 0 1 2)) #'> :key #'car))
                   (l (mapcar #'car l-sort))
                   (v (magicl:block-matrix (list
                                            (cl-mpm/utils::matrix-column v (cdr (nth 0 l-sort)))
                                            (cl-mpm/utils::matrix-column v (cdr (nth 1 l-sort)))
                                            (cl-mpm/utils::matrix-column v (cdr (nth 2 l-sort)))) '(1 3))))
              (let* ((De3
                       (cl-mpm/fastmaths::fast-scale!
                        (cl-mpm/utils:matrix-from-list (list
                                                        (- 1d0 nu) nu nu
                                                        nu (- 1d0 nu) nu
                                                        nu nu (- 1d0 nu)))
                        (/ E (* (+ 1d0 nu) (- 1d0 (* 2d0 nu))))))
                     (epsTr (cl-mpm/utils:vector-from-list l))
                     (sig (cl-mpm/utils:@-mat-vec De3 epsTr))
                     (sig (cl-mpm/fastmaths:fast-.+ sig (cl-mpm/utils::voigt-eye pore-pressure) sig))
                     (f (mc-yield-func sig phi c))
                     (initial-f f))
                ;; (format t "f: ~E - Fdp: ~E~%" f f-dp)
                ;; (when (and
                ;;        (> f tol)
                ;;        (not (> f-dp tol)))
                ;;   (error "DP misses mc case ~E ~E" f f-dp))
                (if (> f tol)
                    (let* (
                           (Ce (magicl:inv De3))
                           (eps-e (cl-mpm/utils::vector-copy epsTr))
                           ;; (eps-e epsTr)
                           (k (/ (+ 1 (sin phi)) (- 1d0 (sin phi))))
                           (sigc (* 2d0 c (sqrt k)))
                           (m (/ (+ 1 (sin psi)) (- 1d0 (sin psi))))
                           (siga (magicl:scale! (cl-mpm/utils:vector-from-list (list 1d0 1d0 1d0))
                                                (/ sigc (- k 1d0))
                                                ))
                           (r1 (vector-from-list (list 1d0 1d0 k)))
                           (r2 (vector-from-list (list 1d0 k k)))
                           (rg1 (vector-from-list (list 1d0 1d0 m)))
                           (rg2 (vector-from-list (list 1d0 m m)))
                           (df (vector-from-list (list k 0d0 -1d0)))
                           (dg (vector-from-list (list m 0d0 -1d0)))
                           (rp (magicl:scale! (cl-mpm/utils:@-mat-vec De3 dg)
                                              (/ 1d0 (the double-float
                                                          (magicl:tref (magicl:@ (magicl:transpose dg) De3 df) 0 0)
                                                          ))))
                           (t1 (/ (magicl:tref (magicl:@ (magicl:transpose rg1) Ce (magicl:.- sig siga)) 0 0)
                                  (magicl:tref (magicl:@ (magicl:transpose rg1) Ce r1) 0 0)))
                           (t2 (/ (magicl:tref (magicl:@ (magicl:transpose rg2) Ce (magicl:.- sig siga)) 0 0)
                                  (magicl:tref (magicl:@ (magicl:transpose rg2) Ce r2) 0 0)))
                           (f12 (magicl:tref (magicl:@ (magicl:transpose! (cl-mpm/fastmaths::cross-product rp r1))
                                                       (magicl:.- sig siga)) 0 0))
                           (f13 (magicl:tref (magicl:@ (magicl:transpose! (cl-mpm/fastmaths::cross-product rp r2))
                                                       (magicl:.- sig siga)) 0 0))
                           (path :no-return)
                           (Q
                             (magicl:transpose!
                              (magicl:block-matrix (list
                                                    (cl-mpm/fastmaths::fast-.* (cl-mpm/utils::matrix-column v 0)
                                                                              (cl-mpm/utils::matrix-column v 0))

                                                    (cl-mpm/fastmaths::fast-.* (cl-mpm/utils::matrix-column v 1)
                                                                              (cl-mpm/utils::matrix-column v 1))
                                                    (cl-mpm/fastmaths::fast-.* (cl-mpm/utils::matrix-column v 2)
                                                                              (cl-mpm/utils::matrix-column v 2))

                                                    (magicl:scale!
                                                     (cl-mpm/fastmaths::fast-.* (cl-mpm/utils::matrix-column v 0)
                                                                               (cl-mpm/utils::matrix-column v 1)) 2d0)
                                                    (magicl:scale!
                                                     (cl-mpm/fastmaths::fast-.* (cl-mpm/utils::matrix-column v 1)
                                                                               (cl-mpm/utils::matrix-column v 2)) 2d0)
                                                    (magicl:scale!
                                                     (cl-mpm/fastmaths::fast-.* (cl-mpm/utils::matrix-column v 2)
                                                                               (cl-mpm/utils::matrix-column v 0)) 2d0)

                                                    (cl-mpm/fastmaths::fast-.* (cl-mpm/utils::matrix-column v 0)
                                                                              (rotate-vector (cl-mpm/utils::matrix-column v 0)))
                                                    (cl-mpm/fastmaths::fast-.* (cl-mpm/utils::matrix-column v 1)
                                                                              (rotate-vector (cl-mpm/utils::matrix-column v 1)))
                                                    (cl-mpm/fastmaths::fast-.* (cl-mpm/utils::matrix-column v 2)
                                                                              (rotate-vector (cl-mpm/utils::matrix-column v 2)))

                                                    (magicl:scale! (cl-mpm/fastmaths::fast-.+
                                                                    (cl-mpm/fastmaths::fast-.* (cl-mpm/utils::matrix-column v 0)
                                                                                              (rotate-vector (cl-mpm/utils::matrix-column v 1)))
                                                                    (cl-mpm/fastmaths::fast-.* (cl-mpm/utils::matrix-column v 1)
                                                                                              (rotate-vector (cl-mpm/utils::matrix-column v 0)))) 1d0)

                                                    (magicl:scale! (cl-mpm/fastmaths::fast-.+
                                                                    (cl-mpm/fastmaths::fast-.* (cl-mpm/utils::matrix-column v 1)
                                                                                              (rotate-vector (cl-mpm/utils::matrix-column v 2)))
                                                                    (cl-mpm/fastmaths::fast-.* (cl-mpm/utils::matrix-column v 2)
                                                                                              (rotate-vector (cl-mpm/utils::matrix-column v 1)))) 1d0)
                                                    (magicl:scale! (cl-mpm/fastmaths::fast-.+
                                                                    (cl-mpm/fastmaths::fast-.* (cl-mpm/utils::matrix-column v 2)
                                                                                              (rotate-vector (cl-mpm/utils::matrix-column v 0)))
                                                                    (cl-mpm/fastmaths::fast-.* (cl-mpm/utils::matrix-column v 0)
                                                                                              (rotate-vector (cl-mpm/utils::matrix-column v 2)))) 1d0)
                                                    ) '(2 6)))))
                      (declare (double-float t1 t2 f12 f13))
                      (cond
                        ((and
                          (> t1 tol)
                          (> t2 tol)
                          )
                         ;;Apex stress return
                         (setf sig siga)
                         (setf path :apex)
                         )
                        ((and
                          (< f12 tol)
                          (< f13 tol)
                          )
                         (setf sig (cl-mpm/fastmaths::fast-.+ siga (magicl:scale! r1 t1)))
                         (setf path :line-1)
                         ;;line 1
                         )
                        ((and
                          (> f12 tol)
                          (> f13 tol)
                          )
                         (setf sig (cl-mpm/fastmaths::fast-.+ siga (magicl:scale! r2 t2)))
                         ;;line 2
                         (setf path :line-2)
                         )
                        (t
                         (setf sig (magicl:.- sig (magicl:scale! rp f)))
                         (setf path :main)
                                        ;main
                         )
                        )


                      (setf f (mc-yield-func sig phi c))
                      (when (> f (* 10000d0 tol))
                        (error "Mohr-coloumb return misscalculated on path: ~A with an error of f: ~F" path f))

                      ;; (cl-mpm/fastmaths:fast-.- sig (cl-mpm/utils::voigt-eye pore-pressure) sig)
                      (setf eps-e (magicl:@ Ce sig))

                      ;; (break)
                      (let ((pad-eps (magicl:block-matrix (list eps-e
                                                                (cl-mpm/utils:vector-zeros))
                                                          '(2 1))))
                        ;; (setf eps-e (magicl:@ (magicl:inv Q) pad-eps))
                        (setf eps-e (magicl:linear-solve Q pad-eps))
                        )

                      (setf sig (magicl:@ (magicl:transpose! Q)
                                          (cl-mpm/utils:voigt-from-list
                                           (list
                                            (varef sig 0)
                                            (varef sig 1)
                                            (varef sig 2)
                                            0d0 0d0 0d0))))

                      (values
                       ;; sig
                       (swizzle-coombs->voigt sig)
                       (swizzle-coombs->voigt eps-e) initial-f)
                      )
                    ;;No MC yield - just return
                    (values stress trial-elastic-strain initial-f)))))
          ;;No DP yield - just return
          (values stress
                  trial-elastic-strain f-dp)))))
