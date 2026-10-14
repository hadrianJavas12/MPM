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
    (loop for x across left for y across right do
      (assert (and (smoke-finite x) (smoke-finite y)))
      (assert (<= (abs (- x y)) (* 1d-10 (max 1d0 (abs x) (abs y)))) ()
              "Built-in/delegate mismatch: ~A vs ~A" x y))))

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
          (dotimes (step 2)
            (cl-mpm:update-sim built-in)
            (cl-mpm:update-sim custom))
          (assert (plusp *smoke-custom-calls*) () "Custom CLOS dispatch never ran")
          (loop for a across (cl-mpm:sim-mps built-in)
                for b across (cl-mpm:sim-mps custom) do
                  (smoke-compare-vector (cl-mpm/particle:mp-position a) (cl-mpm/particle:mp-position b))
                  (smoke-compare-vector (cl-mpm/particle:mp-stress a) (cl-mpm/particle:mp-stress b)))
          (let ((output (asdf:system-relative-pathname "cl-mpm" "output/studio-custom-smoke/")))
            (ensure-directories-exist output)
            (cl-mpm/output:save-vtk (merge-pathnames "built-in.vtk" output) built-in)
            (cl-mpm/output:save-vtk (merge-pathnames "custom-delegate.vtk" output) custom))))
      (format t "~&STUDIO CUSTOM SMOKE PASSED (real engine, two steps; not a scientific benchmark)~%")
      (uiop:quit 0))
  (error (e)
    (format *error-output* "~&STUDIO CUSTOM SMOKE FAILED: ~A~%" e)
    (uiop:quit 1)))
