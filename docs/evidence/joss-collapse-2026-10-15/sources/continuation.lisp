;;;; Trusted isolated physical pilot, using the already converged native state.
;;;; No global source file or ordinary Studio material is changed.
(in-package :cl-mpm-studio)

(defclass joss-probe-dp-chalk (joss-reference-chalk) ())
(defmethod cl-mpm/damage::damage-model-calculate-y ((mp joss-probe-dp-chalk) dt)
  (declare (ignore dt))
  (let ((y (max 0d0 (cl-mpm/damage::drucker-prager-criterion
                     (cl-mpm/particle::mp-undamaged-stress mp)
                     (cl-mpm/particle::mp-friction-angle mp)))))
    (setf (cl-mpm/particle::mp-damage-y-local mp) y
          (cl-mpm/particle::mp-local-damage-increment mp) y)))

;; The existing phase runner sets this flag for all MPs. Keep the recovered
;; author's elastic beach/base protected throughout this isolated pilot.
(defmethod (setf cl-mpm/particle::mp-enable-damage) :around
    (enabled (mp joss-probe-dp-chalk))
  (call-next-method (and enabled (/= (cl-mpm/particle::mp-index mp) 1)) mp))
(defmethod (setf cl-mpm/particle::mp-enable-plasticity) :around
    (enabled (mp joss-probe-dp-chalk))
  (call-next-method (and enabled (/= (cl-mpm/particle::mp-index mp) 1)) mp))

(defparameter *dp-pilot-output*
  (uiop:ensure-directory-pathname
   (cl-user::cl-mpm-path "output/reference-reproduction-2026-10-15/dp-physical-pilot/")))
(defparameter *dp-pilot-segment-start* (get-internal-real-time))
(defparameter *dp-pilot-segment-limit* 180d0)
(defparameter *dp-pilot-pause* 0)
(defparameter *dp-pilot-running* nil)

