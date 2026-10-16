(in-package :cl-mpm/constitutive)

(declaim #.cl-mpm/settings:*optimise-setting*)



(let ((mandel-constant
        (magicl:from-list (list 1d0 1d0 (sqrt 2)
                                1d0 1d0 (sqrt 2)
                                (sqrt 2) (sqrt 2) 2d0) '(3 3))))
  (defun voigt-4th-to-mandel (tensor)
    (cl-mpm/fastmaths::fast-.* tensor mandel-constant))
  (defun mandel-to-voigt-4th (tensor)
    (magicl:./ tensor mandel-constant))
  )

(declaim (inline voight-eye)
         (ftype (function (double-float) magicl:matrix/double-float) voight-eye))
(defun voight-eye (val)
  ;(let ((arr (make-array 3 :element-type 'double-float :initial-contents (list val val 0d0))))
  ;  (magicl:from-array arr '(3 1) :layout :column-major))
  ;; (magicl:from-array (make-array 3 :element-type 'double-float :initial-contents (list val val 0d0))
  ;;                    '(3 1) :layout :column-major)
  (cl-mpm/utils:voigt-from-list (list val val val 0d0 0d0 0d0)))
(declaim (inline voight-trace)
         (ftype (function (magicl:matrix/double-float) double-float) voight-trace))
(defun voight-trace (m)
  "Take the trace of a voigt notation stress vector"
  (let ((s (magicl::matrix/double-float-storage m)))
    (+ (the double-float (aref s 0))
       (the double-float (aref s 1))
       (the double-float (aref s 2)))))

(defun deviatoric (voigt)
  (deviatoric-voigt voigt)
  ;; (let* ((mat (voight-to-matrix voigt))
  ;;        (trace (/ (magicl:trace mat) 3d0)))
  ;;   (matrix-to-voight (magicl:.- mat (magicl:eye 3 :value (the double-float trace)))))
  )

(defun deviatoric-mat (mat)
  (let* ((trace (/ (magicl:trace mat) 3d0)))
    (matrix-to-voight (magicl:.- mat (magicl:eye 3 :value (the double-float trace))))))

(defun effective-strain-rate (strain)
  (sqrt
   (* 0.5d0
      (cl-mpm/fastmaths::voigt-tensor-reduce-simd
       (deviatoric strain)))))

(declaim (ftype (function (magicl:matrix/double-float) double-float) voigt-j2))
(defun voigt-j2 (s)
  "Calculate j2 invarient from deviatoric stress"
  (let ((storage (magicl::matrix/double-float-storage s)))
    (/ (+ (the double-float (cl-mpm/fastmaths:dot s s))
          (the double-float (expt (aref storage 3) 2))
          (the double-float (expt (aref storage 4) 2))
          (the double-float (expt (aref storage 5) 2))
          ) 2d0)))

(defun b-norm (b)
  (sqrt (loop for i from 0 below 6
             sum (expt (magicl:tref b i 0) 2))))

(defun rotate-vector (vec)
  (vector-from-list (list (magicl:tref vec 1 0)
                          (magicl:tref vec 2 0)
                          (magicl:tref vec 0 0))))
(defun swizzle-voigt->coombs (vec)
  (voigt-from-list (list
                    (varef vec 0)
                    (varef vec 1)
                    (varef vec 2)
                    (varef vec 5)
                    (varef vec 3)
                    (varef vec 4)
                    )))
(defun swizzle-coombs->voigt (vec &optional res)
  (let ((res (if res
                 res
                 (cl-mpm/utils:voigt-zeros))))
    (setf
     (varef res 0) (varef vec 0)
     (varef res 1) (varef vec 1)
     (varef res 2) (varef vec 2)
     (varef res 3) (varef vec 4)
     (varef res 4) (varef vec 5)
     (varef res 5) (varef vec 3))
    res))



(defun Q-matrix (v)
  (magicl:transpose!
   (magicl:block-matrix
    (list
     (cl-mpm/fastmaths::fast-.* (cl-mpm/utils::matrix-column v 0) (cl-mpm/utils::matrix-column v 0))

     (cl-mpm/fastmaths::fast-.* (cl-mpm/utils::matrix-column v 1) (cl-mpm/utils::matrix-column v 1))
     (cl-mpm/fastmaths::fast-.* (cl-mpm/utils::matrix-column v 2) (cl-mpm/utils::matrix-column v 2))

     (magicl:scale!
      (cl-mpm/fastmaths::fast-.* (cl-mpm/utils::matrix-column v 0) (cl-mpm/utils::matrix-column v 1)) 2d0)
     (magicl:scale!
      (cl-mpm/fastmaths::fast-.* (cl-mpm/utils::matrix-column v 1) (cl-mpm/utils::matrix-column v 2)) 2d0)
     (magicl:scale!
      (cl-mpm/fastmaths::fast-.* (cl-mpm/utils::matrix-column v 2) (cl-mpm/utils::matrix-column v 0)) 2d0)

     (cl-mpm/fastmaths::fast-.* (cl-mpm/utils::matrix-column v 0) (rotate-vector (cl-mpm/utils::matrix-column v 0)))
     (cl-mpm/fastmaths::fast-.* (cl-mpm/utils::matrix-column v 1) (rotate-vector (cl-mpm/utils::matrix-column v 1)))
     (cl-mpm/fastmaths::fast-.* (cl-mpm/utils::matrix-column v 2) (rotate-vector (cl-mpm/utils::matrix-column v 2)))

     (magicl:scale! (cl-mpm/fastmaths::fast-.+
                     (cl-mpm/fastmaths::fast-.* (cl-mpm/utils::matrix-column v 0)
                                               (rotate-vector (cl-mpm/utils::matrix-column v 1)))
                     (cl-mpm/fastmaths::fast-.* (cl-mpm/utils::matrix-column v 1)
                                               (rotate-vector (cl-mpm/utils::matrix-column v 0)))) 1d0)

     (magicl:scale! (cl-mpm/fastmaths::fast-.+
                     (cl-mpm/fastmaths::fast-.* (cl-mpm/utils::matrix-column v 1)
                                               (rotate-vector (cl-mpm/utils::matrix-column v 2)))
                     (cl-mpm/fastmaths::fast-.* (cl-mpm/utils::matrix-column v 2)
                                               (rotate-vector (cl-mpm/utils::matrix-column v 1)))) 1d0)
     (magicl:scale! (cl-mpm/fastmaths::fast-.+
                     (cl-mpm/fastmaths::fast-.* (cl-mpm/utils::matrix-column v 2)
                                               (rotate-vector (cl-mpm/utils::matrix-column v 0)))
                     (cl-mpm/fastmaths::fast-.* (cl-mpm/utils::matrix-column v 0)
                                               (rotate-vector (cl-mpm/utils::matrix-column v 2)))) 1d0)
     ) '(2 6))))
