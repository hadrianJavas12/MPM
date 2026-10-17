;;;; Reference CSV output.
;;;; Extracted without changing the existing numerical expressions.
(in-package :cl-mpm/framework/cliff)

(defun reference-csv-number (value)
  ;; Common Lisp prints double exponents as D; CSV consumers expect E.
  (substitute #\e #\d (string-downcase (format nil "~,12E" value))))

(defun reference-write-row (stream sim phase step time)
  (multiple-value-bind (mass damage-mass) (reference-summary sim)
    (format stream "~{~A~^,~}~%"
            (list step (format nil "~,12F" (if (eq phase :settle) 0d0 time))
                  (format nil "~,12F" (if (eq phase :settle) time 0d0))
                  (string-downcase (symbol-name phase))
                  (reference-csv-number (cl-mpm::sim-mass-scale sim))
                  (reference-csv-number (cl-mpm::sim-stats-energy sim))
                  (reference-csv-number (cl-mpm::sim-stats-work sim))
                  (reference-csv-number (reference-energy-ratio sim))
                  (reference-csv-number (cl-mpm::sim-stats-oobf sim))
                  (reference-csv-number mass) (reference-csv-number damage-mass)
                  (length (cl-mpm:sim-mps sim))))))
