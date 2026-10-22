(in-package :cl-mpm/scenario/slope-descent)

(defclass slope-sim (cl-mpm::mpm-sim-usf)
  ((free-residual :initform 1d0 :accessor free-residual)))

(defun surface-height (base height crest slope x)
  (+ base (max 0d0 (- height (* slope (max 0d0 (- x crest)))))))

(defmethod cl-mpm::update-node-forces :after ((sim slope-sim))
  "Measure undamped physical imbalance before essential BCs erase constrained forces."
  (let ((residual2 0d0) (external2 0d0))
    (cl-mpm:iterate-over-nodes (cl-mpm:sim-mesh sim)
      (lambda (node)
        (when (cl-mpm/mesh:node-active node)
          (dotimes (axis 2)
            (let* ((external (component (cl-mpm/mesh::node-external-force node) axis))
                   (internal (component (cl-mpm/mesh::node-internal-force node) axis))
                   (mask (cl-mpm/mesh::node-bcs node)))
              (incf external2 (* external external))
              (when (or (null mask) (> (component mask axis) .5d0))
                (incf residual2 (expt (+ external internal) 2))))))))
    (setf (free-residual sim) (sqrt (/ residual2 (max external2 1d-30))))))

(defun make-slope (material config)
  "Return native sim and the original crest top row, selected before gravity movement."
  (let* ((h (gethash "meshSize" config)) (width (gethash "width" config))
         (height (gethash "height" config)) (base (gethash "baseHeight" config))
         (crest (gethash "crestLength" config))
         (slope (tan (* pi (/ (gethash "slope" config) 180d0))))
         (ny (* (ceiling (+ height base) h) (gethash "mpsPerCell" config)))
         (nx (* (ceiling width h) (gethash "mpsPerCell" config)))
         (dy (/ (+ height base) ny))
         (sim (cl-mpm/setup:make-simple-sim
               h (list (ceiling width h) (ceiling (+ height base (* 5d0 h)) h))
               :sim-type 'slope-sim
               :args-list (list :enable-fbar nil :enable-damage nil :ghost-factor nil
                                :enable-split nil :mp-removal-size nil)))
         (args (cl-mpm/framework:material-particle-initargs material))
         (mps (apply #'cl-mpm/setup:make-block-mps '(0d0 0d0)
                     (list width (+ base height)) (list nx ny)
                     (gethash "density" config)
                     (cl-mpm/framework:material-particle-class material)
                     :gravity (gethash "gravity" config)
                     :gravity-axis (cl-mpm/utils:vector-from-list '(0d0 1d0 0d0))
                     :clip-func (lambda (x y z)
                                  (declare (ignore z))
                                  (<= y (surface-height base height crest slope x)))
                     args)))
    (setf mps (remove-if-not (lambda (mp) (typep mp 'cl-mpm/particle:particle)) mps))
    (cl-mpm:add-mps sim mps)
    (setf (cl-mpm:sim-gravity sim) (gethash "gravity" config)
          (cl-mpm::sim-mass-scale sim) 1d0
          (cl-mpm::sim-mass-filter sim) 1d-15
          (cl-mpm::sim-mp-removal-size sim) nil
          (cl-mpm:sim-allow-mp-split sim) nil
          (cl-mpm::sim-velocity-algorithm sim) :FLIP)
    ;; Free top, x rollers on sides, fixed bottom; z constraints are inert in 2D.
    (setf (cl-mpm:sim-bcs sim)
          (cl-mpm/bc::make-outside-bc-var
           (cl-mpm:sim-mesh sim)
           (lambda (i) (cl-mpm/bc:make-bc-fixed i '(0 nil nil)))
           (lambda (i) (cl-mpm/bc:make-bc-fixed i '(0 nil nil)))
           (lambda (i) (cl-mpm/bc:make-bc-fixed i '(nil nil nil)))
           (lambda (i) (cl-mpm/bc:make-bc-fixed i '(0 0 nil)))
           (lambda (i) (cl-mpm/bc:make-bc-fixed i '(nil nil 0)))
           (lambda (i) (cl-mpm/bc:make-bc-fixed i '(nil nil 0)))))
    (values sim
            (remove-if-not
             (lambda (mp)
               (and (> (component (cl-mpm/particle:mp-position mp) 1)
                       (- (+ base height) (* .75d0 dy)))
                    (<= (component (cl-mpm/particle:mp-position mp) 0) crest))) mps))))
