;;; Runner for Chalk Example Simulation
(in-package :cl-user)

(format t "========================================~%")
(format t "Loading cl-mpm and Chalk example...~%")
(format t "========================================~%")

(ql:quickload :cl-mpm :silent t)
(ql:quickload :cl-mpm/setup :silent t)
(ql:quickload :cl-mpm/damage :silent t)
(ql:quickload :cl-mpm/penalty :silent t)
(ql:quickload :cl-mpm/eigenerosion :silent t)
(ql:quickload :cl-mpm/plotter :silent t)

;; Configure workers
(cl-mpm/utils:set-workers 4)

;; Ensure output directories exist
(ensure-directories-exist #P"D:/MPM/output/")
(ensure-directories-exist #P"D:/MPM/outframes/")

;; Define dummy CL-MPM/MPI package for serial simulation
(unless (find-package :cl-mpm/mpi)
  (let ((pkg (make-package :cl-mpm/mpi :use '(:cl))))
    (export (intern "MPI-SUM" pkg) pkg)
    (export (intern "MPM-SIM-MPI" pkg) pkg)))
(defclass cl-mpm/mpi:mpm-sim-mpi () ())
(defun cl-mpm/mpi:mpi-sum (x) x)

;; Define cl-mpm/buoyancy stub for serial simulation
(unless (find-package :cl-mpm/buoyancy)
  (let ((pkg (make-package :cl-mpm/buoyancy :use '(:cl))))
    (export (intern "BC-SCALAR" pkg) pkg)
    (export (intern "BC-BUOYANCY-SIM" pkg) pkg)))
(defclass cl-mpm/buoyancy:bc-scalar (cl-mpm/bc::bc)
  ((sim :accessor cl-mpm/buoyancy::bc-buoyancy-sim :initarg :sim :initform nil)))

;; Define swank.live stub for headless batch execution
(unless (find-package :swank.live)
  (let ((pkg (make-package :swank.live :use '(:cl))))
    (export (intern "UPDATE-SWANK" pkg) pkg)))
(defun swank.live:update-swank () nil)

;; Load chalk constitutive models
(load "D:/MPM/src/models/chalk.lisp")

;; Allow legacy/experimental initargs
(defmethod initialize-instance :around ((mp cl-mpm/particle::particle-chalk-delayed) &rest initargs &key &allow-other-keys)
  (apply #'call-next-method mp initargs))

;; Load chalk example
(load "D:/MPM/examples/chalk/chalk.lisp")

(format t "Initializing Chalk Simulation (setup)...~%")
(in-package :cl-mpm/examples/chalk)
(setup)

(format t "Domain setup complete! Particles count: ~D~%" (length (cl-mpm:sim-mps *sim*)))
(format t "Saving initial mesh VTK to D:/MPM/output/mesh.vtk...~%")
(cl-mpm/output:save-vtk-mesh #P"D:/MPM/output/mesh.vtk" *sim*)

;; ========================================================
;; KONFIGURASI SIMULASI & PEWARNAAN
;; ========================================================
;; Mode Pewarnaan:
;;   :stress -> Menampilkan tegangan Von Mises (area tegangan tinggi berwarna MERAH)
;;   :damage -> Menampilkan retakan/kerusakan material
(defparameter *plot-mode* :stress)

;; Mengaktifkan kalkulasi kerusakan dan plastisitas
(setf (cl-mpm::sim-enable-damage *sim*) t)

(defparameter *max-steps*
  (or (let* ((args (cdr (member "--" sb-ext:*posix-argv* :test #'string=)))
             (first-arg (and args (first args))))
        (when (and first-arg (> (length first-arg) 0))
          (parse-integer first-arg :junk-allowed t)))
      (when (uiop:getenv "MAX_STEPS")
        (parse-integer (uiop:getenv "MAX_STEPS") :junk-allowed t))
      10)) ; <-- Nilai default jumlah step

(defparameter *substeps-per-frame*
  (or (when (uiop:getenv "SUBSTEPS")
        (parse-integer (uiop:getenv "SUBSTEPS") :junk-allowed t))
      10)) ; <-- Nilai default kalkulasi fisika per step

(format t "~%========================================~%")
(format t "Running ~D steps of Chalk simulation (Plot Mode: ~A)...~%"
        *max-steps* *plot-mode*)
(format t "========================================~%")

(dotimes (step *max-steps*)
  (format t "Step ~D/~D: computing physics...~%" (1+ step) *max-steps*)
  (dotimes (sub *substeps-per-frame*)
    (cl-mpm:update-sim *sim*))
  (let ((vtk-path (format nil "D:/MPM/output/sim_~5,'0d.vtk" (1+ step)))
        (png-path (format nil "D:/MPM/outframes/frame_~5,'0d.png" (1+ step))))
    (format t "  -> Saving VTK: ~A~%" vtk-path)
    (cl-mpm/output:save-vtk (pathname vtk-path) *sim*)
    (ignore-errors
      (if (eq *plot-mode* :stress)
          (cl-mpm/plotter:simple-plot
           *sim*
           :plot :deformed
           :colour-func (lambda (mp) (cl-mpm/fastmaths::voigt-von-mises (cl-mpm/particle:mp-stress mp))))
          (plot *sim*))
      (vgplot:title (format nil "Chalk Sim Step ~D (~A)" (1+ step) *plot-mode*))
      (vgplot:print-plot (pathname png-path) :terminal "png size 1280,720")
      (format t "  -> Saving PNG: ~A~%" png-path))))

(format t "~%========================================~%")
(format t "SUCCESS: Chalk simulation example finished (~D steps)!~%" *max-steps*)
(format t "Output VTK files: D:\\MPM\\output\\~%")
(format t "Output PNG plots: D:\\MPM\\outframes\\~%")
(format t "========================================~%")

(ignore-errors (vgplot:close-all-plots))
(sleep 1)

(sb-ext:exit :code 0)
