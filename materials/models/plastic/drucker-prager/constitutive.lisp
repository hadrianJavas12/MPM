(in-package :cl-mpm/constitutive)

(declaim #.cl-mpm/settings:*optimise-setting*)



(defun dp-yield-mc-circumscribe (stress phi c)
  (declare (double-float c phi))
  (let* ((factor (sqrt (+ 3d0 (expt (sin phi) 2))))
         (a (/ (* (sqrt 3) c (cos phi)) factor))
         (b (/ (* (sqrt 3) (sin phi)) factor))
         (p (/ (cl-mpm/utils::trace-voigt stress) 3d0))
         (j2 (cl-mpm/constitutive::voigt-j2
              (cl-mpm/utils::deviatoric-voigt stress))))
    (declare (double-float a b j2 p))
    (+
     (the double-float (sqrt j2))
     (- a)
     (* b p))))

(defun dp-yield-mc-dp2 (stress phi c)
  (declare (double-float c phi))
  (let* ((a (* c (cos phi)))
         (b (sin phi))
         (p (cl-mpm/utils::trace-voigt stress))
         (j2 (cl-mpm/constitutive::voigt-j2
              (cl-mpm/utils::deviatoric-voigt stress))))
    (declare (double-float a b j2 p))
    (+
     (the double-float (sqrt j2))
     (- a)
     (* b p))))

(declaim (notinline plastic-dp))
(defun plastic-dp (stress de trial-elastic-strain E nu phi psi c)
  ;; (declare (optimize (speed 3) (safety 0) (debug 0)))
  (declare (optimize (speed 0) (safety 3) (debug 3)))
  (declare (double-float E nu phi psi c)
           (magicl:matrix/double-float stress de trial-elastic-strain))
  (let* ((tol 1d-9)
         (initial-f 0d0))

    (let ((f-dp (dp-yield-mc-circumscribe stress phi c)))
      ;;Early check for if we should yield - DP eval is much faster?
      (if t;(> f-dp tol)
          (multiple-value-bind (l v) (cl-mpm/utils::eig (cl-mpm/utils:voigt-to-matrix trial-elastic-strain))
            (let* ((l-sort (sort (mapcar #'cons l (list 0 1 2)) #'> :key #'car))
                   (l (mapcar #'car l-sort))
                   (v (magicl:block-matrix (list
                                            (cl-mpm/utils::matrix-column v (cdr (nth 0 l-sort)))
                                            (cl-mpm/utils::matrix-column v (cdr (nth 1 l-sort)))
                                            (cl-mpm/utils::matrix-column v (cdr (nth 2 l-sort)))) '(1 3))))
              (let* ((alfa (- (tan phi)))
                     (bta (- (tan psi)))
                     (xsic (* (sqrt 3) (/ 1d0 (tan phi)) c))
                     (De3
                       (cl-mpm/fastmaths::fast-scale!
                        (cl-mpm/utils:matrix-from-list (list
                                                        (- 1d0 nu) nu nu
                                                        nu (- 1d0 nu) nu
                                                        nu nu (- 1d0 nu)))
                        (/ E (* (+ 1d0 nu) (- 1d0 (* 2d0 nu))))))
                     ;; (Ce (magicl:inv De3))
                     (Ce (cl-mpm/fastmaths:fast-scale!
                          (cl-mpm/utils:matrix-from-list
                                                       (list
                                                        1d0 (- nu) (- nu)
                                                        (- nu) 1d0 (- nu)
                                                        (- nu) (- nu) 1d0))
                          (/ 1d0 E)))
                     (epsTr (cl-mpm/utils:vector-from-list l))
                     (sig (magicl:.-
                           (cl-mpm/utils:@-mat-vec De3 epsTr)
                           (/ xsic (sqrt 3))))
                     (epsE (magicl:@ Ce sig))
                     (xi (/ (cl-mpm/fastmaths:fast-sum sig) (sqrt 3)))
                     (s (magicl:.-
                         sig
                         (/ xi (sqrt 3))))
                     (rho (sqrt (cl-mpm/fastmaths:dot s s)))
                     (f (- rho (* alfa xi)))
                     (initial-f f))
                (if (> f tol)
                    (let* ((epsTr (cl-mpm/utils:vector-copy epsE))
                           (fap (if (not (= bta 0d0))
                                     (+
                                      (* rho (sqrt (+ 1d0 nu)))
                                      (/
                                       (* xi (sqrt (- 1d0 (* 2d0 nu))))
                                       (* bta
                                          (/
                                           (sqrt (+ 1d0 nu))
                                           (sqrt (- 1d0 (* 2d0 nu)))))))
                                    (* xi sb-ext:double-float-negative-infinity)))
                           (path :no-path)
                           (Q (Q-matrix v)))
                      (cond
                        ((< fap tol)
                         (setf path :apex-return)
                         (setf sig (cl-mpm/fastmaths:fast-scale!
                                    (cl-mpm/utils:vector-from-list (list 1d0 1d0 1d0))
                                    (/ xsic (sqrt 3))))
                         (setf epsE (magicl:@ Ce sig)))
                        (t
                         (setf path :surface-return)
                         (let ((tolf 1d-6)
                               (b (magicl:zeros '(4 1)))
                               (dgam 0d0)
                               (df (magicl:.-
                                    (cl-mpm/fastmaths:fast-scale-vector s (/ 1d0 rho))
                                    (/ alfa (sqrt 3))))
                               (dg (magicl:.-
                                    (cl-mpm/fastmaths:fast-scale-vector s (/ 1d0 rho))
                                    (/ bta (sqrt 3))))
                               (dgg
                                 (magicl:.-
                                  (cl-mpm/fastmaths:fast-scale!
                                   (magicl:.-
                                    (magicl:eye 3 :value 3)
                                    (magicl:ones (list 3 3))
                                    )
                                   (/ 1d0 (* 3d0 rho)))
                                  (cl-mpm/fastmaths:fast-scale!
                                   (magicl:@ s (magicl:transpose s))
                                   (/ 1d0 (expt rho 3))))))
                           (setf (varef b 3) f)
                           (loop for i from 0 to 4
                                 while (or (> (sqrt
                                                (+
                                                 (expt (varef b 0) 2)
                                                 (expt (varef b 1) 2)
                                                 (expt (varef b 2) 2)))
                                               tol)
                                            (> (abs (varef b 3)) tolf)
                                            )
                                 do
                                    (let* ((A (magicl:block-matrix (list
                                                                    (magicl:.+
                                                                     (magicl:eye 3)
                                                                     (cl-mpm/fastmaths:fast-scale! (magicl:@ dgg De3) dgam)
                                                                     )
                                                                    dg
                                                                    (magicl:@ (magicl:transpose df) De3)
                                                                    (magicl:zeros '(1 1)))
                                                                   (list 2 2)
                                                ))
                                           (dx (cl-mpm/fastmaths:fast-scale! (magicl:linear-solve A b) -1d0)))
                                      ;; (pprint A)
                                      ;; (pprint dx)
                                      (loop for i from 0 to 2 do 
                                        (incf (varef epsE i) (varef dx i)))
                                      (incf dgam (varef dx 3))
                                      (setf sig (magicl:@ De3 epsE))
                                      (setf xi (/ (cl-mpm/fastmaths:fast-sum sig) (sqrt 3)))
                                      (setf s (magicl:.-
                                               sig
                                               (/ xi (sqrt 3))))
                                      (setf rho (sqrt (cl-mpm/fastmaths:dot s s)))
                                      (setf df (magicl:.-
                                                (cl-mpm/fastmaths:fast-scale-vector s (/ 1d0 rho))
                                                (/ alfa (sqrt 3))))
                                      (setf dg (magicl:.-
                                           (cl-mpm/fastmaths:fast-scale-vector s (/ 1d0 rho))
                                           (/ bta (sqrt 3))))
                                      (setf dgg
                                       (magicl:.-
                                        (cl-mpm/fastmaths:fast-scale!
                                         (magicl:.-
                                          (magicl:eye 3 :value 3)
                                          (magicl:ones (list 3 3))
                                          )
                                         (/ 1d0 (* 3d0 rho)))
                                        (cl-mpm/fastmaths:fast-scale!
                                         (magicl:@ s (magicl:transpose s))
                                         (/ 1d0 (expt rho 3)))))

                                      (loop for i from 0 to 2 do
                                        (setf (varef b i) (+ (- (varef epsE i) (varef epstr i))
                                                             (* dgam (varef dg i)))))
                                      ;; (pprint (varef b 3))
                                      (setf (varef b 3) (- rho (* alfa xi))))))
                         (loop for i from 0 to 2 do 
                           (incf (varef sig i) (/ xsic (sqrt 3))))
                         ))

                      (setf epsE (magicl:@ Ce sig))
                      (let ((pad-eps (magicl:block-matrix (list epsE
                                                                (cl-mpm/utils:vector-zeros))
                                                          '(2 1))))
                        (setf epsE (magicl:linear-solve Q pad-eps))
                        )

                      (setf sig (magicl:@ (magicl:transpose! Q)
                                          (cl-mpm/utils:voigt-from-list
                                           (list
                                            (magicl:tref sig 0 0)
                                            (magicl:tref sig 1 0)
                                            (magicl:tref sig 2 0)
                                            0d0 0d0 0d0))))
                      (values
                       ;; sig
                       (swizzle-coombs->voigt sig)
                       (swizzle-coombs->voigt epsE)
                       initial-f
                       t))
                    ;;No MC yield - just return
                    (values stress
                            trial-elastic-strain
                            initial-f
                            0d0
                            nil)))))
          ;;No DP yield - just return
          (values stress
                  trial-elastic-strain
                  f-dp
                  0d0
                  nil)))))
