;;;; Ordinary cliff face and toe-notch cutting.
;;;; Extracted without changing the existing numerical expressions.
(in-package :cl-mpm/framework/cliff)

(defun cut-cliff-face (sim config shelf-length soil)
  "Remove material in front of the (possibly inclined or overhanging) face."
  (let* ((deviation (+ (- (param config "cliffSlope") 90d0) (param config "undercut")))
         (angle (- (deg->rad deviation)))
         (normal (magicl:from-list (list (cos angle) (sin angle)) '(2 1)))
         (toe (magicl:from-list (list shelf-length soil) '(2 1) :type 'double-float)))
    (cl-mpm/setup:remove-sdf
     sim
     (lambda (p)
       (if (> (magicl:tref p 1 0) soil)
           (cl-mpm/setup::plane-point-sdf
            (magicl:from-list (list (magicl:tref p 0 0) (magicl:tref p 1 0)) '(2 1))
            normal toe)
           1d0)))))

(defun cut-toe-notch (sim config shelf-length soil)
  "Remove a rectangular, elliptic or triangular toe notch.
The notch dimensions follow the legacy convention: notchDepth measures
inward from the original face at x=SHELF-LENGTH; 0 means 1.5 x height.
The tip fraction affects triangular notches only."
  (let ((notch-h (param config "notchHeight")))
    (when (> notch-h 1d-2)
      (let* ((depth (param config "notchDepth"))
             (notch-d (if (> depth 1d-2) depth (* 1.5d0 notch-h)))
             (half-h (* 0.5d0 notch-h))
             (centre-y (+ soil half-h))
             (shape (param config "notchShape"))
             (tip-y (+ soil (* notch-h (param config "notchTipFraction"))))
             (sdf (ecase shape
                    (:rectangle
                     (cl-mpm/setup::rectangle-sdf
                      (list shelf-length centre-y) (list notch-d half-h)))
                    (:ellipse
                     (cl-mpm/setup::ellipse-sdf
                      (list shelf-length centre-y 0d0) notch-d half-h))
                    (:triangle
                     ;; REMOVE-SDF uses only the sign of the supplied function.
                     ;; A triangle has a tip at (face-depth, tip-y) and an
                     ;; open vertical edge along the original cliff face.
                     (lambda (p)
                       (let* ((x (magicl:tref p 0 0))
                              (y (magicl:tref p 1 0))
                              (inside-y (and (> y soil) (< y (+ soil notch-h))))
                              (fraction (if inside-y
                                            (if (< y tip-y)
                                                (/ (- y soil) (- tip-y soil))
                                                (/ (- (+ soil notch-h) y)
                                                   (- (+ soil notch-h) tip-y)))
                                            0d0))
                              (left-x (- shelf-length (* notch-d fraction))))
                         (if (and inside-y
                                  (> x left-x) (< x shelf-length))
                             -1d0 1d0)))))))
        (cl-mpm/setup:remove-sdf
         sim
         (lambda (p)
           ;; Do not cut through the underlying soil/foundation layer.
           (if (> (magicl:tref p 1 0) soil)
               (funcall sdf p)
               1d0)))))))
