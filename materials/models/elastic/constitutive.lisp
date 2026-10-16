(in-package :cl-mpm/constitutive)

(declaim #.cl-mpm/settings:*optimise-setting*)


;; (declaim (optimize (debug 3) (safety 3) (speed 0)))
;; (declaim (optimize (debug 0) (safety 0) (speed 3)))

(defun linear-elastic-matrix (E nu)
  "Create an isotropic linear elastic matrix"
  (declare (double-float E nu))
    (cl-mpm/fastmaths:fast-scale!
     (magicl:from-list (list
                        (- 1d0 nu) nu nu 0d0 0d0 0d0
                        nu (- 1d0 nu) nu 0d0 0d0 0d0
                        nu nu (- 1d0 nu) 0d0 0d0 0d0
                        0d0 0d0 0d0 (* 0.5d0 (- 1d0 (* 2d0 nu))) 0d0 0d0
                        0d0 0d0 0d0 0d0 (* 0.5d0 (- 1d0 (* 2d0 nu))) 0d0
                        0d0 0d0 0d0 0d0 0d0 (* 0.5d0 (- 1d0 (* 2d0 nu))))
                       '(6 6) :type 'double-float)
     (/ E (* (+ 1d0 nu) (- 1d0 (* 2d0 nu))))))

(defun linear-elastic-principal-matrix (E nu)
  "Create an isotropic linear elastic matrix"
  (declare (double-float E nu))
  (cl-mpm/fastmaths:fast-scale!
   (matrix-from-list (list
                      (- 1d0 nu) nu nu
                      nu (- 1d0 nu) nu
                      nu nu (- 1d0 nu)))
   (/ E (* (+ 1d0 nu) (- 1d0 (* 2d0 nu))))))

(defun linear-elastic-matrix-ps (E nu)
  "Create an isotropic linear elastic matrix"
  (let ((inv-nu (/ 1d0 (- 1d0 (expt nu 2)))))
    (magicl:scale!
     (magicl:from-list (list
                        1d0 nu 0d0 0d0 0d0 0d0
                        nu 1d0 0d0 0d0 0d0 0d0
                        0d0 0d0 0d0 0d0 0d0 0d0
                        0d0 0d0 0d0 0d0 0d0 0d0
                        0d0 0d0 0d0 0d0 0d0 0d0
                        0d0 0d0 0d0 0d0 0d0 (* 0.5d0 (- 1d0 nu)))
                       '(6 6) :type 'double-float)
     (/ E (- 1d0 (* nu nu))))))

(defun linear-elastic-mat (strain elastic-matrix &optional (result nil))
  "Isotropic linear-elastic constitutive model"
  ;(cl-mpm/utils:@-tensor-voigt elastic-matrix strain)
  ;; (let ((result (if result
  ;;                   result
  ;;                   (cl-mpm/utils:voigt-zeros))))
  ;   (magicl:mult elastic-matrix strain :target result)
  ;;   result)
  (let ((result (if result
                    result
                    (cl-mpm/utils:voigt-zeros))))
    (cl-mpm/fastmaths::fast-@-tensor-voigt elastic-matrix strain result)
    result))

(declaim (ftype (function (magicl:matrix/double-float double-float double-float)
                          magicl:matrix/double-float
                          ) linear-elastic))
(defun linear-elastic (strain E nu)
  "Isotropic linear-elastic constitutive model"
   (cl-mpm/fastmaths::fast-@-tensor-voigt (linear-elastic-matrix E nu) strain))
