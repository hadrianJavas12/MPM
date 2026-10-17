(in-package :cl-mpm/damage)

(declaim (optimize (debug 0) (safety 0) (speed 3)))



(defun principal-stresses (stress)
  (multiple-value-bind (l v) (cl-mpm/utils::eig (voight-to-matrix stress))
    (declare (ignore v))
    (values (apply #'max l) (apply #'min l))))

(defun principal-stresses-3d (stress)
  (multiple-value-bind (l v) (cl-mpm/utils::eig (voight-to-matrix stress))
    (declare (ignore v))
    (setf l (sort l #'>))
    (values (nth 0 l) (nth 1 l) (nth 2 l))))

;; (defgeneric update-delocalisation-list (sim))
;; (defmethod update-delocalisation-list ((sim cl-mpm::mpm-sim))
;;   (update-delocalisation-list-mps (cl-mpm:sim-mesh *sim*)
;;                                   (cl-mpm:sim-mps *sim*)))


;;This is a simd dot product
(progn

  (defun diff-squared-mat (pos-a pos-b)
    (let ((pos-a (magicl::matrix/double-float-storage pos-a))
          (pos-b (magicl::matrix/double-float-storage pos-b)))
      (values (the double-float (cl-mpm/fastmaths::dot-vector pos-a pos-b)))))

  (defun test-simd-acc (a b)
    (let (
          ;; (a (cl-mpm/utils:vector-from-list (list 1d0 2d0 3d0)))
          ;; (b (cl-mpm/utils:vector-from-list (list -1d0 5d0 8d0)))
          (a (cl-mpm/utils:vector-from-list (list 0d0 0d0 0d0)))
          (b (cl-mpm/utils:vector-from-list (list 1d0 1d0 1d0)))
          )
      (pprint (diff-squared-mat a b))
      ))

  (declaim
   (inline diff-squared)
   (ftype (function (cl-mpm/particle:particle cl-mpm/particle:particle) double-float) diff-squared))
  (defun diff-squared (mp-a mp-b)
    (cl-mpm/fastmaths::diff-norm
     (cl-mpm/particle:mp-position mp-a)
     (cl-mpm/particle:mp-position mp-b))
    )
  )
