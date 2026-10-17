(in-package :cl-mpm/constitutive)

(declaim #.cl-mpm/settings:*optimise-setting*)





(defun secant-hardening (plasticity-func ps-0 ps-hardening-func)
  (let ()
    (labels ((fkn (k)
               (+
                ps-0
                (funcall ps-hardening-func (funcall plasticity-func k))))
             (f (k)
               (-
                (fkn k)
                k)))
      (let* ((kn ps-0)
             (kn1 (fkn kn))
             (rn (f kn))
             (rn1 (f kn1)))
        ;; (format t "~A ~A ~%" kn1 kn)
        ;; (format t "~A ~A ~%" rn rn1)
        (if (= kn1 kn)
            kn
            (progn
              (loop for i from 0 to 100
                    while (and (> (abs (- rn rn1)) 1d-9)
                               (> (abs (- kn kn1)) 0d0)
                               ;; (> (abs rn) 0d0)
                               ;; (> (abs rn1) 0d0)
                               )
                    do
                       ;; (format t "iter ~D - error ~E~%" i (abs (- rn rn1)))
                       ;; (format t "kn ~E - kn1 ~E~%" kn kn1)
                       ;; (format t "rn ~E - kn1 ~E~%" rn rn1)
                       (when (> (abs (- kn kn1)) 0d0)
                         (let ((inc (*
                                     rn
                                     (/
                                      (- kn kn1)
                                      (- rn rn1)))))
                           (setf kn1 kn
                                 rn1 rn)
                           (setf
                            kn (- kn inc))
                           (setf
                            rn (f kn))
                           )))
              (fkn kn)))))))
