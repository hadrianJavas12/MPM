(in-package :cl-mpm/constitutive)

(declaim #.cl-mpm/settings:*optimise-setting*)


;; (defun maxwell-damage (strain-increment stress elasticity poisson-ratio de viscosity dt damage)
;;   "A stress increment form of a viscoelastic maxwell material"
;;   (let* ((order 2)
;;          (stress-matrix (voight-to-matrix stress))
;;          (pressure (/ (magicl:trace stress-matrix) 3d0))
;;          (pressure-matrix (magicl:eye 2 :value pressure))
;;          (dev-stress (magicl:.- stress-matrix pressure-matrix))
;;          (relaxation-const (/ (* dt elasticity)
;;                               (* 2d0 (- 1d0 poisson-ratio) viscosity)))
;;          )
;;     (declare (type double-float relaxation-const))
;;     (magicl:.-
;;      (magicl:scale! (magicl:@ de strain-increment) (max 1d-3 (- 1d0 damage)))
;;                                         ;(magicl:@ (linear-elastic-matrix (* (- 1d0 damage) elasticity) poisson-ratio) strain-increment)
;;      (magicl:scale! (matrix-to-voight dev-stress) relaxation-const))
;;     ;; (matrix-to-voight (tensile-project (voight-to-matrix (magicl:@ de strain-increment)) stress damage))
;;     ))

(defun tensile-projection-eig (stress)
  (flet ((H (x) (if (> x 0d0) 1d0 0d0)))
    (multiple-value-bind (l v) (cl-mpm/utils::eig (voight-to-matrix stress))
      (loop for i from 0 to 1
            do (let* ((sii (nth i l)))
                 (setf (nth i l) (* sii (H sii)))))
      (matrix-to-voight (magicl:@ v
                                  (magicl:from-diag l :type 'double-float)
                                  (magicl:transpose v))))))

(defun tensile-projection-Q-mandel (stress)
  (flet ((H (x) (if (> x 0d0) 1d0 0d0)))
    (let ((Q (magicl:zeros '(3 3) :type 'double-float)))
      (multiple-value-bind (l v) (cl-mpm/utils::eig (voight-to-matrix stress))
        (loop for i from 0 to 1
              do (let* ((sii (nth i l))
                        (vii (magicl::column v i))

                        (vsi (magicl:@ vii (magicl:transpose vii)))
                        (comp-prod
                          (magicl:scale (magicl:@
                                         (matrix-to-mandel vsi)
                                         (magicl:transpose (matrix-to-mandel vsi)))
                                        (H sii)))

                        (v1 (magicl:tref vii 0 0))
                        (v2 (magicl:tref vii 1 0))

                        (v1111 (* v1 v1 v1 v1))
                        (v2222 (* v2 v2 v2 v2))
                        (v1122 (* v1 v1 v2 v2))
                        (v1112 (* v1 v1 v1 v2))
                        (v1222 (* v1 v2 v2 v2))
                        (v1212 (* v1 v2 v1 v2))

                        (comp
                          (magicl:scale!
                           (magicl:from-list (list (* 1 v1111) (* 1 v1122) (* (sqrt 2) v1112)
                                                   (* 1 v1122) (* 1 v2222) (* (sqrt 2) v1222)
                                                   (* (sqrt 2) v1112) (* (sqrt 2) v1222) (* 2 v1212)) '(3 3))
                           (H sii))
                          )
                        )
                   (cl-mpm/fastmaths::fast-.+ Q comp Q)
                   )
              )
      Q))))

(defun tensile-projection-Q-cw-mandel (strain)
  (flet ((H (x) (if (> x 0d0) 1d0 0d0)))
    (let ((Q (magicl:zeros '(3 3) :type 'double-float)))
      (multiple-value-bind (l v) (cl-mpm/utils::eig (voight-to-matrix (cl-mpm/fastmaths::fast-.* strain
                                                                          (magicl:from-list '(1d0 1d0 0.5d0) '(3 1))
                                                                          )))
        (loop for i from 0 to 1
              do (let* ((si (nth i l))
                        (vi (magicl::column v i))
                        (vii (magicl:@ vi (magicl:transpose vi)))
                        (comp-prod
                          (magicl:scale (magicl:@
                                         (matrix-to-mandel vii)
                                         (magicl:transpose (matrix-to-mandel vii)))
                                        (H si))))
                   (cl-mpm/fastmaths::fast-.+ Q comp-prod Q)
                   )
              )
        (let* ((si (nth 0 l))
               (sj (nth 1 l))
               (vi (magicl::column v 0))
               (vj (magicl::column v 1))
               (vij (magicl:@ vi (magicl:transpose vj)))
               (vji (magicl:@ vj (magicl:transpose vi)))
               (pij (magicl:scale!
                     (cl-mpm/fastmaths::fast-.+ vij vji)
                     0.5d0))
               (comp-prod
                 (magicl:scale! (magicl:@
                                (matrix-to-mandel pij)
                                (magicl:transpose (matrix-to-mandel pij)))
                               (+ (H si) (H sj)))))
          (cl-mpm/fastmaths::fast-.+ Q comp-prod Q))
          )
      Q)))

(defun tensile-project-q (stress)
  (mandel-to-voigt
   (magicl:@
    (tensile-projection-q-mandel stress)
    (voigt-to-mandel stress))))

(defun tensile-projection-A (strain damage)
  "Generate a mandel form tensile projection matrix A* from stress"
  (let ((Q (tensile-projection-q-cw-mandel strain))
        (I (magicl:from-diag '(1d0 1d0 1d0))))
    (cl-mpm/fastmaths::fast-.+ I (magicl:scale Q (- (sqrt (- 1d0 damage)) 1d0)))))

;; (defun test-tensile ()
;;   (loop for stress in (list
;;                        (magicl:from-list '(1 0 0) '(3 1) :type 'double-float)
;;                        (magicl:from-list '(0 1 0) '(3 1) :type 'double-float)
;;                        (magicl:from-list '(1 1 0) '(3 1) :type 'double-float)
;;                        (magicl:from-list '(-1 0 0) '(3 1) :type 'double-float)
;;                        (magicl:from-list '(0 -1 0) '(3 1) :type 'double-float)
;;                        (magicl:from-list '(-1 -1 0) '(3 1) :type 'double-float)
;;                        (magicl:from-list '(1 -1 0) '(3 1) :type 'double-float)
;;                        (magicl:from-list '(-1 1 0) '(3 1) :type 'double-float)
;;                        (magicl:from-list '(0 0 1) '(3 1) :type 'double-float)
;;                        (magicl:from-list '(1 0 1) '(3 1) :type 'double-float)
;;                        (magicl:from-list '(0 1 1) '(3 1) :type 'double-float)
;;                        (magicl:from-list '(-1 0 1) '(3 1) :type 'double-float)
;;                        (magicl:from-list '(0 -1 1) '(3 1) :type 'double-float)
;;                         )
;;         do (let* ((stress-eig (tensile-projection-eig stress 1d0))
;;                   (stress-project (tensile-project-q stress))
;;                  )
;;              (format t "Stress~%")
;;              (loop for i from 0 to 2
;;                    do (format t "~A ~A ~A ~%"
;;                               (magicl:tref stress i 0)
;;                               (magicl:tref stress-eig i 0)
;;                               (magicl:tref stress-project i 0)
;;                               )))
;;     ))

(defun tensile-project (stiffness stress damage)
  (if (> damage 0.0d0)
    (let ((damaged-stiffness (magicl:zeros '(2 2) :type 'double-float)))
      (multiple-value-bind (l v) (cl-mpm/utils::eig (voight-to-matrix stress))
        (loop for i from 0 to 1
              do (let* ((sii (nth i l))
                        (vii (magicl::column v i))
                        (scale 1d0)
                        (A (magicl:@ vii (magicl:transpose vii)))
                        )
                   (when (> sii 0d0)
                     (setf scale (sqrt (- 1d0 damage)))
                     (magicl:scale! A scale))
                   (cl-mpm/fastmaths::fast-.+ damaged-stiffness
                              (magicl:@ A stiffness A)
                              damaged-stiffness)
                     )))
      damaged-stiffness)
    stiffness))
(defun apply-damage-constitutive (de strain damage)
  (let ((A (tensile-projection-a strain damage)))
    (mandel-to-voigt-4th (magicl:@ A (voigt-4th-to-mandel de) A))))
