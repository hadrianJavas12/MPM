(in-package :cl-mpm/damage)


;; (defun modified-vm-strain (strain nu k E)
;;   (multiple-value-bind (e1 e2 e3)
;;       (principal-stresses-3d
;;        (magicl:.*
;;         strain
;;         (cl-mpm/utils:voigt-from-list
;;          (list 1d0 1d0 1d0
;;                0.5d0
;;                0.5d0
;;                0.5d0))))
;;     (let* ((i1 (+ e1 e2 e3))
;;            (j2
;;              ;; (cl-mpm/constitutive::voigt-j2 (cl-mpm/utils::deviatoric-voigt strain))
;;              (* 1/6 (+
;;                      (expt (- e1 e2) 2)
;;                      (expt (- e2 e3) 2)
;;                      (expt (- e3 e1) 2)))
;;              )
;;            (k-factor (/ (- k 1d0)
;;                         (- 1d0 (* 2d0 nu))))
;;            (s_1 (* E
;;                    (+ (* i1 (/ k-factor (* 2d0 k)))
;;                       (* (/ 1d0 (* 2d0 k))
;;                          (sqrt (+ (expt (* k-factor i1) 2)
;;                                   (* (/ (* 12 k) (expt (- 1d0 nu) 2)) j2)
;;                                   )))))))
;;       s_)))

(defun principal-strains (strains)
  (multiple-value-bind (l v) (cl-mpm/utils::eig (voigt-to-matrix strains))
    (declare (ignore v))
    (setf l (sort l #'>))
    (values (nth 0 l) (nth 1 l) (nth 2 l))))
