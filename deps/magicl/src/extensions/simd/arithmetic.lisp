;;;; arithmetic.lisp
;;;;
;;;; Author: Sam Sutcliffe

(in-package #:magicl.simd)

;(magicl::defmatrix matrix-simd-2 double-float magicl:tensor/double-float)

;; (define-extensible-function (scale! scale!-simd :simd) (tensor factor))
;; ;; (define-extensible-function (.+! .+!-simd :simd) (tensor factor))

(declaim (inline compatible-matrices-p
                 compatible-vectors-p))
(defun compatible-matrices-p (m1 m2)
  (and
   (eq (magicl::matrix-layout m1)
       (magicl::matrix-layout m2))
   (eq (type-of m1)
       (type-of m2))))

(defun compatible-vectors-p (v1 v2)
  (eq (type-of v1)
      (type-of v2)))

(defmacro with-compatibility-test ((tensor-type) &body body)
  (policy-cond:policy-if (> speed safety)
                         `(cond
                            (,(if (subtypep tensor-type 'matrix)
                                  `(and (compatible-matrices-p source1 source2)
                                        (or (not target) (compatible-matrices-p source1 target)))
                                  `(or (not target) (compatible-vectors-p source1 target)))
                             ,@body)
                            (t (call-next-method)))
                         `(progn
                            ,@body)
                         ))

(declaim (ftype (function (
                           (simple-array double-float)
                           (simple-array double-float)
                           (simple-array double-float)
                           &key (offset fixnum)
                           ) (values)) simd-add-2))
(defun simd-add-2 (a b target &key (offset 0))
  (declare (optimize (speed 3) (debug 0) (safety 0)))
  (declare (type sb-simd:f64vec a b target)
           (fixnum offset))
      (setf (sb-simd-avx:f64.2-aref target offset)
            (sb-simd-avx:f64.2+
             (sb-simd-avx:f64.2-aref a offset)
             (sb-simd-avx:f64.2-aref b offset)
             ))
  (values))

(declaim (ftype (function ((simple-array double-float)
                           (simple-array double-float)
                           (simple-array double-float)
                           &key (offset fixnum)
                           ) (values)) simd-add))
(defun simd-add (a b target &key (offset 0))
  (declare (optimize (speed 3) (debug 0) (safety 0)))
  (declare (type sb-simd:f64vec a b target)
           (fixnum offset))
  (multiple-value-bind (iter remain) (floor (length a) 2)
    (declare (fixnum iter remain))
    (dotimes (i iter)
      (setf (sb-simd-avx:f64.2-aref target offset)
            (sb-simd-avx:f64.2+
             (sb-simd-avx:f64.2-aref a offset)
             (sb-simd-avx:f64.2-aref b offset)
             ))
      (incf offset 2)
      )
    (unless (eq remain 0)
      (dotimes (i remain)
        (setf (aref target offset)
              (+ (aref a offset) (aref b offset)))
        (incf offset 1))
      )
    )
  target)

(defun simd-mult (a b target &key (offset 0))
  (declare (optimize (speed 3) (debug 0) (safety 0)))
  (declare (type sb-simd:f64vec a b target)
           (fixnum offset))
  (multiple-value-bind (iter remain) (floor (length a) 2)
    (declare (fixnum iter remain))
    (dotimes (i iter)
      (setf (sb-simd-avx:f64.2-aref target offset)
            (sb-simd-avx:f64.2*
             (sb-simd-avx:f64.2-aref a offset)
             (sb-simd-avx:f64.2-aref b offset)
             ))
      (incf offset 2)
      )
    (unless (eq remain 0)
      (dotimes (i remain)
        (setf (aref target offset)
              (* (aref a offset) (aref b offset)))
        (incf offset 1))
      )
    )
  target)



(define-extensible-function (.+ .+-simd :simd) (source1 source2 &optional target))
(define-extensible-function (.* .*-simd :simd) (source1 source2 &optional target))

(defmethod .+-simd ((source1 magicl::matrix/double-float)
                    (source2 magicl::matrix/double-float)
                    &optional target)
  (with-compatibility-test (magicl::matrix/double-float)
   (policy-cond:with-expectations (> speed safety)
       ((assertion (equalp (shape source1)
                           (shape source2)))))
  (if target
      (progn
        (simd-add (magicl::storage source1) (magicl::storage source2) (magicl::storage target))
        target)
      (let ((target (deep-copy-tensor source1)))
        (simd-add (magicl::storage source1) (magicl::storage source2) (magicl::storage target))
        target))
    ))
(defun .+-simd (source1 source2
                  &optional target)
  (declare (magicl::matrix/double-float source1 source2))
  (if target
      (progn
        (simd-add (magicl::storage source1) (magicl::storage source2) (magicl::storage target))
        target)
      (let ((target (deep-copy-tensor source1)))
        (simd-add (magicl::storage source1) (magicl::storage source2) (magicl::storage target))
        target)))

(defun .+-unsafe (source1 source2
                  &optional target)
  (declare (magicl::matrix/double-float source1 source2))
    (if target
        (progn
          (simd-add (magicl::storage source1) (magicl::storage source2) (magicl::storage target))
          target)
        (let ((target (deep-copy-tensor source1)))
          (simd-add (magicl::storage source1) (magicl::storage source2) (magicl::storage target))
          target)))

(defmethod .*-simd ((source1 magicl::matrix/double-float)
                    (source2 magicl::matrix/double-float)
                    &optional target)
  (with-compatibility-test (magicl::matrix/double-float)
    (policy-cond:with-expectations (> speed safety)
        ((assertion (equalp (shape source1)
                            (shape source2)))))
    (if target
        (progn
          (simd-mult (magicl::storage source1) (magicl::storage source2) (magicl::storage target))
          target)
        (let ((target (deep-copy-tensor source1)))
          (simd-mult (magicl::storage source1) (magicl::storage source2) (magicl::storage target))
          target))
    ))

;; (defmethod .+-simd ((source1 matrix-simd-2)
;;                     (source2 matrix-simd-2)
;;                     &optional target)
;;   (with-compatibility-test (magicl::matrix/double-float)
;;     (policy-cond:with-expectations (> speed safety)
;;         ((assertion (equalp (shape source1)
;;                             (shape source2)))))
;;     (if target
;;         (progn
;;           (simd-add (magicl::storage source1) (magicl::storage source2) (magicl::storage target))
;;           target)
;;         (let ((target (deep-copy-tensor source1)))
;;           (simd-add (magicl::storage source1) (magicl::storage source2) (magicl::storage target))
;;           target))
;;     ))


;(fast-generic-functions:seal-domain #'magicl.simd::.+-simd '(magicl:matrix/double-float magicl:matrix/double-float))

;; (defmethod .+-simd ((tensor matrix/double-float)
;;                     (factor double-float))
;;   tensor)


;; (declaim (ftype magicl::allocator simd-allocator))
;; (defun simd-allocator (size element-type initial-element)
;;   (print "Hello simd allocator")
;;   (let ((storage
;;           ;; (apply #'make-array
;;           ;;               size
;;           ;;               :element-type element-type
;;           ;;               (if initial-element
;;           ;;                   (list ':initial-element (coerce initial-element element-type))
;;           ;;                   nil))
;;           ))
;;     (values storage
;;             #'magicl::dummy-finalizer)))

;; ;; Scalar - matrix multiplication
;; (macrolet ((def-scale (matrix-type scalar-type function)
;;              `(defmethod scale!-blas ((tensor ,matrix-type)
;;                                       (factor ,scalar-type))
;;                 (,function
;;                  (magicl::size tensor)
;;                  factor
;;                  (magicl::storage tensor)
;;                  1)
;;                 tensor)))
;;   (def-scale matrix/single-float single-float magicl.blas-cffi:%sscal)
;;   (def-scale matrix/double-float double-float magicl.blas-cffi:%dscal)
;;   (def-scale vector/single-float single-float magicl.blas-cffi:%sscal)
;;   (def-scale vector/double-float double-float magicl.blas-cffi:%dscal))

;; (declaim (inline compatible-matrices-p
;;                  compatible-vectors-p))
;; (defun compatible-matrices-p (m1 m2)
;;   (and
;;    (eq (magicl::matrix-layout m1)
;;        (magicl::matrix-layout m2))
;;    (eq (type-of m1)
;;        (type-of m2))))

;; (defun compatible-vectors-p (v1 v2)
;;   (eq (type-of v1)
;;       (type-of v2)))

;; (defmacro with-compatibility-test ((tensor-type) &body body)
;;   `(cond
;;      (,(if (subtypep tensor-type 'matrix)
;;            `(and (compatible-matrices-p source1 source2)
;;                  (or (not target) (compatible-matrices-p source1 target)))
;;            `(or (not target) (compatible-vectors-p source1 target)))
;;       ,@body)
;;      (t (call-next-method))))

;; (defgeneric copy-to/w-same-layout (source target)
;;   (:documentation "Fast copy from SOURCE to TARGET with the same
;; layout. If TARGET is NIL, this function works just like
;; DEEP-COPY-TENSOR."))

;; (defmethod copy-to/w-same-layout ((source abstract-tensor)
;;                                   (target null))
;;   (deep-copy-tensor source))

;; (macrolet ((def-copier (tensor-type scalar-type)
;;              `(defmethod copy-to/w-same-layout ((source ,tensor-type)
;;                                                 (target ,tensor-type))
;;                 (declare (optimize (speed 3)))
;;                 (when (not (eq source target))
;;                   (let ((storage-t (magicl::storage target))
;;                         (storage-s (magicl::storage source)))
;;                     (declare (type (simple-array ,scalar-type)
;;                                    storage-s storage-t))
;;                     (replace storage-t storage-s)))
;;                 target)))
;;   (def-copier matrix/single-float single-float)
;;   (def-copier matrix/double-float double-float)
;;   (def-copier vector/single-float single-float)
;;   (def-copier vector/double-float double-float))

;; (define-extensible-function (.+ .+-blas :blas) (source1 source2 &optional target))
;; (define-extensible-function (.- .--blas :blas) (source1 source2 &optional target))
;; (define-extensible-function (.* .*-blas :blas) (source1 source2 &optional target))
;; (define-extensible-function (./ ./-blas :blas) (source1 source2 &optional target))

;; ;; Fast matrix/vector addition
;; (macrolet ((def-+ (tensor-type scalar-type function)
;;              `(defmethod .+-blas ((source1 ,tensor-type)
;;                                   (source2 ,tensor-type)
;;                                   &optional target)
;;                 (with-compatibility-test (,tensor-type)
;;                   (policy-cond:with-expectations (> speed safety)
;;                       ((assertion (equalp (shape source1)
;;                                           (shape source2)))))
;;                   (let ((source1 (if (eq target source1)
;;                                      (deep-copy-tensor source1)
;;                                      source1))
;;                         (source2 (copy-to/w-same-layout source2 target)))
;;                     (,function
;;                      (magicl::size source2)
;;                      (coerce 1 ',scalar-type)
;;                      (magicl::storage source1) 1
;;                      (magicl::storage source2) 1)
;;                     source2)))))
;;   (def-+ matrix/single-float single-float magicl.blas-cffi:%saxpy)
;;   (def-+ matrix/double-float double-float magicl.blas-cffi:%daxpy)
;;   (def-+ vector/single-float single-float magicl.blas-cffi:%saxpy)
;;   (def-+ vector/double-float double-float magicl.blas-cffi:%daxpy))

;; ;; Fast matrix/vector subtraction
;; (macrolet ((def-- (tensor-type scalar-type function)
;;              `(defmethod .--blas ((source1 ,tensor-type)
;;                                   (source2 ,tensor-type)
;;                                   &optional target)
;;                 (with-compatibility-test (,tensor-type)
;;                   (policy-cond:with-expectations (> speed safety)
;;                       ((assertion (equalp (shape source1)
;;                                           (shape source2)))))
;;                   (let ((source2 (if (eq target source2)
;;                                      (deep-copy-tensor source2)
;;                                      source2))
;;                         (source1 (copy-to/w-same-layout source1 target)))
;;                     (,function
;;                      (magicl::size source2)
;;                      (coerce -1 ',scalar-type)
;;                      (magicl::storage source2) 1
;;                      (magicl::storage source1) 1)
;;                     source1)))))
;;   (def-- matrix/single-float single-float magicl.blas-cffi:%saxpy)
;;   (def-- matrix/double-float double-float magicl.blas-cffi:%daxpy)
;;   (def-- vector/single-float single-float magicl.blas-cffi:%saxpy)
;;   (def-- vector/double-float double-float magicl.blas-cffi:%daxpy))

;; ;; Fast matrix/vector element-wise multiplication/division

;; (macrolet ((def-op (name tensor-type scalar-type function)
;;              `(defmethod ,name ((source1 ,tensor-type)
;;                                 (source2 ,tensor-type)
;;                                 &optional target)
;;                 (declare (optimize (speed 3)))
;;                 (with-compatibility-test (,tensor-type)
;;                   (policy-cond:with-expectations (> speed safety)
;;                       ((assertion (equalp (shape source1)
;;                                           (shape source2)))))
;;                   (let ((target
;;                           (or target
;;                               (empty (shape source1) :type ',scalar-type))))
;;                     (let ((target-st  (magicl::storage target))
;;                           (source1-st (magicl::storage source1))
;;                           (source2-st (magicl::storage source2)))
;;                       (declare (type (simple-array ,scalar-type)
;;                                      target-st source1-st source2-st))
;;                       (map-into target-st #',function source1-st source2-st))
;;                     target)))))
;;   (def-op .*-blas matrix/single-float single-float *)
;;   (def-op .*-blas matrix/double-float double-float *)
;;   (def-op ./-blas matrix/single-float single-float /)
;;   (def-op ./-blas matrix/double-float double-float /)
;;   (def-op .*-blas vector/single-float single-float *)
;;   (def-op .*-blas vector/double-float double-float *)
;;   (def-op ./-blas vector/single-float single-float /)
;;   (def-op ./-blas vector/double-float double-float /))
