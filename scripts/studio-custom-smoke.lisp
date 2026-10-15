;;;; Real-engine smoke test, requiring the complete CL-MPM/Quicklisp toolchain.
;;;; windows\cl-mpm.cmd scripts\studio-custom-smoke.lisp
;;;; Unlike studio/test/lisp-contract-harness.lisp, this uses the real MPM engine.
(in-package :cl-user)
(ql:quickload :cl-mpm-studio :silent t)
(in-package :cl-mpm-studio)

(defvar *smoke-custom-calls* 0)
(defmethod cl-mpm/particle:constitutive-model ((mp studio-custom-chalk) strain dt)
  (incf *smoke-custom-calls*)
  (call-next-method))

(defun smoke-finite (value)
  (and (typep value 'double-float)
       (not (sb-ext:float-nan-p value))
       (not (sb-ext:float-infinity-p value))))

(defun smoke-compare-vector (a b)
  (let ((left (cl-mpm/utils::fast-storage a)) (right (cl-mpm/utils::fast-storage b)))
    (assert (= (length left) (length right)))
    (loop for x across left for y across right
          for difference = (abs (- x y)) do
      (assert (and (smoke-finite x) (smoke-finite y)))
      (assert (<= difference (* 1d-10 (max 1d0 (abs x) (abs y)))) ()
              "Built-in/delegate mismatch: ~A vs ~A" x y)
          maximize difference)))

(defun smoke-vtk-line (stream)
  (loop with bytes = nil
        for byte = (read-byte stream nil nil) do
          (when (null byte)
            (assert (null bytes) () "Truncated VTK header")
            (return nil))
          (when (= byte 10)
            (return (coerce (nreverse bytes) 'string)))
          (assert (< byte 128) () "Binary payload found where a VTK header was expected")
          (push (code-char byte) bytes)))

(defun smoke-vtk-double (stream)
  (let ((bits 0))
    (dotimes (i 8)
      (setf bits (logior (ash bits 8) (read-byte stream))))
    (let ((value (ieee-floats:decode-float64 bits)))
      (assert (smoke-finite value) () "Nonfinite VTK value")
      value)))

(defun smoke-check-vtk (path sim)
  "Read exact big-endian blocks, catching corrupt text/binary interleaving."
  (let ((mps (cl-mpm:sim-mps sim)) (scalars 0))
    (with-open-file (stream path :element-type '(unsigned-byte 8))
      (assert (string= (smoke-vtk-line stream) "# vtk DataFile Version 2.0"))
      (smoke-vtk-line stream) ; title
      (assert (string= (smoke-vtk-line stream) "BINARY"))
      (assert (string= (smoke-vtk-line stream) "DATASET UNSTRUCTURED_GRID"))
      (assert (string= (smoke-vtk-line stream) (format nil "POINTS ~D double" (length mps))))
      (loop for mp across mps do
        (dotimes (i 3)
          (assert (= (smoke-vtk-double stream)
                     (cl-mpm/utils:varef (cl-mpm/particle::mp-position-trial mp) i))
                  () "VTK point differs from the simulation")))
      (assert (string= (smoke-vtk-line stream) ""))
      (assert (string= (smoke-vtk-line stream) (format nil "POINT_DATA ~D" (length mps))))
      (loop for header = (smoke-vtk-line stream) while header do
        (let ((tokens (uiop:split-string header :separator '(#\Space))))
          (assert (and (= (length tokens) 4)
                       (string= (first tokens) "SCALARS")
                       (string= (third tokens) "double")
                       (string= (fourth tokens) "1")) () "Invalid VTK scalar declaration: ~A" header)
          (assert (string= (smoke-vtk-line stream) "LOOKUP_TABLE default"))
          (loop for mp across mps for value = (smoke-vtk-double stream) do
            (when (string= (second tokens) "mass")
              (assert (= value (cl-mpm/particle:mp-mass mp)) () "VTK mass differs from the simulation")))
          (assert (string= (smoke-vtk-line stream) ""))
          (incf scalars))))
    (assert (plusp scalars) () "Missing VTK scalar data")
    (format t "~&VTK verified: ~A (~D points; ~D finite scalar arrays)~%" path (length mps) scalars)))

(handler-case
    (let ((config (load-config)))
      (setf (gethash "shelfHeight" config) 10d0
            (gethash "soilBoundary" config) 5d0
            (gethash "meshSize" config) 5d0
            (gethash "mpsPerCell" config) 1
            (gethash "workers" config) 1
            (gethash "enablePlasticity" config) nil
            (gethash "enableDamage" config) nil)
      (cl-mpm/utils:set-workers 1)
      (let ((built-in (make-cliff-sim config)))
        (setf (gethash "constitutiveModel" config) :custom)
        (let ((custom (make-cliff-sim config)))
          (assert (plusp (length (cl-mpm:sim-mps custom))))
          (assert (= (length (cl-mpm:sim-mps built-in)) (length (cl-mpm:sim-mps custom))))
          (assert (= (cl-mpm:sim-dt built-in) (cl-mpm:sim-dt custom)))
          (dotimes (step 2)
            (cl-mpm:update-sim built-in)
            (cl-mpm:update-sim custom))
          (assert (= (length (cl-mpm:sim-mps built-in)) (length (cl-mpm:sim-mps custom))))
          (assert (plusp *smoke-custom-calls*) () "Custom CLOS dispatch never ran")
          (let ((position-difference 0d0) (stress-difference 0d0))
            (loop for a across (cl-mpm:sim-mps built-in)
                  for b across (cl-mpm:sim-mps custom) do
                    (setf position-difference
                          (max position-difference
                               (smoke-compare-vector (cl-mpm/particle:mp-position a)
                                                     (cl-mpm/particle:mp-position b))))
                    (setf stress-difference
                          (max stress-difference
                               (smoke-compare-vector (cl-mpm/particle:mp-stress a)
                                                     (cl-mpm/particle:mp-stress b)))))
            (format t "~&Particles: ~D, steps: 2, dt: ~,8E s, custom calls: ~D~%"
                    (length (cl-mpm:sim-mps custom)) (cl-mpm:sim-dt custom) *smoke-custom-calls*)
            (format t "~&Max absolute position difference: ~,8E m; stress difference: ~,8E Pa~%"
                    position-difference stress-difference))
          (let ((output (asdf:system-relative-pathname "cl-mpm" "output/studio-custom-smoke/")))
            (ensure-directories-exist output)
            (let ((built-in-path (merge-pathnames "built-in.vtk" output))
                  (custom-path (merge-pathnames "custom-delegate.vtk" output)))
              (cl-mpm/output:save-vtk built-in-path built-in)
              (cl-mpm/output:save-vtk custom-path custom)
              (smoke-check-vtk built-in-path built-in)
              (smoke-check-vtk custom-path custom)))))
      (format t "~&STUDIO CUSTOM SMOKE PASSED (real engine, two steps; not a scientific benchmark)~%")
      (uiop:quit 0))
  (error (e)
    (format *error-output* "~&STUDIO CUSTOM SMOKE FAILED: ~A~%" e)
    (uiop:quit 1)))
