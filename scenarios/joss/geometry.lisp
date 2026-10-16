;;;; Joss face, notch and domain clipping.
;;;; Extracted without changing the existing numerical expressions.
(in-package :cl-mpm/framework/cliff)

(defun reference-face-x (config y)
  (let* ((base (param config "soilBoundary"))
         (height (param config "shelfHeight"))
         (toe (* height (param config "shelfAspect")))
         (lower-height (- height (param config "upperVerticalHeight")))
         (inward-per-height (/ 1d0 (tan (deg->rad (param config "cliffSlope"))))))
    (- toe (* inward-per-height (min lower-height (max 0d0 (- y base)))))))

(defun reference-solid-p (config x y)
  (let* ((base (param config "soilBoundary"))
         (toe (* (param config "shelfHeight") (param config "shelfAspect")))
         (notch (param config "notchDepth")))
    (or (<= y base)
        (and (<= x (reference-face-x config y))
             ;; 45-degree wave-notch ramp; foundation is preserved.
             (>= (- y base) (+ (- x toe) notch))))))

(defun reference-surface-height (config x)
  (let* ((base (param config "soilBoundary"))
         (height (param config "shelfHeight"))
         (toe (* height (param config "shelfAspect")))
         (kink-x (reference-face-x config (+ base height))))
    (cond ((<= x kink-x) (+ base height))
          ((< x toe) (+ base (* (- toe x) (tan (deg->rad (param config "cliffSlope"))))))
          (t base))))

(defun reference-domain-corners (config mp)
  (let* ((position (cl-mpm/particle:mp-position mp))
         (size (cl-mpm/particle::mp-domain-size mp))
         (x (cl-mpm/utils:varef position 0))
         (y (cl-mpm/utils:varef position 1))
         (dx (* 0.5d0 (cl-mpm/utils:varef size 0)))
         (dy (* 0.5d0 (cl-mpm/utils:varef size 1))))
    (loop for sx in '(-1d0 1d0) append
      (loop for sy in '(-1d0 1d0)
            collect (reference-solid-p config (+ x (* sx dx)) (+ y (* sy dy)))))))

(defun reference-clip-geometry (sim config)
  ;; Each loop is one bisection of partially intersecting domains, at most the
  ;; prescribed count per MP; reject fully removed domains between bisections.
  (dotimes (depth (param config "geometryRefinement"))
    (cl-mpm::split-mps-criteria
     sim
     (lambda (mp h)
       (declare (ignore h))
       (let ((corners (reference-domain-corners config mp)))
         (when (and (some #'identity corners) (not (every #'identity corners)))
           (if (>= (cl-mpm/utils:varef (cl-mpm/particle::mp-domain-size mp) 0)
                   (cl-mpm/utils:varef (cl-mpm/particle::mp-domain-size mp) 1))
               :x :y)))))
    (cl-mpm::remove-mps-func sim
      (lambda (mp) (not (some #'identity (reference-domain-corners config mp))))))
  (cl-mpm::remove-mps-func
   sim
   (lambda (mp)
     (not (reference-solid-p config
             (cl-mpm/utils:varef (cl-mpm/particle:mp-position mp) 0)
             (cl-mpm/utils:varef (cl-mpm/particle:mp-position mp) 1)))))
  sim)
