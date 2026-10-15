;;;; Native Windows/full-engine PNG smoke and regression for asynchronous gnuplot.
;;;; windows\cl-mpm.cmd scripts\studio-plot-smoke.lisp
;;;; Optional "before-fix" mode records the original silent timeout behaviour.
(in-package :cl-user)
(ql:quickload :cl-mpm-studio :silent t)

(defun plot-smoke-nonempty-file-p (path)
  (ignore-errors
    (with-open-file (stream path :direction :input :element-type '(unsigned-byte 8))
      (plusp (file-length stream)))))

(handler-case
    (let* ((before-fix (member "before-fix" (cl-mpm-script-args) :test #'string=))
           (output (asdf:system-relative-pathname
                    "cl-mpm" "output/windows-verification-2026-10-14/plot-smoke/"))
           (blocker (merge-pathnames "blocked" output))
           (unwritable (merge-pathnames "blocked/child.png" output))
           (positive (merge-pathnames "positive.png" output))
           (config (cl-mpm-studio:load-config)))
      (ensure-directories-exist output)
      (when (probe-file positive) (delete-file positive))
      ;; A regular file cannot be the parent directory for child.png.
      (with-open-file (stream blocker :direction :output :if-exists :supersede)
        (write-line "plot smoke intentionally blocks a child pathname" stream))
      (setf (gethash "shelfHeight" config) 10d0
            (gethash "soilBoundary" config) 5d0
            (gethash "meshSize" config) 5d0
            (gethash "mpsPerCell" config) 1
            (gethash "workers" config) 1
            (gethash "enablePlasticity" config) nil
            (gethash "enableDamage" config) nil)
      (cl-mpm/utils:set-workers 1)
      (let ((sim (cl-mpm-studio::make-cliff-sim config)))
        (cl-mpm:update-sim sim)
        (format t "~&PNG NEGATIVE: ~A~%" (uiop:native-namestring unwritable))
        (finish-output)
        (let* ((started (get-internal-real-time))
               (failure (handler-case
                            (progn (cl-mpm-studio::save-frame sim :stress "Unwritable PNG" unwritable)
                                   nil)
                          (error (e) e)))
               (elapsed (/ (- (get-internal-real-time) started)
                           (float internal-time-units-per-second 1d0))))
          (assert (not (plot-smoke-nonempty-file-p unwritable)))
          (if before-fix
              (progn
                (assert (null failure) () "Original save-frame unexpectedly reported: ~A" failure)
                (format t "~&BASELINE REPRODUCED: save-frame returned after ~,2F s without PNG or error.~%"
                        elapsed))
              (progn
                (assert failure () "save-frame silently returned without writing PNG")
                (assert (search "PNG" (princ-to-string failure)) ()
                        "Unexpected failure: ~A" failure)
                (format t "~&NEGATIVE PASSED after ~,2F s: ~A~%" elapsed failure))))
        ;; Start a clean gnuplot process after its failed output command.
        (ignore-errors (vgplot:close-all-plots))
        (cl-mpm-studio::save-frame sim :stress "PNG smoke positive" positive)
        (assert (plot-smoke-nonempty-file-p positive))
        (unless before-fix
          (assert (cl-mpm-studio::png-file-complete-p positive)))
        (format t "~&POSITIVE PASSED: readable PNG at ~A~%" (uiop:native-namestring positive)))
      (ignore-errors (vgplot:close-all-plots))
      (format t "~&STUDIO PLOT SMOKE PASSED (full engine/gnuplot; not a scientific benchmark)~%")
      (finish-output)
      (uiop:quit 0))
  (error (e)
    (ignore-errors (vgplot:close-all-plots))
    (format *error-output* "~&STUDIO PLOT SMOKE FAILED: ~A~%" e)
    (finish-output *error-output*)
    (uiop:quit 1)))
