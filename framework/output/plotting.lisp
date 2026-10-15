;;;; Shared native VTK sequence names and gnuplot rendering.
;;;; Extracted without changing the existing numerical expressions.
(in-package :cl-mpm/framework/cliff)

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
