(in-package :cl-mpm/framework)

(defun cliff-particle-factory (material)
  (lambda (config block-size h)
    (let* ((counts (mapcar (lambda (s) (max 1 (round (* s (gethash "mpsPerCell" config)) h))) block-size))
           (args (append (material-particle-initargs material)
                         (list :gravity -9.8d0 :gravity-axis
                               (cl-mpm/utils:vector-from-list '(0d0 1d0 0d0))))))
      (cl-mpm/setup::make-mps-from-list
       (apply #'cl-mpm/setup::make-block-mps-list '(0d0 0d0) block-size counts
              (option material :density 1800d0) (material-particle-class material) args)))))
