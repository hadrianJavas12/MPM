(in-package :cl-mpm/scenario/gravity-slope)

;; Inherit only the read-only free-force residual diagnostic. This dependency
;; is loaded before this scenario by cl-mpm-framework.asd; no strip is built.
(defclass gravity-slope-sim (cl-mpm/scenario/slope-descent::slope-sim) ())

(defun ramp-factor (time duration)
  "Smoothstep gravity ramp evaluated at the actual explicit step endpoint."
  (unless (and (finite-p time) (>= time 0d0) (finite-p duration) (> duration 0d0))
    (error "Gravity ramp requires finite nonnegative time and positive duration."))
  (let ((r (min 1d0 (/ time duration))))
    (* r r (- 3d0 (* 2d0 r)))))

(defun slope-surface (config x)
  (max 0d0 (- (gethash "height" config)
              (* (tan (* pi (/ (gethash "slope" config) 180d0)))
                 (max 0d0 (- x (gethash "crestLength" config)))))))

(defun build-slope (material config)
  "Construct only the native unnotched MPs/grid/BCs; performs zero updates."
  (let* ((h (gethash "meshSize" config))
         (width (gethash "width" config)) (height (gethash "height" config))
         (ppc (gethash "mpsPerCell" config))
         (sim (cl-mpm/setup:make-simple-sim
               h (list (round (gethash "domainWidth" config) h)
                       (round (gethash "domainHeight" config) h))
               :sim-type 'gravity-slope-sim
               :args-list (list :enable-fbar nil :enable-damage nil :ghost-factor nil
                                :enable-split nil :mp-removal-size nil)))
         (mps (apply #'cl-mpm/setup:make-block-mps '(0d0 0d0)
                     (list width height)
                     (list (* (round width h) ppc) (* (round height h) ppc))
                     (gethash "density" config)
                     (cl-mpm/framework:material-particle-class material)
                     :gravity 0d0
                     :gravity-axis (cl-mpm/utils:vector-from-list '(0d0 1d0 0d0))
                     :body-force (cl-mpm/utils:vector-from-list '(0d0 0d0 0d0))
                     :clip-func (lambda (x y z)
                                  (declare (ignore z)) (<= y (slope-surface config x)))
                     (cl-mpm/framework:material-particle-initargs material))))
    (cl-mpm:add-mps sim (remove-if-not (lambda (mp) (typep mp 'cl-mpm/particle:particle)) mps))
    (unless (plusp (length (cl-mpm:sim-mps sim))) (error "Gravity slope contains no particles."))
    (setf (cl-mpm:sim-gravity sim) 0d0
          (cl-mpm:sim-damping-factor sim) 0d0
          (cl-mpm::sim-mass-scale sim) 1d0
          (cl-mpm::sim-mass-filter sim) 1d-15
          (cl-mpm::sim-mp-removal-size sim) nil
          (cl-mpm:sim-allow-mp-split sim) nil
          (cl-mpm::sim-velocity-algorithm sim) :FLIP
          (cl-mpm::sim-bcs-force-list sim) nil)
    ;; Order is left, right, top, bottom, front, back in make-outside-bc-var.
    (setf (cl-mpm:sim-bcs sim)
          (cl-mpm/bc::make-outside-bc-var
           (cl-mpm:sim-mesh sim)
           (lambda (i) (cl-mpm/bc:make-bc-fixed i '(0 nil nil)))
           (lambda (i) (cl-mpm/bc:make-bc-fixed i '(0 nil nil)))
           (lambda (i) (cl-mpm/bc:make-bc-fixed i '(nil nil nil)))
           (lambda (i) (cl-mpm/bc:make-bc-fixed i '(0 0 nil)))
           (lambda (i) (cl-mpm/bc:make-bc-fixed i '(nil nil 0)))
           (lambda (i) (cl-mpm/bc:make-bc-fixed i '(nil nil 0)))))
    sim))
