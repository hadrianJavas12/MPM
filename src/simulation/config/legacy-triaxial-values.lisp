(in-package :cl-mpm/calibration/triaxial)

(defun value (config key default)
  (gethash key config default))

(defun num (config key default)
  (let ((v (value config key default)))
    (unless (and (realp v) (not (sb-ext:float-nan-p (float v 1d0)))
                 (not (sb-ext:float-infinity-p (float v 1d0))))
      (error "~A must be finite" key))
    (float v 1d0)))

(defun finite-p (v)
  (and (realp v) (not (sb-ext:float-nan-p (float v 1d0)))
       (not (sb-ext:float-infinity-p (float v 1d0)))))
