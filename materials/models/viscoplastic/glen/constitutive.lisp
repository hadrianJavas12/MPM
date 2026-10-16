(in-package :cl-mpm/constitutive)

(declaim #.cl-mpm/settings:*optimise-setting*)




(defun elasto-glen (strain-increment stress E nu de viscosity dt strain)
  "A absolute stress form of a nonlinear glen flow with elastic volume"
  (let* ((order 2)
         (strain-dev (deviatoric strain-increment))
         (bulk-modulus (/ E (* (+ 1 nu) (- 1 nu nu))))
         ;; (pressure-inc (* bulk-modulus (voight-trace strain-increment)))
         ;; (pressure (+ pressure-inc (* 0.5 (voight-trace stress))))
         (pressure (* bulk-modulus 0.5 (voight-trace strain)))
         )
    (declare (type double-float pressure))
    (cl-mpm/fastmaths::fast-.+
     (magicl:from-list (list pressure pressure 0d0) '(3 1))
     (magicl:scale! strain-dev (/ (* 2d0 viscosity) dt))
    )))

(defun elasto-glen-damage (strain-increment stress E nu de viscosity dt strain damage)
  "A absolute stress form of a nonlinear glen flow with elastic volume"
  (let* ((order 2)
         (strain-dev (deviatoric strain-increment))
         (bulk-modulus (/ E (* (+ 1 nu) (- 1 nu nu))))
         (pressure (* bulk-modulus 0.5 (voight-trace strain)))
         )
    (declare (type double-float pressure))
    (when (< pressure 0)
      (setf pressure (* pressure (- 1d0 damage))))
    (cl-mpm/fastmaths::fast-.+
     (magicl:from-list (list pressure pressure 0d0) '(3 1))
     (magicl:scale! strain-dev (/ (* 2d0 viscosity) dt))
     )))

(defun norton-hoff (strain-increment stress youngs-modulus poisson-ratio visc-factor visc-power dt vorticity)
  "A stress of a viscoplastic norton-off material"
  (let* ((order 3)
         ;(strain-matrix (voight-to-matrix strain-increment))
         (pressure (/ (magicl:trace (voight-to-matrix stress)) 3d0))
         (pressure-matrix (magicl:eye 2 :value pressure))
         (dev-stress (matrix-to-voight (magicl:.- (voight-to-matrix stress) pressure-matrix)))
         (glenn-strain-rate (magicl:scale dev-stress (* dt
                                                        visc-factor
                                                        (expt (magicl::sum (cl-mpm/fastmaths::fast-.* dev-stress dev-stress
                                                                                        (magicl:from-list
                                                                                         '(0.5d0 0.5d0 1d0) '(3 1))))
                                                              (* 0.5 (- visc-power 1)))))))
    (cl-mpm/fastmaths::fast-.+ stress
               (magicl:.-
                ;;I think this is correct but not sure
                (magicl:@ (linear-elastic-matrix youngs-modulus poisson-ratio)
                          (magicl:.- strain-increment glenn-strain-rate))
                (magicl:scale (matrix-to-voight
                               (magicl::.- (magicl:@ (voight-to-matrix stress) (assemble-vorticity-matrix vorticity))
                                           (magicl:@ (assemble-vorticity-matrix vorticity) (voight-to-matrix stress)))
                               ) 0)
                ))
    ))

(defun norton-hoff-plastic-strain (stress visc-factor visc-power dt)
  (let* ((order 3)
         ;(strain-matrix (voight-to-matrix strain-increment))
         (pressure (/ (magicl:trace (voight-to-matrix stress)) 3d0))
         (pressure-matrix (magicl:eye 2 :value pressure))
         (dev-stress (matrix-to-voight (magicl:.- (voight-to-matrix stress) pressure-matrix)))
         (glenn-strain-rate (magicl:scale dev-stress (* dt
                                                        visc-factor
                                                        (expt (magicl::sum (cl-mpm/fastmaths::fast-.* dev-stress dev-stress
                                                                                        (magicl:from-list
                                                                                         '(0.5d0 0.5d0 1d0) '(3 1))))
                                                              (- visc-power 1)))))
         )
    glenn-strain-rate
    ))

(defun glen-flow (strain-increment stress bulk-modulus visc-factor visc-power dt vorticity)
  "A stress of a viscoplastic glen flow law material"
  (let* ((order 3)
         ;(strain-matrix (voight-to-matrix strain-increment))
         (pressure (/ (magicl:trace (voight-to-matrix stress)) 3d0))
         (pressure-increment (* bulk-modulus (magicl:trace (voight-to-matrix strain-increment))))
         (pressure-matrix (magicl:eye 2 :value (+ pressure pressure-increment)))
         (dev-stress (glen-stress strain-increment visc-factor visc-power dt)))
    (cl-mpm/fastmaths::fast-.+ (matrix-to-voight pressure-matrix) dev-stress)))

(defun glen-stress (strain visc-factor visc-power dt)
  (let* ((strain-trace (/ (magicl:trace (voight-to-matrix strain)) 3d0))
         (dev-strain (matrix-to-voight (magicl:.- (voight-to-matrix strain) (magicl:eye 2 :value strain-trace))))
         (second-invar (magicl:from-list '(0.5d0 0.5d0 1d0) '(3 1) :type 'double-float))
         (effective-strain (magicl::sum (cl-mpm/fastmaths::fast-.* dev-strain dev-strain second-invar)))
         )
    (if (> effective-strain 0d0)
        (magicl:scale dev-strain (* visc-factor (expt effective-strain
                                                 (* 0.5d0 (- (/ 1d0 visc-power) 1d0)))))
        (magicl:scale dev-strain 0d0))))


(declaim (ftype (function (magicl:matrix/double-float double-float double-float) double-float) glen-viscosity))
(defun glen-viscosity (stress visc-factor visc-power)
  "Get the viscosity for a given stress state"
  (let* ((s-dev (deviatoric-voigt stress))
         (second-invar (cl-mpm/utils:voigt-from-list (list 1d0 1d0 1d0 2d0 2d0 2d0)))
         (visc-factor (expt visc-factor (- visc-power)))
         (effective-stress (+ 1d-20 (* 0.5d0
                                       (cl-mpm/fastmaths::fast-sum
                                        (cl-mpm/fastmaths:fast-.*
                                         (cl-mpm/fastmaths:fast-.* s-dev s-dev)
                                         second-invar))))))
    (declare (type double-float effective-stress))
    (if (> effective-stress 0d0)
        (/ 1d0 (* 2d0 visc-factor (expt effective-stress (* 0.5d0 (- visc-power 1)))))
        0d0)))

(declaim (ftype (function (magicl:matrix/double-float double-float double-float) double-float) glen-viscosity-strain))
(defun glen-viscosity-strain (strain visc-factor visc-power)
  "Get the viscosity for a given strain state"
  (let* ((effective-strain (+ 1d-20 (effective-strain-rate strain))))
    (declare (type double-float effective-strain))
    (* visc-factor (the double-float (expt effective-strain (* 1d0 (- (/ 1d0 visc-power) 1d0)))))))

(defun glen-viscosity-stress (stress visc-factor visc-power)
  (declare (double-float visc-factor visc-power))
  "Get the viscosity for a given strain state"
  (let* ((A (expt visc-factor (/ -1d0 visc-power)))
         (effective-strain (+ 1d-50 (sqrt (* 0.5d0 (expt (cl-mpm/utils::trace-voigt (deviatoric-voigt stress)) 2d0))))))
    (declare (type double-float effective-strain A))
    (if (> effective-strain 0d0)
        (/ 1d0 (* 2d0 A (the double-float (expt effective-strain (- visc-power 1d0)))))
        0d0)))


(declaim (ftype (function (magicl:matrix/double-float double-float double-float) (values double-float)) glen-viscosity-strain))
(defun glen-viscosity-stretch (stretch visc-factor visc-power)
  "Get the viscosity for a given strain state"
  (let* (;(effective-strain (+ 1d-15 (cl-mpm/fastmaths::voigt-tensor-reduce-simd (deviatoric strain))))
         (dev-stretch (deviatoric-voigt stretch))
         (effective-strain (+ 1d-15 (* 0.5d0 (magicl::sum (cl-mpm/fastmaths::fast-.* dev-stretch dev-stretch))))))
    (declare (type double-float effective-strain))
    (if (> effective-strain 0d0)
        (values (* 0.5d0 visc-factor (expt effective-strain (* 0.5d0 (- (/ 1d0 visc-power) 1d0)))))
        (values 0d0))))
