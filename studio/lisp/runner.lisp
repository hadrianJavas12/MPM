;;;; runner.lisp — time loop, VTK/PNG output and command-line entry point.

(in-package :cl-mpm-studio)

(defun colour-function (mode)
  "Per-particle scalar used to colour PNG frames."
  (ecase mode
    (:stress (lambda (mp) (cl-mpm/fastmaths::voigt-von-mises (cl-mpm/particle:mp-stress mp))))
    (:damage (lambda (mp) (cl-mpm/particle::mp-damage mp)))
    (:velocity (lambda (mp) (cl-mpm/fastmaths::mag (cl-mpm/particle:mp-velocity mp))))))

(defun png-file-complete-p (path)
  "Check that gnuplot has finished writing a readable, nonempty PNG at PATH.
A file may exist while the separate gnuplot process is still writing it."
  (ignore-errors
    (with-open-file (stream path :direction :input :element-type '(unsigned-byte 8))
      (let ((length (file-length stream))
            (signature #(137 80 78 71 13 10 26 10))
            (end-chunk #(0 0 0 0 73 69 78 68 174 66 96 130)))
        (and (>= length (+ (length signature) (length end-chunk)))
             (loop for expected across signature
                   always (eql expected (read-byte stream nil nil)))
             (file-position stream (- length (length end-chunk)))
             (loop for expected across end-chunk
                   always (eql expected (read-byte stream nil nil))))))))

(defun save-frame (sim mode title path &key (timeout-seconds 5d0))
  "Render SIM with gnuplot (through vgplot) into the PNG file PATH."
  (cl-mpm/plotter:simple-plot sim :plot :deformed :colour-func (colour-function mode))
  (vgplot:title title)
  ;; An exported script may reuse its output directory; do not accept an old PNG.
  (let ((existing (ignore-errors (probe-file path))))
    (when existing (delete-file existing)))
  (vgplot:print-plot path :terminal "png size 1280,720")
  ;; Wait for the PNG end chunk, not merely file creation: gnuplot is asynchronous.
  (loop repeat (ceiling timeout-seconds 0.05d0)
        when (png-file-complete-p path) do (return-from save-frame path)
        do (sleep 0.05))
  (when (png-file-complete-p path) (return-from save-frame path))
  (error "gnuplot did not write a complete readable PNG to ~A within ~A seconds."
         (uiop:native-namestring path) timeout-seconds))

(defun numbered (dir prefix n type)
  (merge-pathnames (format nil "~A_~5,'0D.~A" prefix n type) dir))

(defun run (config output-dir)
  "Run the cliff scenario described by CONFIG, writing into OUTPUT-DIR:
  vtk/mesh.vtk, vtk/sim_NNNNN.vtk  (ParaView)
  frames/frame_NNNNN.png           (gnuplot, skipped if gnuplot fails)
Prints one \"Step k/N\" line per frame; studio/server.js parses these."
  (when (eq (param config "scenario") :joss-bay)
    (when (eq (param config "constitutiveModel") :custom)
      (error "Joss Bay requires its dedicated reference material, not a custom chalk method."))
    (return-from run (run-joss-reference config output-dir)))
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
