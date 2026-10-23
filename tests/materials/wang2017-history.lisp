;;;; Windows native coordinate controls; no settling or solver steps.
;;;; windows\cl-mpm.cmd tests\materials\wang2017-history.lisp FRESH.json
(in-package :cl-user)
(require :asdf)
(ql:quickload '(:cl-mpm/models/wang2017 :yason) :silent t)

(defpackage :cl-mpm/tests/wang2017-history
  (:use :cl :cl-mpm/models/wang2017))
(in-package :cl-mpm/tests/wang2017-history)

(defvar *labels* nil)
(defvar *failures* nil)
(defun close-p (value expected)
  (<= (abs (- value expected)) 1d-12))
(defun rejected-p (function)
  (handler-case (progn (funcall function) nil) (error () t)))
(defmacro control (label &body body)
  `(handler-case
       (progn ,@body (push ,label *labels*) (format t "~&PASS: ~A~%" ,label))
     (error (condition)
       (push (format nil "~A: ~A" ,label condition) *failures*)
       (format t "~&FAIL: ~A: ~A~%" ,label condition))))

(control "Zero and hydrostatic plastic strain have zero paper coordinate"
  (assert (zerop (paper-kps #(0 0 0 0 0 0))))
  (assert (zerop (paper-kps #(.04d0 .04d0 .04d0 0 0 0)))))
(control "Uniaxial plastic strain removes one-third trace"
  (assert (close-p (paper-kps #(.03d0 0 0 0 0 0)) (/ .03d0 (sqrt 3d0))))
  (assert (close-p (paper-kps #(.03d0 -.015d0 -.015d0 0 0 0))
                   (* .03d0 (/ (sqrt 3d0) 2d0)))))
(control "All physical tensor shear components enter contraction twice"
  (dolist (tensor '(#(0 0 0 .012d0 0 0) #(0 0 0 0 -.012d0 0)
                     #(0 0 0 0 0 .012d0)))
    (assert (close-p (paper-kps tensor) .012d0))))
(control "Engineering shear conversion is explicit and uses engine component order"
  (let ((engineering #(.01d0 -.02d0 .03d0 .04d0 -.06d0 .08d0)))
    (assert (equalp (engineering-voigt-to-tensor engineering)
                    #(.01d0 -.02d0 .03d0 .02d0 -.03d0 .04d0)))
    (assert (equalp (tensor-to-engineering-voigt
                    (engineering-voigt-to-tensor engineering)) engineering))
    (assert (close-p (paper-kps (engineering-voigt-to-tensor #(0 0 0 0 0 .02d0)))
                     .01d0))))
(control "Hydrostatic offset does not alter a general tensor coordinate"
  (assert (close-p (paper-kps #(.01d0 -.02d0 .03d0 .004d0 -.006d0 .008d0))
                   (paper-kps #(.11d0 .08d0 .13d0 .004d0 -.006d0 .008d0)))))
(control "Forty-five degree rotation converts deviatoric diagonal strain to shear"
  (assert (close-p (paper-kps #(.02d0 -.02d0 0 0 0 0))
                   (paper-kps #(0 0 0 0 0 .02d0)))))
(control "Cyclic axis permutation preserves arbitrary-tensor coordinate"
  (assert (close-p (paper-kps #(.01d0 -.02d0 .03d0 .004d0 -.006d0 .008d0))
                   (paper-kps #(-.02d0 .03d0 .01d0 -.006d0 .008d0 .004d0)))))
(control "Coordinate agrees with independent full-matrix contraction after rotation"
  (let* ((ep #2A((.01d0 .008d0 -.006d0) (.008d0 -.02d0 .004d0)
                (-.006d0 .004d0 .03d0)))
         (theta .37d0) (c (cos theta)) (s (sin theta))
         (q (make-array '(3 3) :initial-contents
                         (list (list c (- s) 0d0) (list s c 0d0) '(0d0 0d0 1d0))))
         (rotated (make-array '(3 3) :initial-element 0d0)))
    (dotimes (i 3) (dotimes (j 3)
      (dotimes (a 3) (dotimes (b 3)
        (incf (aref rotated i j) (* (aref q i a) (aref ep a b) (aref q j b)))))))
    (let* ((mean (/ (loop for i below 3 sum (aref rotated i i)) 3d0))
           (contraction
             (loop for i below 3 sum
               (loop for j below 3 sum
                 (expt (- (aref rotated i j) (if (= i j) mean 0d0)) 2))))
           (rotated-kps
             (paper-kps (vector (aref rotated 0 0) (aref rotated 1 1)
                                (aref rotated 2 2) (aref rotated 1 2)
                                (aref rotated 2 0) (aref rotated 0 1)))))
      (assert (close-p rotated-kps (sqrt (* .5d0 contraction))))
      (assert (close-p rotated-kps
                       (paper-kps #(.01d0 -.02d0 .03d0 .004d0 -.006d0 .008d0)))))))
(control "Monotonic coaxial path has proportional J2 factor sqrt(3)/2"
  (let* ((s0 (make-paper-history))
         (s1 (advance-history s0 #(.01d0 -.005d0 -.005d0 0 0 0)))
         (s2 (advance-history s1 #(.02d0 -.01d0 -.01d0 0 0 0))))
    (assert (close-p (history-kps s2) (* .03d0 (/ (sqrt 3d0) 2d0))))))
(control "Nonproportional signed history differs from accumulated increment norms"
  (let* ((s1 (advance-history (make-paper-history) #(0 0 0 0 0 .01d0)))
         (s2 (advance-history s1 #(0 0 0 .01d0 0 0)))
         (summed-paper-increment-norms .02d0))
    (assert (close-p (history-kps s2) (* .01d0 (sqrt 2d0))))
    (assert (> (abs (- (history-kps s2) summed-paper-increment-norms)) .005d0))))
(control "Reversal cancels tensor norm without silently imposing a maximum"
  (let* ((s1 (make-paper-history #(0 0 0 0 0 .01d0)))
         (s2 (advance-history s1 #(0 0 0 0 0 -.01d0))))
    (assert (zerop (history-kps s2)))
    (assert (close-p (history-kps s1) .01d0))))
(control "History constructor and reader own copies of retained data"
  (let* ((input (vector 0d0 0d0 0d0 0d0 0d0 .01d0))
         (history (make-paper-history input)) (copy (history-tensor history)))
    (setf (aref input 5) 99d0 (aref copy 5) 88d0)
    (assert (close-p (history-kps history) .01d0))))
(control "Invalid candidate cannot alter a committed coordinate state"
  (let ((history (make-paper-history #(0 0 0 0 0 .01d0))))
    (assert (rejected-p (lambda () (advance-history history #(0 0 0 0 0 :invalid)))))
    (assert (close-p (history-kps history) .01d0))))
(control "Malformed tensor components and non-real numbers are rejected"
  (dolist (bad '(nil #(0 0 0) #(0 0 0 0 0 "bad") #(0 0 0 0 0 #C(1 1))))
    (assert (rejected-p (lambda () (paper-kps bad))))))
(control "Soil2 cohesion endpoints, mid-branch and residual tail match paper units"
  (loop for k in '(0d0 .005d0 .01d0 .02d0 .03d0)
        for c in '(30000d0 26250d0 22500d0 15000d0 15000d0)
        do (assert (close-p (soil2-cohesion k) c))))
(control "Cohesion rejects negative, complex and nonnumeric coordinates"
  (dolist (bad '(-.001d0 #C(1 1) :invalid))
    (assert (rejected-p (lambda () (soil2-cohesion bad))))))
(control "Large finite hydrostatic input and residual coordinate avoid intermediate overflow"
  (assert (zerop (paper-kps (vector 1d308 1d308 1d308 0d0 0d0 0d0))))
  (assert (= (soil2-cohesion 1d308) 15000d0)))

(let ((output (first (cl-user::cl-mpm-script-args)))
      (record (make-hash-table :test 'equal)))
  (assert output)
  (setf (gethash "passed" record) (if *failures* 'yason:false t)
        (gethash "controlsCount" record) (length *labels*)
        (gethash "controlLabels" record) (coerce (reverse *labels*) 'vector)
        (gethash "failures" record) (coerce (reverse *failures*) 'vector)
        (gethash "physicalUpdatesExecuted" record) 0
        (gethash "particleAdapterImplemented" record) 'yason:false
        (gethash "scope" record) "Pure fixed-frame paper Eq5-6 signed tensor history and Soil2 cohesion; no native particle coupling, finite-strain transport or slope validation")
  (ensure-directories-exist output)
  (with-open-file (stream output :direction :output :if-exists :error)
    (yason:encode record stream)))
(format t "~&WANG2017 HISTORY: ~D PASS, ~D FAIL; zero physical updates.~%"
        (length *labels*) (length *failures*))
(uiop:quit (if *failures* 1 0))
