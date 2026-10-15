;;;; Ordinary cliff frame stepping; dedicated Joss dispatch.
;;;; Extracted without changing the existing numerical expressions.
(in-package :cl-mpm/framework/cliff)

(defun run (config output-dir &key (cliff-builder #'make-cliff-sim))
  "Run the cliff scenario described by CONFIG, writing into OUTPUT-DIR:
  vtk/mesh.vtk, vtk/sim_NNNNN.vtk  (ParaView)
  frames/frame_NNNNN.png           (gnuplot, skipped if gnuplot fails)
Prints one \"Step k/N\" line per frame for command-line progress.
CLIFF-BUILDER receives CONFIG and returns a native simulation."
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
    (let ((sim (funcall cliff-builder config)))
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
