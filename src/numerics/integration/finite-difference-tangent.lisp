(in-package :cl-mpm/particle)

(declaim #.cl-mpm/settings:*optimise-setting*)



(defun diff-tangent (func strain)
  (let ())
  (let ((stress-0 (funcall func (voigt-copy strain)))
        (de (cl-mpm/utils::tensor-voigt-4th-zeros))
        (eps 1d-9))
    (loop for i from 0 below 6
          do (loop for j from 0 below 6
                   do (labels ((probe (eps)
                                 (let ((tstrain (cl-mpm/utils::voigt-copy strain)))
                                   (incf (varef tstrain j) eps)
                                   (let ((stress (funcall func tstrain)))
                                     (- (varef stress-0 i) (varef stress i))))))
                        (setf (mtref de i j)
                              (/ (- (probe eps) (probe (- eps)))
                                 (* -2 eps))))))
    (let ((mapping-list (list 0 1 2 5 3 4))
          ;;Potentially corrected listing?
          ;; (mapping-list (list 0 1 2 5 5 3 3 4 4))
          (result (cl-mpm/utils::arb-matrix 9 9)))
      (loop for i from 0
            for im in mapping-list
            do
               (loop for j from 0
                     for jm in mapping-list
                     do (setf (magicl:tref result i j) (magicl:tref de im jm))))
      result)
    de))
