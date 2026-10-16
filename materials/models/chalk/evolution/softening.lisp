(in-package :cl-mpm/damage)



(defun brittle-chalk-d (stress E Gf length init-stress)
  (declare (double-float stress E Gf length init-stress))
  "Function that controls how damage evolves with principal stresses"
  ;; (if (> stress init-stress)
  ;;     (* (expt (max 0d0 (- stress init-stress)) 0.5d0) rate) 0d0)
  ;; (when (> length (/ (* 2 Gf E) (expt init-stress 2)))
  ;;   (error "Length scale is too long"))
  (let* ((hs (/ (expt init-stress 2) (* 2d0 E Gf)))
         (hsl (/ (* hs length) (- 1d0 (* hs length)))))
    (if (> stress init-stress)
        (min 1d0 (max 0d0
                      (- 1d0 (* (/ init-stress stress) (exp (* -2d0 hs (/ (- stress init-stress) stress)))))
                      ))
        0d0)
    ))

(defun damage-rate-profile-chalk (stress damage rate init-stress)
  (declare (double-float stress damage rate init-stress))
  "Function that controls how damage evolves with principal stresses"
  (if (> stress init-stress)
      (* (expt (max 0d0 (- stress init-stress)) 0.5d0) rate)
      0d0))
