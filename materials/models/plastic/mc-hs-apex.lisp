;;;; Opt-in cohesionless friction-evolving MC with explicit g_A=p apex flow.
;;;; No alteration of the strict or perfect-composite projectors.
(defpackage :cl-mpm/models/mc-hs-apex
  (:use :cl)
  (:local-nicknames (:mc :cl-mpm/models/mc-evolution)
                    (:ap :cl-mpm/models/mc-composite-apex))
  (:export #:project-principal #:particle-mc-hs-apex))
(in-package :cl-mpm/models/mc-hs-apex)

(defun check-law (law)
  ;; c=0 makes the apex exactly zero for EVERY evolved positive phi.
  ;; Therefore no strength/history root is hidden in the analytic apex return.
  (unless (and (typep law 'mc:evolution-law)
               (eq (mc:evolution-law-variant law) :hs)
               (eq (mc:evolution-law-stress-measure law) :cauchy)
               (eql (mc:evolution-law-psi law) 0d0)
               (every (lambda (row) (= (second row) 0d0))
                      (mc:evolution-law-cohesion-points law))
               (every (lambda (row) (< 0d0 (second row) 90d0))
                      (mc:evolution-law-points law)))
    (mc::integration-fail "HS apex requires Cauchy HS, c=0, psi=0 and strictly positive phi throughout"))
  law)

(defun project-principal (trial e nu j law old-kappa)
  (check-law law)
  (unless (and (typep trial 'sequence) (= (length trial) 3)
               (every #'mc::finite-real-p trial)
               (mc::finite-real-p e) (> e 0d0)
               (mc::finite-real-p nu) (< -1d0 nu .5d0)
               (mc::finite-real-p j) (> j 0d0)
               (mc::finite-real-p old-kappa) (>= old-kappa 0d0))
    (mc::integration-fail "Invalid HS apex trial, elasticity, J or history"))
  (let* ((raw (map 'vector (lambda (x) (float x 1d0)) trial))
         (tol (+ mc::+stress-atol+ (* mc::+stress-rtol+ (max 1d0 (mc::max-abs3 raw)))))
         (min-phi (* (/ pi 180d0) (reduce #'min (mc:evolution-law-points law) :key #'second)))
         (mean (/ (reduce #'+ raw) 3d0)))
    (multiple-value-bind (c phi psi) (mc:law-values law old-kappa)
      (declare (ignore c psi))
      ;; Preserve the strict elastic screen. Use a disjoint apex domain proven
      ;; inadmissible for trace-free shear at EVERY phi in this evolving law.
      (if (and (> mean (/ tol (* 2d0 (sin min-phi))))
               (> (reduce #'max (map 'vector (lambda (n) (mc::dot3 n raw))
                                    (mc::plane-vectors phi))) tol))
          (let* ((result (ap::%analytic-apex raw (/ e (* 2d0 (+ 1d0 nu)))
                           (/ e (* 3d0 (- 1d0 (* 2d0 nu))))
                           j 0d0 phi old-kappa 0d0 mean tol e nu law))
                 (kappa (mc:projection-kappa result)))
            ;; Same accumulated J2 increment as strict MC. Apex stress=0,
            ;; hence all evolved MC planes and plastic work are exactly zero.
            (multiple-value-bind (new-c new-phi new-psi) (mc:law-values law kappa)
              (setf (mc:projection-cohesion result) new-c
                    (mc:projection-phi result) new-phi
                    (mc:projection-psi result) new-psi))
            result)
          (mc:project-principal trial e nu j law old-kappa)))))

(defclass particle-mc-hs-apex (mc:particle-mc-evolution) ()
  (:documentation "Explicit extra volumetric apex flow; regular HS shear psi0. Not a fracture model."))
(defmethod initialize-instance :around ((mp particle-mc-hs-apex) &rest args
                                       &key evolution-law &allow-other-keys)
  (declare (ignore args)) (check-law evolution-law) (call-next-method))
(defmethod mc:project-particle-principal ((mp particle-mc-hs-apex) trial e nu j law old-kappa)
  (project-principal trial e nu j law old-kappa))