(defmethod cl-mpm:update-sim :before ((sim joss-reference-aggregate-sim))
  (when (and *dp-pilot-running*
             (> (/ (- (get-internal-real-time) *dp-pilot-segment-start*)
                   (float internal-time-units-per-second 1d0))
                *dp-pilot-segment-limit*))
    (incf *dp-pilot-pause*)
    (reference-check-finite sim)
    (let* ((n *dp-pilot-pause*)
           (control (merge-pathnames (format nil "resume-~D.txt" n) *dp-pilot-output*))
           (status (make-hash-table :test #'equal))
           (wait-start (get-internal-real-time)))
      (setf (gethash "status" status) "awaiting-directed-continuation"
            (gethash "physicalTime" status) (cl-mpm::sim-time sim)
            (gethash "massScale" status) (cl-mpm::sim-mass-scale sim)
            (gethash "mass" status) (reference-summary sim)
            (gethash "maximumDamage" status)
            (loop for mp across (cl-mpm:sim-mps sim) maximize (cl-mpm/particle:mp-damage mp))
            (gethash "pause" status) n (gethash "control" status) (namestring control))
      (cl-mpm/output:save-vtk
       (merge-pathnames (format nil "pause-~D.vtk" n) *dp-pilot-output*) sim)
      (criterion-probe-json (merge-pathnames "pause.json" *dp-pilot-output*) status)
      (format t "~&DP PHYSICAL PILOT PAUSED: ~A~%" (jonathan:to-json status))
      (finish-output)
      ;; Preserve the physical call stack/state instead of repeating equilibrium.
      ;; A trusted text command is either 'stop' or 'continue <wall-seconds>'.
      (loop
        (when (> (/ (- (get-internal-real-time) wait-start) internal-time-units-per-second) 14400)
          (error "Physical pilot control wait expired after four hours"))
        (when (probe-file control)
          (let ((line (with-open-file (stream control) (read-line stream nil ""))))
            (cond ((string= (string-trim '(#\Space #\Tab #\Return #\Newline) line) "stop")
                   (error "Physical pilot stopped by trusted control"))
                  ((and (> (length line) 9) (string= (subseq line 0 9) "continue "))
                   (let ((seconds (parse-integer line :start 9 :junk-allowed t)))
                     (when (and seconds (<= 60 seconds 14400))
                       (setf *dp-pilot-segment-limit* (float seconds 1d0)
                             *dp-pilot-segment-start* (get-internal-real-time))
                       (format t "~&DP physical state resumed for <=~D wall seconds.~%" seconds)
                       (finish-output) (return)))))))
        (sleep 1d0)))))

(let* ((sim *criterion-probe-sim*) (config *criterion-probe-config*)
       (original-constructor (symbol-function 'make-joss-reference-sim))
       (original-getenv (symbol-function 'uiop:getenv))
       (used nil) (base-count 0) (description (make-hash-table :test #'equal)))
  (assert sim)
  (ensure-directories-exist *dp-pilot-output*)
  (loop for mp across (cl-mpm:sim-mps sim) do
    (change-class mp 'joss-probe-dp-chalk)
    (setf (cl-mpm/particle::mp-index mp)
          (if (<= (cl-mpm/utils:varef (cl-mpm/particle:mp-position mp) 1)
                  (param config "soilBoundary")) 1 0))
    (when (= (cl-mpm/particle::mp-index mp) 1) (incf base-count)))
  ;; This is an actual physical-time runner, not the legacy DR timeline runner.
  ;; Recheck equilibrium with one elastic update before its normal time reset.
  (setf (gethash "settleMaxSteps" config) 1
        (gethash "settleTolerance" config) 1.01d-4
        (gethash "simulationTime" config) 40d0
        (gethash "maxSteps" config) 1000
        (gethash "accelerateInterval" config) 2d0)
  (setf (gethash "damageCriterion" description) "Drucker-Prager, radian friction; isolated dedicated class"
        (gethash "protectedBaseParticles" description) base-count
        (gethash "baseProtection" description) "index1 elastic beach/base; damage/plasticity disabled"
        (gethash "preparedState" description) "criterion-probe strict aggregate equilibrium,1658 updates"
        (gethash "initiationStress" description) 18926.452181842527d0
        (gethash "delayTime" description) (param config "delayTime")
        (gethash "purpose" description) "First actual DP physical-trajectory discriminator, not completed reference validation"
        (gethash "wallBound" description) "Pause at180 wallseconds, retain state for trusted resume command; four-hour control expiry")
  (criterion-probe-json (merge-pathnames "pilot-provenance.json" *dp-pilot-output*) description)
  (criterion-probe-json (merge-pathnames "config.json" *dp-pilot-output*) config)
  (unwind-protect
       (progn
         (setf (symbol-function 'make-joss-reference-sim)
               (lambda (ignored &rest options)
                 (declare (ignore ignored options))
                 (when used (error "Settled constructor may be reused only once"))
                 (setf used t) sim)
               ;; Scoped environment lookup prevents slow native plotting; all
               ;; real VTKs are subsequently rendered by the scientific script.
               (symbol-function 'uiop:getenv)
               (lambda (key) (if (string= key "CL_MPM_REFERENCE_PNG") "0"
                                 (funcall original-getenv key)))
               *dp-pilot-running* t)
         (format t "~&DP PHYSICAL PILOT START: same converged native state; ~D protected base MPs; target40s~%" base-count)
         (finish-output)
         (handler-case (run-joss-reference config *dp-pilot-output*)
           (error (e)
             (let ((failure (make-hash-table :test #'equal)))
               (setf (gethash "error" failure) (princ-to-string e)
                     (gethash "physicalTime" failure) (cl-mpm::sim-time sim))
               (criterion-probe-json (merge-pathnames "pilot-error.json" *dp-pilot-output*) failure))
             (error e))))
    (setf *dp-pilot-running* nil
          (symbol-function 'make-joss-reference-sim) original-constructor
          (symbol-function 'uiop:getenv) original-getenv)))
