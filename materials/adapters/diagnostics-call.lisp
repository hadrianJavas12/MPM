(in-package :cl-mpm/calibration/triaxial)

(defun material-diagnostic-call (name &rest arguments)
  "Optional framework protocol; the historical standalone VM loader stays independent."
  (let* ((package (find-package :cl-mpm/framework))
         (function (and package (find-symbol name package))))
    (unless (and function (fboundp function))
      (error "Material diagnostics require the native framework protocol ~A." name))
    (apply function arguments)))
