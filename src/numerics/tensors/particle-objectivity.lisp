(in-package :cl-mpm/particle)

(declaim (optimize (debug 0) (safety 0) (speed 3)))



;; (declaim (inline assemble-vorticity-matrix)
;;          (ftype (function (magicl:matrix/double-float)
;;                           magicl:matrix/double-float
;;                           ) assemble-vorticity-matrix))
(defun assemble-vorticity-matrix (vorticity)
  (let ((dx (magicl:tref vorticity 0 0))
        (dy (magicl:tref vorticity 1 0))
        (dxdy (magicl:tref vorticity 2 0))
        )
    (declare (double-float dx dy dxdy))
    (cl-mpm/utils::matrix-from-list (list dx dxdy 0d0
                                          (- dxdy) dy 0d0
                                          0d0 0d0 0d0))))

(defun objectify-stress (mp)
  (cl-mpm/particle:mp-stress mp))

(defun objectify-stress-jaumann (stress-inc stress vorticity)
  (magicl:.-
   stress-inc
   (matrix-to-voight
    (magicl::.- (magicl:@ (voight-to-matrix stress) (assemble-vorticity-matrix vorticity))
                (magicl:@ (assemble-vorticity-matrix vorticity) (voight-to-matrix stress)))))
             )

(defun objectify-stress-kirchoff-truesdale (stress-inc stress velocity-rate)
  (magicl:.-
   stress-inc
   (matrix-to-voight
    (magicl::.- (magicl:@ (voight-to-matrix stress) (voight-to-matrix velocity-rate))
                (magicl:@ (voight-to-matrix velocity-rate) (voight-to-matrix stress))
                ))))

;; (declaim (inline objectify-stress-logspin)
;;          (ftype (function (magicl:matrix/double-float
;;                            magicl:matrix/double-float
;;                            magicl:matrix/double-float
;;                            magicl:matrix/double-float
;;                            magicl:matrix/double-float
;;                            )
;;                           magicl:matrix/double-float
;;                           )
;;                 objectify-stress-logspin))
(defun objectify-stress-logspin (stress-inc stress def vorticity D)
    (let ((b (magicl:@ def (magicl:transpose def)))
          ;; (omega (assemble-vorticity-matrix vorticity))
          (omega (magicl:scale! (magicl:.- D (magicl:transpose D)) 0.5d0))
          (D (magicl:scale! (cl-mpm/fastmaths::fast-.+ D (magicl:transpose D)) 0.5d0))
          ;; (D (cl-mpm/utils::voigt-to-matrix D))
          )
        (multiple-value-bind (l v) (cl-mpm/utils::eig b)
          (loop for i from 0 to 2
                do (loop for j from 0 to 2
                         do
                            ;;For all the pairs of eigenvalues
                            (when (not (= i j))
                              (let ((l_i (nth i l))
                                    (l_j (nth j l))
                                    (v_i (magicl:column v i))
                                    (v_j (magicl:column v j)))
                                ;; (declare (double-float l_i l_j)
                                ;;          (magicl:matrix/double-float v_i v_j))
                                ;;When the eigenvalues are distinct
                                (when (and
                                       ;;When they are nonzero
                                       (> (abs (- l_i l_j)) 1d-6)
                                       )
                                  ;; When we have pairs of unique nonzero eigenvalues
                                  (setf omega
                                        (cl-mpm/fastmaths::fast-.+ omega
                                                   (magicl:scale!
                                                    (magicl:@
                                                     (magicl:@
                                                      v_i
                                                      (magicl:transpose v_i))
                                                     D
                                                     (magicl:@
                                                      v_j
                                                      (magicl:transpose v_j)))
                                                    (+
                                                     (/ (+ 1d0 (/ l_i l_j)) (- 1d0 (/ l_i l_j)))
                                                     (/ 2d0 (the double-float (log (/ l_i l_j)))))
                                                    )))
                                  ))))))
      (magicl:.-
       stress-inc
       (cl-mpm/utils::matrix-to-voight
        (magicl::.- (magicl:@ (cl-mpm/utils::voight-to-matrix stress) omega)
                    (magicl:@ omega (cl-mpm/utils::voight-to-matrix stress)))))
      ))



(defun matrix-sqrt (mat)
  (multiple-value-bind (l v) (cl-mpm/utils::eig mat)
    (magicl:@ v
              (cl-mpm/utils::matrix-from-list
               (list
                (the double-float (sqrt (the double-float (nth 0 l)))) 0d0 0d0
                0d0 (the double-float (sqrt (the double-float (nth 1 l)))) 0d0
                0d0 0d0 (the double-float (sqrt (the double-float (nth 2 l))))
                ))
              (magicl:transpose v)
              )))
