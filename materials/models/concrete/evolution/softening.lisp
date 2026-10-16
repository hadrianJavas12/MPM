(in-package :cl-mpm/damage)



(defun brittle-concrete-linear-d (stress E Gf length init-stress)
  (let* ((hsl (/ (expt init-stress 2) (* 2 E Gf)))
         (hs (/ (* hsl length) (- 1 (* hsl length)))))
    (if (> stress init-stress)
        (* (+ 1d0 hs) (- 1d0 (/ init-stress stress)))
        0d0
        )))

(defun brittle-concrete-d (stress E Gf length init-stress)
  (declare (double-float stress E Gf length init-stress))
  "Function that controls how damage evolves with principal stresses"
  (let* (
         (ft init-stress)
         (e0 (/ ft E))
         (ef (+ (/ e0 2) (/ Gf (* length ft))))
         (k (/ stress E))
         )

    (when (> length (/ (* 2 Gf E) (expt ft 2)))
      (error "Length scale is too long"))
    (if (> k e0)
        (- 1d0 (* (/ e0 k) (exp (- (/ (- k e0) (- ef e0)))))) 0d0)))
