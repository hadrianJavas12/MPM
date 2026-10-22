;;;; Genuine material-point controls for the experimental total-stress clay law.
;;;; windows\cl-mpm.cmd tests\materials\clay-creep-points.lisp [output-directory]
;;;; Optional output defaults to output/clay-creep-points/. No solver run here.
(in-package :cl-user)
(require :asdf)
(ql:quickload :cl-mpm-framework :silent t)

(defpackage :cl-mpm/tests/clay-creep-points
  (:use :cl :cl-mpm/models/clay-creep))
(in-package :cl-mpm/tests/clay-creep-points)

(defparameter *checks* 0)
(defparameter *failures* nil)
(defparameter *e* 20d6)
(defparameter *nu* .25d0)
(defparameter *g* (/ *e* (* 2d0 (+ 1d0 *nu*))))

(defun close-to (actual expected tolerance &optional (label "value"))
  (unless (and (cl-mpm/models/clay-creep::finite-number-p actual)
               (<= (abs (- actual expected)) tolerance))
    (error "~A expected ~,16G; actual ~,16G; tolerance ~G."
           label expected actual tolerance)))
(defun check (predicate message) (unless predicate (error "~A" message)))
(defun rejects (thunk) (handler-case (progn (funcall thunk) nil) (error () t)))
(defmacro point-check (name &body body)
  `(handler-case
       (progn ,@body (incf *checks*) (format t "~&PASS: ~A~%" ,name))
     (error (condition)
       (push (list ,name (princ-to-string condition)) *failures*)
       (format t "~&FAIL: ~A: ~A~%" ,name condition))))
(defun law (&key (peak 50d3) (residual peak) (softening .02d0) (eta 5d6))
  (make-clay-creep-law :yield-peak peak :yield-residual residual
                       :softening-kappa softening :viscosity eta))
(defun shear-strain (q &optional (pressure 0d0))
  "Pure engineering xy shear plus prescribed hydrostatic Kirchhoff pressure."
  (let ((normal (* (- pressure) (/ (- 1d0 (* 2d0 *nu*)) *e*))))
    (vector normal normal normal 0d0 0d0 (/ q (* (sqrt 3d0) *g*)))))
(defun axial-strain (q)
  "Trace-free normal strain produces the same q as the shear test."
  (vector (/ q (* 3d0 *g*)) (/ (- q) (* 6d0 *g*))
          (/ (- q) (* 6d0 *g*)) 0d0 0d0 0d0))
(defun update-point (strain material &optional (kappa 0d0) (dt .1d0))
  (clay-creep-update strain *e* *nu* material kappa dt))
(defun vector-close (actual expected tolerance)
  (check (= (length actual) (length expected)) "Vector lengths differ.")
  (dotimes (i (length expected)) (close-to (elt actual i) (elt expected i) tolerance)))
(defun native (material)
  (make-instance 'particle-clay-creep :E *e* :nu *nu* :creep-law material
                 :enable-plasticity t :enable-creep t))
(defun set-native-strain (mp values)
  (replace (cl-mpm/utils:fast-storage (cl-mpm/particle:mp-strain mp)) values))
(defun native-signature (mp)
  "Snapshots are independent; signature covers numeric public and engine state."
  (loop for entry in (first (snapshot-clay-creep-particle mp))
        collect (list (first entry) (second entry)
                      (let ((value (third entry)))
                        (if (typep value 'magicl:matrix/double-float)
                            (coerce (cl-mpm/utils:fast-storage value) 'list) value)))))

(point-check "explicit law parameters reject invalid viscosity/strength/softening"
  (check (rejects (lambda () (law :eta 0d0))) "Zero viscosity was accepted.")
  (check (rejects (lambda () (law :residual 60d3))) "Residual exceeds peak.")
  (check (rejects (lambda () (law :softening 0d0))) "Zero strain scale accepted.")
  (check (rejects (lambda () (update-point (shear-strain 60d3)
                                          (law :peak 50d3 :residual 0d0 :softening 1d-6))))
         "H >=3G must reject, rather than cap its parameters."))

(point-check "zero time, disabled creep and under-threshold response stay elastic"
  (let* ((material (law)) (strain (shear-strain 40d3)))
    (dolist (result (list (update-point strain material)
                          (update-point (shear-strain 100d3) material 0d0 0d0)
                          (clay-creep-update (shear-strain 100d3) *e* *nu* material 0d0 1d0
                                             :enabled nil)))
      (close-to (clay-creep-result-kappa result) 0d0 0d0)
      (close-to (clay-creep-result-rate result) 0d0 0d0)
      (close-to (clay-creep-result-work result) 0d0 0d0))))

(point-check "hydrostatic pressure never produces J2 creep"
  (let* ((strain #( -.01d0 -.01d0 -.01d0 0d0 0d0 0d0))
         (result (update-point strain (law))))
    (close-to (clay-creep-result-q result) 0d0 0d0)
    (close-to (clay-creep-result-kappa result) 0d0 0d0)
    (vector-close (clay-creep-result-elastic-strain result) strain 0d0)))

(point-check "analytic shear stress relaxation matches backward Euler and Voigt factors"
  (let* ((material (law :eta 5d6)) (dt .2d0) (qtrial 100d3)
         (result (update-point (shear-strain qtrial) material 0d0 dt))
         (expected (+ 50d3 (/ (- qtrial 50d3) (+ 1d0 (/ (* 3d0 *g* dt) 5d6))))))
    (close-to (clay-creep-result-q result) expected 1d-8)
    (close-to (aref (clay-creep-result-tau result) 5) (/ expected (sqrt 3d0)) 1d-8)
    (close-to (clay-creep-result-rate result) (/ (- expected 50d3) 5d6) 1d-13)
    (close-to (aref (clay-creep-result-plastic-increment result) 5)
              (* (sqrt 3d0) (clay-creep-result-delta result)) 1d-13)))

(point-check "normal and shear deviators give the same invariant radial update"
  (let* ((material (law :peak 50d3 :residual 20d3 :softening .02d0))
         (shear (update-point (shear-strain 100d3) material))
         (axial (update-point (axial-strain 100d3) material))
         (pressurized (update-point (shear-strain 100d3 200d3) material)))
    (close-to (clay-creep-result-kappa shear) (clay-creep-result-kappa axial) 1d-13)
    (close-to (clay-creep-result-kappa shear) (clay-creep-result-kappa pressurized) 1d-13)
    (close-to (loop for i below 3 sum
                (aref (clay-creep-result-plastic-increment axial) i)) 0d0 1d-13)))

(point-check "residual strength kink is crossed by the exact piecewise BE root"
  (let* ((material (law :peak 60d3 :residual 20d3 :softening .01d0 :eta 1d6))
         (result (update-point (shear-strain 500d3) material .009d0 1d0))
         (expected (/ (- 500d3 20d3) (+ 1d6 (* 3d0 *g*)))))
    (check (> (clay-creep-result-kappa result) .01d0) "Residual branch was not crossed.")
    (close-to (clay-creep-result-delta result) expected 1d-13)
    (close-to (clay-creep-result-yield result) 20d3 1d-8)
    (close-to (clay-creep-result-rate result)
              (/ (- (clay-creep-result-q result) 20d3) 1d6) 1d-13)))

(point-check "discrete dissipation equals tau dot engineering plastic strain and is nonnegative"
  (let* ((result (update-point (shear-strain 100d3 250d3)
                               (law :peak 50d3 :residual 20d3 :softening .02d0)))
         (dot (loop for i below 6 sum
                (* (aref (clay-creep-result-tau result) i)
                   (aref (clay-creep-result-plastic-increment result) i)))))
    (check (> dot 0d0) "Nonpositive dissipative increment.")
    (close-to dot (clay-creep-result-work result) 1d-8)))

(defun imposed-stress-step (q-held kappa material dt)
  "Solve strain control required by a constant q apparatus; never prescribe kappa.
Outer monotone bisection adjusts elastic trial shear. The pure material update
is the sole source of accepted kappa, dissipation and creep strain/rate."
  (let ((low q-held)
        (high (+ q-held (* 3d0 *g* dt (/ q-held (clay-creep-law-viscosity material)))))
        (result nil))
    (dotimes (i 70)
      (let ((trial (* .5d0 (+ low high))))
        (setf result (update-point (shear-strain trial) material kappa dt))
        (if (> (clay-creep-result-q result) q-held)
            (setf high trial) (setf low trial))))
    (close-to (clay-creep-result-q result) q-held 1d-7 "held q")
    result))

(defun integrate-hold (q material dt duration &optional stream)
  (let ((kappa 0d0) (work 0d0) (steps (round (/ duration dt))))
    (when stream
      (format stream "step,time_s,q_kirchhoff_pa,kappa_eq,strain_percent,shear_strain_percent,rate_per_s,yield_kirchhoff_pa,work_be_pa~%")
      (format stream "0,0.0,~,16E,0.0,0.0,0.0,~,16E,~,16E,0.0~%"
              q (/ (- q (clay-creep-yield material 0d0)) (clay-creep-law-viscosity material))
              (clay-creep-yield material 0d0)))
    (dotimes (i steps)
      (let ((result (imposed-stress-step q kappa material dt)))
        (setf kappa (clay-creep-result-kappa result))
        (incf work (clay-creep-result-work result))
        (when stream
          (format stream "~D,~,16E,~,16E,~,16E,~,16E,~,16E,~,16E,~,16E,~,16E~%"
                  (1+ i) (* (1+ i) dt) (clay-creep-result-q result) kappa (* 100d0 kappa)
                  (* 100d0 (sqrt 3d0) kappa) (clay-creep-result-rate result)
                  (clay-creep-result-yield result) work))))
    kappa))

(point-check "constant imposed stress produces secondary creep and softening acceleration"
  (let* ((constant (law :peak 50d3 :eta 5d6))
         (soft (law :peak 50d3 :residual 20d3 :softening .05d0 :eta 5d6))
         (q 60d3) (duration 1d0) (dt .01d0)
         (constant-k (integrate-hold q constant dt duration))
         (soft-k (integrate-hold q soft dt duration))
         (h (/ 30d3 .05d0))
         (exact (* (/ (- q 50d3) h) (- (exp (/ (* h duration) 5d6)) 1d0))))
    (close-to constant-k (/ (* duration (- q 50d3)) 5d6) 1d-12)
    (check (> soft-k constant-k) "Softening did not accelerate strain under held stress.")
    (check (< (abs (- soft-k exact)) 3d-6) "Held-stress solution misses analytic creep law.")))

(point-check "time refinement approaches analytic stress relaxation and creep-hold strain"
  (let* ((material (law :peak 50d3 :eta 5d6)) (duration .2d0)
         (exact-q (+ 50d3 (* 50d3 (exp (- (/ (* 3d0 *g* duration) 5d6))))))
         (soft (law :peak 50d3 :residual 20d3 :softening .05d0 :eta 5d6))
         (h (/ 30d3 .05d0))
         (exact-k (* (/ 10d3 h) (- (exp (/ h 5d6)) 1d0))))
    (labels ((relax (dt)
               (let ((strain (shear-strain 100d3)) (kappa 0d0) (last-q 100d3))
                 (dotimes (i (round (/ duration dt)))
                   (let ((result (update-point strain material kappa dt)))
                     (setf strain (clay-creep-result-elastic-strain result)
                           kappa (clay-creep-result-kappa result)
                           last-q (clay-creep-result-q result))))
                 last-q)))
      (check (< (abs (- (relax .01d0) exact-q))
                 (abs (- (relax .02d0) exact-q))) "Relaxation refinement did not improve.")
      (check (< (abs (- (integrate-hold 60d3 soft .01d0 1d0) exact-k))
                 (abs (- (integrate-hold 60d3 soft .02d0 1d0) exact-k)))
             "Held-stress refinement did not improve."))))

(point-check "native adapter trial is repeatable, commits once and resets all saved history"
  (let* ((mp (native (law :peak 50d3 :residual 20d3 :softening .02d0)))
         (strain (shear-strain 100d3)) (initial (native-signature mp)))
    (set-native-strain mp strain)
    (cl-mpm/particle:constitutive-model mp (cl-mpm/particle:mp-strain mp) .1d0)
    (let ((kappa (particle-kappa mp)) (work (particle-work mp)))
      (set-native-strain mp strain)
      (cl-mpm/particle:constitutive-model mp (cl-mpm/particle:mp-strain mp) .1d0)
      (close-to (particle-kappa mp) kappa 0d0 "repeat trial kappa")
      (close-to (particle-work mp) work 0d0 "repeat trial work"))
    (cl-mpm/particle::reset-loadstep-mp mp)
    (check (equalp initial (native-signature mp)) "Reset did not restore committed numeric state.")
    (set-native-strain mp strain)
    (cl-mpm/particle:constitutive-model mp (cl-mpm/particle:mp-strain mp) .1d0)
    (cl-mpm/particle::new-loadstep-mp mp)
    (let ((committed (particle-kappa mp)))
      (set-native-strain mp strain)
      (cl-mpm/particle:constitutive-model mp (cl-mpm/particle:mp-strain mp) .1d0)
      (check (> (particle-kappa mp) committed) "New accepted loadstep failed to advance kappa.")
      (cl-mpm/particle::reset-loadstep-mp mp)
      (close-to (particle-kappa mp) committed 0d0))))

(point-check "failed native constitutive trial cannot alter committed or trial history"
  (let ((mp (native (law))))
    (set-native-strain mp (shear-strain 100d3))
    (let ((before (native-signature mp)))
      (check (rejects (lambda ()
                        (cl-mpm/particle:constitutive-model mp (cl-mpm/particle:mp-strain mp) -.1d0)))
             "Negative physical time accepted.")
      (check (equalp before (native-signature mp)) "Failed update mutated native particle."))
    (let ((f (cl-mpm/particle::mp-deformation-gradient mp)))
      (setf (magicl:tref f 0 0) -1d0)
      (let ((before (native-signature mp)))
        (check (rejects (lambda ()
                          (cl-mpm/particle:constitutive-model mp (cl-mpm/particle:mp-strain mp) .1d0)))
               "Negative det(F) accepted.")
        (check (equalp before (native-signature mp)) "Bad-J failure mutated particle.")))))

(point-check "native creep switch leaves stresses and history intact while disabling flow"
  (let ((mp (native (law))))
    (setf (particle-enable-creep mp) nil)
    (set-native-strain mp (shear-strain 100d3))
    (cl-mpm/particle:constitutive-model mp (cl-mpm/particle:mp-strain mp) 1d0)
    (close-to (particle-kappa mp) 0d0 0d0)
    (close-to (particle-rate mp) 0d0 0d0)
    (close-to (aref (cl-mpm/utils:fast-storage (cl-mpm/particle::mp-stress-kirchoff mp)) 5)
              (/ 100d3 (sqrt 3d0)) 1d-8)
    (setf (particle-enable-creep mp) t)
    (cl-mpm/particle:constitutive-model mp (cl-mpm/particle:mp-strain mp) 1d0)
    (check (> (particle-kappa mp) 0d0) "Enabling creep failed to allow stress-driven flow.")))

(point-check "material hold CSV stores actual accepted point solutions"
  (let* ((arguments (cl-user::cl-mpm-script-args))
         (directory (uiop:ensure-directory-pathname
                     (or (first arguments) "output/clay-creep-points/"))))
    (ensure-directories-exist directory)
    (dolist (entry (list (list "constant-strength-hold.csv" (law :eta 5d6))
                         (list "softening-hold.csv"
                               (law :peak 50d3 :residual 20d3 :softening .05d0 :eta 5d6))))
      (with-open-file (stream (merge-pathnames (first entry) directory)
                              :direction :output :if-exists :error :if-does-not-exist :create)
        (integrate-hold 60d3 (second entry) .01d0 5d0 stream)))
    (format t "~&Point hold CSV evidence: ~A~%" directory)))

(if *failures*
    (progn
      (format t "~&CLAY CREEP POINTS FAIL: ~D passed; ~D failed.~%" *checks* (length *failures*))
      (dolist (failure (reverse *failures*)) (format t "~&  ~A: ~A~%" (first failure) (second failure)))
      (uiop:quit 1))
    (progn (format t "~&CLAY CREEP POINTS PASS: ~D passed; 0 failed.~%" *checks*) (uiop:quit 0)))
