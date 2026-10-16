(in-package :cl-mpm/constitutive)

(declaim #.cl-mpm/settings:*optimise-setting*)



(defun maxwell-linear (strain-increment stress elasticity viscosity dt)
  (cl-mpm/fastmaths::fast-.+
   stress
   (magicl:@
    (linear-elastic-matrix elasticity 0d0) strain-increment)))


(defun maxwell (strain-increment stress elasticity poisson-ratio de viscosity dt)
  "A stress increment form of a viscoelastic maxwell material"
  (let* ((relaxation-const (/ (* dt elasticity) (* 2d0 (- 1d0 poisson-ratio) viscosity))))
    (declare (type double-float relaxation-const))
    (magicl:.-
     (magicl:@ de strain-increment)
     (magicl:scale! (deviatoric-voigt stress) relaxation-const))
    ))

(defun maxwell-exp-inc (strain-increment stress elasticity poisson-ratio de viscosity dt)
  "A stress increment form of a viscoelastic maxwell material"
  (magicl:.-
   stress
   (maxwell-exp-v strain-increment stress elasticity poisson-ratio de viscosity dt)))
(defun maxwell-damage (strain-increment stress elasticity poisson-ratio de viscosity dt damage strain)
  "A stress increment form of a viscoelastic maxwell material"
  (let* ((relaxation-const (/ (* dt elasticity) (* 2d0 (- 1d0 poisson-ratio) viscosity)))
         (elastic-increment (magicl:@ de strain-increment))
         )
    (declare (type double-float relaxation-const))
    (let* ((stress-matrix (voight-to-matrix elastic-increment))
           (p (/ (magicl:trace stress-matrix) 3d0))
           (pressure-matrix (magicl:eye 2 :value p))
           (dev-stress (magicl:.- stress-matrix pressure-matrix)))
      (setf elastic-increment (matrix-to-voight
                    (cl-mpm/fastmaths::fast-.+ pressure-matrix
                               (magicl:scale! dev-stress (max 0d0 (- 1d0 damage)))))))
    ;; (magicl:scale! elastic-increment (max 1d-3 (- 1d0 damage)))
    (magicl:.-
     elastic-increment
     ;; (magicl:scale! (magicl:@ de strain-increment) (max 1d-3 (expt (- 1d0 damage) 1d0)))
     ;; (magicl:@ (apply-damage-constitutive de strain damage) strain-increment)
     (magicl:scale! (deviatoric-voigt stress) relaxation-const))
    ))

(declaim (ftype (function (magicl:matrix/double-float
                           magicl:matrix/double-float
                           double-float
                           double-float
                           magicl:matrix/double-float
                           double-float
                           double-float
                           )
                          magicl:matrix/double-float
                          ) maxwell-exp))
(defun maxwell-exp (strain-increment stress elasticity nu de viscosity dt)
  ;; (declare (optimize (safety 3) (speed 0)))
  "A stress increment form of a viscoelastic maxwell material"
  (let* ((stress-matrix (voight-to-matrix stress))
         (pressure (/ (magicl:trace stress-matrix) 3d0))
         (pressure-matrix (magicl:eye 3 :value pressure))
         (dev-stress (magicl:.- stress-matrix pressure-matrix))
         (rho (/ (* 2 (- 1 nu) viscosity) elasticity))
         (exp-rho (exp (- (/ dt rho))))
         (lam (* (- 1 exp-rho) (/ rho dt)))
         ;; (exp-rho 1d0)
         ;; (lam 1d0)
         (stress-inc (voight-to-matrix (magicl:@ de strain-increment)))
         (stress-inc-pressure (magicl:eye 3 :value (/ (magicl:trace stress-inc) 3d0)))
         (stress-inc-dev (magicl:.- stress-inc stress-inc-pressure)
         ))
    (cl-mpm/fastmaths::fast-.+
     (matrix-to-voight (cl-mpm/fastmaths::fast-.+ pressure-matrix stress-inc-pressure))
               (cl-mpm/fastmaths::fast-.+
                (magicl:scale! (matrix-to-voight dev-stress) exp-rho)
                (magicl:scale! (matrix-to-voight stress-inc-dev) lam)))))


(defun maxwell-exp-v (strain-increment stress elasticity nu de viscosity dt &key (result-stress))
  "A stress increment form of a viscoelastic maxwell material"
  (let* ((pressure (/ (voight-trace stress) 3d0))
         (pressure-matrix (voight-eye pressure))
         (dev-stress (magicl:.- stress pressure-matrix))
         (rho (/ (* 2d0 (- 1d0 nu) viscosity) elasticity))
         (exp-rho (exp (- (/ dt rho))))
         (lam (* (- 1 exp-rho) (/ rho dt)))
         (stress-inc (magicl:@ (linear-elastic-matrix elasticity nu) strain-increment))
         (stress-inc-pressure (voight-eye (/ (voight-trace stress-inc) 3d0)))
         (stress-inc-dev (magicl:.- stress-inc stress-inc-pressure)))
    (declare (double-float rho exp-rho lam viscosity elasticity dt nu))
    ;(declare (dynamic-extent pressure-matrix dev-stress stress-inc stress-inc-pressure stress-inc-dev))
    (cl-mpm/fastmaths::fast-.+
     (cl-mpm/fastmaths::fast-.+ pressure-matrix stress-inc-pressure)
     (cl-mpm/fastmaths::fast-.+ (cl-mpm/fastmaths:fast-scale! dev-stress exp-rho)
                                (cl-mpm/fastmaths:fast-scale! stress-inc-dev lam)))))

(declaim (ftype (function (magicl:matrix/double-float
                           magicl:matrix/double-float
                           double-float
                           double-float
                           magicl:matrix/double-float
                           double-float
                           double-float
                           &optional
                           (magicl:matrix/double-float nil)
                           )) maxwell-exp-v-simd))

(defun maxwell-exp-v-simd (strain-increment stress elasticity nu de viscosity dt &optional (result-stress nil))
  "A stress increment form of a viscoelastic maxwell material"
  (let* (
         (pressure (/ (voight-trace stress) 3d0))
         (pressure-matrix (voight-eye pressure))
         (dev-stress (magicl:.- stress pressure-matrix))
         (rho (/ (* 2d0 (- 1d0 nu) viscosity) elasticity))
         (exp-rho (exp (- (/ dt rho))))
         (lam (* (- 1 exp-rho) (/ rho dt)))
         (stress-inc (magicl:@ de strain-increment))
         (stress-inc-pressure (voight-eye (/ (voight-trace stress-inc) 3d0)))
         (stress-inc-dev (magicl:.- stress-inc stress-inc-pressure))
         (result-stress (if result-stress
                            result-stress
                            (magicl:zeros '(3 1)))))
    (declare (double-float rho exp-rho lam viscosity elasticity dt nu))
    ;; (declare (dynamic-extent pressure-matrix dev-stress stress-inc stress-inc-pressure stress-inc-dev))
    (cl-mpm/fastmaths:fast-.+ result-stress pressure-matrix)
    (cl-mpm/fastmaths:fast-.+ result-stress stress-inc-pressure)
    (cl-mpm/fastmaths:fast-.+ result-stress stress-inc-pressure)
    (cl-mpm/fastmaths:fast-.+ result-stress stress-inc-pressure)
    (cl-mpm/fastmaths:fast-fmacc result-stress dev-stress exp-rho)
    (cl-mpm/fastmaths:fast-fmacc result-stress stress-inc-dev lam)
    result-stress
    ;; (cl-mpm/fastmaths::fast-.+
    ;;  (cl-mpm/fastmaths::fast-.+ pressure-matrix stress-inc-pressure result-stress)
    ;;  (cl-mpm/fastmaths::fast-.+ (magicl:scale! dev-stress exp-rho)
    ;;             (magicl:scale! stress-inc-dev lam) result-stress))
  ))


(defun maxwell-forwards-fs ()

  )
