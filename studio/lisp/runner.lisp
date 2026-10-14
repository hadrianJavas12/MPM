;;;; runner.lisp — time loop, VTK/PNG output and command-line entry point.

(in-package :cl-mpm-studio)

(defun colour-function (mode)
  "Per-particle scalar used to colour PNG frames."
  (ecase mode
    (:stress (lambda (mp) (cl-mpm/fastmaths::voigt-von-mises (cl-mpm/particle:mp-stress mp))))
    (:damage (lambda (mp) (cl-mpm/particle::mp-damage mp)))
    (:velocity (lambda (mp) (cl-mpm/fastmaths::mag (cl-mpm/particle:mp-velocity mp))))))

(defun save-frame (sim mode title path)
  "Render SIM with gnuplot (through vgplot) into the PNG file PATH."
  (cl-mpm/plotter:simple-plot sim :plot :deformed :colour-func (colour-function mode))
  (vgplot:title title)
  (vgplot:print-plot path :terminal "png size 1280,720")
  ;; gnuplot is a separate process: wait until it has written the file.
  (loop repeat 100
        until (probe-file path)
        do (sleep 0.05))
  (sleep 0.1))

(defun numbered (dir prefix n type)
  (merge-pathnames (format nil "~A_~5,'0D.~A" prefix n type) dir))

(defun run (config output-dir)
  "Run the cliff scenario described by CONFIG, writing into OUTPUT-DIR:
  vtk/mesh.vtk, vtk/sim_NNNNN.vtk  (ParaView)
  frames/frame_NNNNN.png           (gnuplot, skipped if gnuplot fails)
Prints one \"Step k/N\" line per frame; studio/server.js parses these."
  (let* ((output-dir (uiop:ensure-directory-pathname output-dir))
         (vtk-dir (merge-pathnames "vtk/" output-dir))
         (frames-dir (merge-pathnames "frames/" output-dir))
         (frames (param config "maxSteps"))
         (substeps (param config "substeps"))
         (mode (param config "plotMode"))
         (plotting t))
    (ensure-directories-exist vtk-dir)
    (ensure-directories-exist frames-dir)
    (describe-config config)
    (cl-mpm/utils:set-workers (param config "workers"))
    (let ((sim (make-cliff-sim config)))
      (format t "~&Particles: ~D, dt: ~,3E s, output: ~A~%"
              (length (cl-mpm:sim-mps sim)) (cl-mpm:sim-dt sim) (uiop:native-namestring output-dir))
      (finish-output)
      (cl-mpm/output:save-vtk-mesh (merge-pathnames "mesh.vtk" vtk-dir) sim)
      (dotimes (i frames)
        (let ((step (1+ i)))
          (dotimes (s substeps)
            (cl-mpm:update-sim sim))
          (cl-mpm/output:save-vtk (numbered vtk-dir "sim" step "vtk") sim)
          (when plotting
            (handler-case
                (save-frame sim mode
                            (format nil "Frame ~D/~D (~(~A~))" step frames mode)
                            (numbered frames-dir "frame" step "png"))
              (error (e)
                (format t "~&Plotting disabled (is gnuplot installed?): ~A~%" e)
                (setf plotting nil))))
          (format t "~&Step ~D/~D~%" step frames)
          (finish-output)))
      (ignore-errors (vgplot:close-all-plots))
      ;; gnuplot writes the last PNG asynchronously.
      (sleep 1)
      sim)))

(defun load-custom-model (path)
  "Load an explicitly approved user Lisp file from disk.
This is NOT a sandbox. Studio's HTTP server must opt in and run locally."
  (unless (and path (probe-file path))
    (error "Missing custom-model.lisp source file."))
  (format t "~&Loading USER-SUPPLIED Lisp: ~A~%" (namestring path))
  (finish-output)
  (load path)
  (let ((method (find-method
                 #'cl-mpm/particle:constitutive-model
                 '()
                 (list (find-class 'studio-custom-chalk)
                       (find-class 't)
                       (find-class 't))
                 nil)))
    (unless method
      (error "Custom file must define constitutive-model (studio-custom-chalk strain dt).")))
  (format t "~&Custom constitutive model installed.~%")
  (finish-output))

(defun default-output-dir ()
  (asdf:system-relative-pathname "cl-mpm" "output/cliff/"))

(defun main (args)
  "Entry point. ARGS = ([config.json] [output-dir] [custom-model.lisp]).
Without a config every parameter takes its schema default; the output
directory defaults to the config file's directory, else output/cliff/.
Returns a process exit code."
  (destructuring-bind (&optional config-path output-dir custom-path) args
    (handler-case
        (let* ((config-path (and config-path (uiop:parse-native-namestring config-path)))
               (config (load-config config-path))
               (output-dir (cond (output-dir (uiop:ensure-directory-pathname
                                              (uiop:parse-native-namestring output-dir)))
                                 (config-path (uiop:pathname-directory-pathname config-path))
                                 (t (default-output-dir)))))
          (when (eq (param config "constitutiveModel") :custom)
            (load-custom-model
             (and custom-path (uiop:parse-native-namestring custom-path))))
          (run config output-dir)
          (format t "~&SUCCESS~%")
          0)
      (error (e)
        (format *error-output* "~&ERROR: ~A~%" e)
        1))))
