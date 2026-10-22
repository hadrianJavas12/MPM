;;;; Construction, signed-force mapping and rejection controls; not a Fig.3 reproduction.
;;;; windows\cl-mpm.cmd tests\benchmarks\wang2017-descent.lisp FRESH_NEGATIVE_OUTPUT
(in-package :cl-user)
(ql:quickload :cl-mpm-framework :silent t)
(load (cl-mpm-path "cases/benchmarks/wang2017-soil1.lisp"))
(in-package :cl-mpm/scenario/slope-descent)
(defvar *checks* 0)
(defun check-close (a b)
  (assert (<= (abs (- a b)) (* 1d-9 (max 1d0 (abs b))))))
(defun rejected-p (thunk)
  (handler-case (progn (funcall thunk) nil) (error () t)))
(defmacro check (name &body body)
  `(progn ,@body (incf *checks*) (format t "~&PASS: ~A~%" ,name)))

(cl-mpm/utils:set-workers 1)
(let* ((case cl-mpm/framework:*simulation*)
       (material (cl-mpm/framework:simulation-material case))
       (parameters (cl-mpm/framework:simulation-parameters case))
       (before (alexandria:copy-hash-table parameters))
       (config (compile-configuration case)))
  (check "Paper Soil1 SI inputs, real velocity and physical duration"
    (check-close (gethash "E" config) 20d6)
    (check-close (* (gethash "density" config) (- (gethash "gravity" config))) 20000d0)
    (check-close (gethash "velocity" config) 1d-4)
    (check-close (gethash "duration" config) 1000d0)
    (check-close (gethash "patchStart" config) 7d0)
    (check-close (gethash "patchLength" config) 3d0)
    (assert (= (hash-table-count before) (hash-table-count parameters)))
    (maphash (lambda (key value) (assert (eql value (gethash key parameters)))) before))
  (check "Actual native perfect MC; unchanged strength at arbitrary history"
    (assert (eq (cl-mpm/framework:material-particle-class material)
                'cl-mpm/models/mc-evolution:particle-mc-evolution))
    (let ((law (getf (cl-mpm/framework:material-particle-initargs material) :evolution-law)))
      (dolist (k '(0d0 .001d0 10d0))
        (multiple-value-bind (c phi psi) (cl-mpm/models/mc-evolution::law-values law k)
          (check-close c 30000d0) (check-close phi (* pi (/ 35d0 180d0))) (check-close psi 0d0)))))
  (check "Unknown parameter rejects before source or run output"
    (unwind-protect
         (progn (setf (gethash "unconsumedParameter" parameters) 1)
                (assert (rejected-p (lambda () (compile-configuration case)))))
      (remhash "unconsumedParameter" parameters)))
  (check "Invalid crest patch rejects rather than silently clipping input"
    (let ((loading (cl-mpm/framework:simulation-loading case)))
      (unwind-protect
           (progn (setf (getf (slot-value loading 'cl-mpm/framework::options) :patch-length) 30d0)
                  (assert (rejected-p (lambda () (compile-configuration case)))))
        (setf (getf (slot-value loading 'cl-mpm/framework::options) :patch-length) 3d0))))
  (multiple-value-bind (sim top-row) (make-slope material config)
    (check "Native plane-strain geometry, unit mass scale and a nonempty crest"
      (assert (= (cl-mpm/mesh:mesh-nd (cl-mpm:sim-mesh sim)) 2))
      (assert (= (cl-mpm::sim-mass-scale sim) 1d0))
      (assert (> (length top-row) 6))
      (assert (every (lambda (mp) (typep mp 'cl-mpm/models/mc-evolution:particle-mc-evolution))
                     (cl-mpm:sim-mps sim))))
    (let ((intervals (make-hash-table :test 'eq)))
      (loop for mp across top-row do
        (let ((x (component (cl-mpm/particle:mp-position mp) 0))
              (half (* .5d0 (component (cl-mpm/particle::mp-domain-size mp) 0))))
          (setf (gethash mp intervals) (cons (- x half) (+ x half)))))
      ;; Perturb reference elevations without changing constitutive state: all
      ;; selected material points must remain represented by their own datum.
      (incf (magicl:tref (cl-mpm/particle:mp-position (aref top-row 14)) 1 0) 1d-5)
      (let ((strip (make-strip top-row config intervals)))
        (check "Full three-metre strip retained despite unequal reference elevations"
          (assert (= (length (strip-contacts strip)) 6))
          (check-close (reduce #'+ (strip-contacts strip) :key #'contact-width) 3d0)
          (multiple-value-bind (actual gap rms) (strip-measurements strip)
            (check-close actual 0d0) (check-close gap 0d0) (check-close rms 0d0)))
        (cl-mpm::reset-grid (cl-mpm:sim-mesh sim))
        (cl-mpm::p2g (cl-mpm:sim-mesh sim) (cl-mpm:sim-mps sim) :FLIP)
        (cl-mpm::update-node-kinematics sim)
        (check "Signed spring reaction agrees with analytic stiffness and mapped grid force"
          (dolist (descent '(1d-4 -1d-4))
            (setf (strip-target strip) descent)
            (cl-mpm/bc::apply-sim-bc sim strip 0d0)
            (let ((expected (* (strip-epsilon strip) 3d0 descent)))
              (check-close (strip-reaction strip) expected)
              (check-close (strip-mapped-reaction strip) expected)))))))
  (check "Gravity budget failure persists an incomplete manifest instead of success"
    (let* ((output (or (first (cl-user::cl-mpm-script-args))
                       (error "Supply a fresh negative-control output directory.")))
           (directory (uiop:ensure-directory-pathname output))
           (short (alexandria:copy-hash-table config)))
      (when (probe-file directory) (error "Negative-control directory must not exist."))
      (setf (gethash "settleMaxUpdates" short) 1
            (gethash "settleMinUpdates" short) 1
            (gethash "settleHoldChecks" short) 2)
      (assert (rejected-p (lambda () (run material short directory))))
      (let ((record (cl-mpm/framework::read-parameter-json
                     (merge-pathnames "manifest.json" directory))))
        (assert (null (gethash "complete" record)))
        (assert (equal (gethash "status" record) "failed"))
        (assert (search "Gravity failed sustained equilibrium" (gethash "error" record)))
        (assert (= (gethash "settleUpdates" record) 1))
        (assert (= (gethash "loadingUpdates" record) 0))))))
(format t "~&WANG2017 DESCENT CONTROLS: ~D passed; no physical loading run executed.~%" *checks*)
(uiop:quit 0)
