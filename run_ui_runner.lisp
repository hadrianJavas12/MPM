;;; ========================================================
;;; CL-MPM UI Simulation Runner
;;; Dynamically configured from Web Studio
;;; ========================================================
(in-package :cl-user)

(format t "~%========================================~%")
(format t "Initializing CL-MPM Simulation Engine...~%")
(format t "========================================~%")

;; 1. Quickload required subsystems
(ql:quickload :cl-mpm :silent t)
(ql:quickload :cl-mpm/setup :silent t)
(ql:quickload :cl-mpm/damage :silent t)
(ql:quickload :cl-mpm/penalty :silent t)
(ql:quickload :cl-mpm/eigenerosion :silent t)
(ql:quickload :cl-mpm/plotter :silent t)

;; Ensure directories
(ensure-directories-exist #P"D:/MPM/output/")
(ensure-directories-exist #P"D:/MPM/outframes/")

;; Load stubs for serial simulation
(unless (find-package :cl-mpm/mpi)
  (let ((pkg (make-package :cl-mpm/mpi :use '(:cl))))
    (export (intern "MPI-SUM" pkg) pkg)
    (export (intern "MPM-SIM-MPI" pkg) pkg)))
(defclass cl-mpm/mpi:mpm-sim-mpi () ())
(defun cl-mpm/mpi:mpi-sum (x) x)

(unless (find-package :cl-mpm/buoyancy)
  (let ((pkg (make-package :cl-mpm/buoyancy :use '(:cl))))
    (export (intern "BC-SCALAR" pkg) pkg)
    (export (intern "BC-BUOYANCY-SIM" pkg) pkg)))
(defclass cl-mpm/buoyancy:bc-scalar (cl-mpm/bc::bc)
  ((sim :accessor cl-mpm/buoyancy::bc-buoyancy-sim :initarg :sim :initform nil)))

(unless (find-package :swank.live)
  (let ((pkg (make-package :swank.live :use '(:cl))))
    (export (intern "UPDATE-SWANK" pkg) pkg)))
(defun swank.live:update-swank () nil)

;; Load material models and chalk setup
(load "D:/MPM/src/models/chalk.lisp")
(defmethod initialize-instance :around ((mp cl-mpm/particle::particle-chalk-delayed) &rest initargs &key &allow-other-keys)
  (apply #'call-next-method mp initargs))
(load "D:/MPM/examples/chalk/chalk.lisp")

;; Default parameters if not injected by simulation_config.lisp
(defparameter *cfg-shelf-height* (if (boundp '*ui-shelf-height*) *ui-shelf-height* 100d0))
(defparameter *cfg-shelf-aspect* (if (boundp '*ui-shelf-aspect*) *ui-shelf-aspect* 2.0d0))
(defparameter *cfg-soil-boundary* (if (boundp '*ui-soil-boundary*) *ui-soil-boundary* 20d0))
(defparameter *cfg-mesh-size* (if (boundp '*ui-mesh-size*) *ui-mesh-size* 5d0))
(defparameter *cfg-mps-per-cell* (if (boundp '*ui-mps-per-cell*) *ui-mps-per-cell* 2))
(defparameter *cfg-undercut* (if (boundp '*ui-undercut*) *ui-undercut* 0d0))
(defparameter *cfg-density* (if (boundp '*ui-density*) *ui-density* 1.7d3))
(defparameter *cfg-E* (if (boundp '*ui-E*) *ui-E* 1d9))
(defparameter *cfg-nu* (if (boundp '*ui-nu*) *ui-nu* 0.35d0))
(defparameter *cfg-friction-angle* (if (boundp '*ui-friction-angle*) *ui-friction-angle* 40d0))
(defparameter *cfg-fracture-energy* (if (boundp '*ui-fracture-energy*) *ui-fracture-energy* 3000d0))
(defparameter *cfg-initiation-stress* (if (boundp '*ui-initiation-stress*) *ui-initiation-stress* 200d3))
(defparameter *cfg-delay-time* (if (boundp '*ui-delay-time*) *ui-delay-time* 1d1))
(defparameter *cfg-max-steps* (if (boundp '*ui-max-steps*) *ui-max-steps* 10))
(defparameter *cfg-substeps* (if (boundp '*ui-substeps*) *ui-substeps* 10))
(defparameter *cfg-plot-mode* (if (boundp '*ui-plot-mode*) *ui-plot-mode* :stress))
(defparameter *cfg-workers* (if (boundp '*ui-workers*) *ui-workers* 4))
(defparameter *cfg-enable-damage* (if (boundp '*ui-enable-damage*) *ui-enable-damage* t))

(cl-mpm/utils:set-workers *cfg-workers*)

(format t "Parameters configured:~%")
(format t "  Shelf Height: ~F m, Aspect: ~F, Undercut: ~F deg~%" *cfg-shelf-height* *cfg-shelf-aspect* *cfg-undercut*)
(format t "  Mesh Resolution: ~F m, MPs/Cell: ~D~%" *cfg-mesh-size* *cfg-mps-per-cell*)
(format t "  Young's Modulus: ~E Pa, Poisson: ~F, Friction: ~F deg~%" *cfg-E* *cfg-nu* *cfg-friction-angle*)
(format t "  Max Steps: ~D, Substeps/Frame: ~D, Mode: ~A~%" *cfg-max-steps* *cfg-substeps* *cfg-plot-mode*)

;; Setup simulation using chalk example infrastructure
(in-package :cl-mpm/examples/chalk)

(defun run-studio-setup ()
  (let* ((mesh-size cl-user::*cfg-mesh-size*)
         (mps-per-cell cl-user::*cfg-mps-per-cell*)
         (shelf-height cl-user::*cfg-shelf-height*)
         (soil-boundary cl-user::*cfg-soil-boundary*)
         (shelf-aspect cl-user::*cfg-shelf-aspect*)
         (runout-aspect 2.00)
         (shelf-length (* shelf-height shelf-aspect))
         (domain-length (+ shelf-length (* runout-aspect shelf-height)))
         (total-shelf-height (+ shelf-height soil-boundary))
         (offset (list 0 0)))
    (setf *sim*
          (setup-test-column (list domain-length (+ total-shelf-height (* 5 mesh-size)))
                             (list domain-length total-shelf-height)
                             offset
                             (/ 1d0 mesh-size) mps-per-cell))
    (loop for mp across (cl-mpm:sim-mps *sim*)
          do (setf (cl-mpm/particle::mp-E mp) cl-user::*cfg-E*
                   (cl-mpm/particle::mp-nu mp) cl-user::*cfg-nu*
                   (cl-mpm/particle::mp-initiation-stress mp) cl-user::*cfg-initiation-stress*
                   (cl-mpm/particle::mp-delay-time mp) cl-user::*cfg-delay-time*
                   (cl-mpm/particle::mp-split-depth mp) 0))
    ;; Apply undercut if angle > 0
    (let* ((undercut-angle cl-user::*cfg-undercut*)
           (normal (magicl:from-list (list (cos (- (* pi (/ undercut-angle 180d0))))
                                           (sin (- (* pi (/ undercut-angle 180d0))))) '(2 1))))
      (when (> (abs undercut-angle) 0.01)
        (cl-mpm/setup:remove-sdf *sim*
                                 (lambda (p)
                                   (if (> (magicl:tref p 1 0) soil-boundary)
                                       (cl-mpm/setup::plane-point-sdf
                                        (magicl:from-list (list (magicl:tref p 0 0)
                                                                (magicl:tref p 1 0)) '(2 1))
                                        normal
                                        (magicl:from-list (list shelf-length soil-boundary)
                                                          '(2 1) :type 'double-float))
                                       1d0)))))
    *sim*))

(run-studio-setup)

(setf (cl-mpm::sim-enable-damage *sim*) cl-user::*cfg-enable-damage*)

(cl-mpm/output:save-vtk-mesh #P"D:/MPM/output/mesh.vtk" *sim*)

(format t "Setup complete! Total Particles: ~D~%" (length (cl-mpm:sim-mps *sim*)))

;; Time loop
(format t "~%========================================~%")
(format t "Executing Simulation Steps...~%")
(format t "========================================~%")

(dotimes (step cl-user::*cfg-max-steps*)
  (format t "Step ~D/~D: computing physics...~%" (1+ step) cl-user::*cfg-max-steps*)
  (finish-output)
  (dotimes (sub cl-user::*cfg-substeps*)
    (cl-mpm:update-sim *sim*))
  (let ((vtk-path (format nil "D:/MPM/output/sim_~5,'0d.vtk" (1+ step)))
        (png-path (format nil "D:/MPM/outframes/frame_~5,'0d.png" (1+ step))))
    (cl-mpm/output:save-vtk (pathname vtk-path) *sim*)
    (ignore-errors
      (cond
        ((eq cl-user::*cfg-plot-mode* :stress)
         (cl-mpm/plotter:simple-plot
          *sim*
          :plot :deformed
          :colour-func (lambda (mp) (cl-mpm/fastmaths::voigt-von-mises (cl-mpm/particle:mp-stress mp)))))
        ((eq cl-user::*cfg-plot-mode* :velocity)
         (cl-mpm/plotter:simple-plot
          *sim*
          :plot :deformed
          :colour-func (lambda (mp) (cl-mpm/fastmaths::mag (cl-mpm/particle:mp-velocity mp)))))
        (t
         (plot *sim*)))
      (vgplot:title (format nil "Step ~D/~D (~A)" (1+ step) cl-user::*cfg-max-steps* cl-user::*cfg-plot-mode*))
      (vgplot:print-plot (pathname png-path) :terminal "png size 1280,720")
      (format t "  -> Saved Frame ~D: ~A~%" (1+ step) png-path)
      (finish-output))))

(format t "~%========================================~%")
(format t "SUCCESS: Simulation completed successfully!~%")
(format t "========================================~%")
(finish-output)

(ignore-errors (vgplot:close-all-plots))
(sleep 1)
(sb-ext:exit :code 0)
