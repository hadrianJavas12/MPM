;;;; Native fixed-frame Soil2 POINT controls, zero particle/solver updates.
;;;; windows\cl-mpm.cmd tests\materials\wang2017-projection.lisp FRESH.json
;;;; Optional WANG2017_POINT_SOURCE_ROOT explicitly loads copied source bytes.
(in-package :cl-user)
(require :asdf)
(ql:quickload :yason :silent t)
(let ((frozen (uiop:getenv "WANG2017_POINT_SOURCE_ROOT")))
  (if frozen
      (dolist (relative '("materials/models/plastic/mohr-coulomb-evolution/package.lisp"
                          "materials/models/plastic/mohr-coulomb-evolution/law.lisp"
                          "materials/models/plastic/mohr-coulomb-evolution/diagnostics.lisp"
                          "materials/models/plastic/mohr-coulomb-evolution/projection.lisp"
                          "materials/models/plastic/wang2017/package.lisp"
                          "materials/models/plastic/wang2017/history.lisp"
                          "materials/models/plastic/wang2017/law.lisp"
                          "materials/models/plastic/wang2017/point-projection.lisp"))
        (let ((path (merge-pathnames relative (uiop:ensure-directory-pathname frozen))))
          (format t "~&LOADING EXACT POINT SOURCE: ~A~%" (truename path))
          (load path)))
      (ql:quickload :cl-mpm/models/wang2017-point :silent t)))

(defpackage :cl-mpm/tests/wang2017-projection
  (:use :cl :cl-mpm/models/wang2017 :cl-mpm/models/wang2017-point))
(in-package :cl-mpm/tests/wang2017-projection)
(defvar *labels* nil)
(defvar *failures* nil)
(defparameter *q* #2A((1d0 0d0 0d0) (0d0 1d0 0d0) (0d0 0d0 1d0)))
(defconstant +e+ 20d6)
(defconstant +nu+ .25d0)
(defconstant +g+ 8d6)
(defparameter *phi* (* 35d0 (/ pi 180d0)))

(defmacro control (label &body body)
  `(handler-case (progn ,@body (push ,label *labels*) (format t "~&PASS: ~A~%" ,label))
     (error (c) (push (format nil "~A: ~A" ,label c) *failures*)
       (format t "~&FAIL: ~A: ~A~%" ,label c))))
(defun close-value (actual expected &optional (tol 1d-11))
  (unless (<= (abs (- actual expected)) tol)
    (error "Expected ~,17G, actual ~,17G, tolerance ~G" expected actual tol)))
(defun close-vector (actual expected &optional (tol 1d-11))
  (assert (= (length actual) (length expected)))
  (dotimes (i (length actual)) (close-value (elt actual i) (elt expected i) tol)))
(defun rejected-p (thunk &optional reason)
  (handler-case (progn (funcall thunk) nil)
    (mc-evolution:material-integration-error (c)
      (or (not reason) (search reason (mc-evolution:integration-error-reason c))))))
(defun project (trial &optional (state (make-paper-history)) (q *q*) (j 1d0))
  (project-paper-principal trial +e+ +nu+ j state q))
(defun shear-trial (increment target-k &optional (j 1d0))
  (let ((t1 (+ (* 2d0 +g+ increment) (* j (soil2-cohesion target-k) (cos *phi*)))))
    (vector t1 0d0 (- t1))))

;; Independent public-result verification, without the legacy J2 coordinate.
(defun verify (p trial old q &optional (j 1d0))
  (let* ((tau (paper-projection-tau p)) (b (paper-projection-plastic-increment p))
         (delta (paper-projection-fixed-increment p))
         (next (history-tensor (paper-projection-history p)))
         (mu (paper-projection-multipliers p))
         (pairs '((0 1) (0 2) (1 0) (1 2) (2 0) (2 1)))
         (flow (vector 0d0 0d0 0d0)) (s (sin *phi*))
         (c (soil2-cohesion (paper-kps next))))
    (close-vector next (map 'vector #'+ (history-tensor old) delta))
    (close-value (paper-projection-kps p) (paper-kps next))
    (close-value (paper-projection-cohesion p) c 1d-7)
    (close-value (paper-projection-history-residual p) 0d0 1d-13)
    (close-value (paper-projection-phi p) *phi*)
    (assert (zerop (paper-projection-psi p)))
    (loop for (a z) in pairs for index from 0
          for residual = (- (* (+ 1d0 s) (aref tau a))
                            (* (- 1d0 s) (aref tau z)) (* 2d0 j c (cos *phi*))) do
      (assert (<= residual 2d-6))
      (assert (>= (aref mu index) -1d-12))
      (incf (aref flow a) (aref mu index))
      (decf (aref flow z) (aref mu index))
      (when (member index (paper-projection-active p)) (close-value residual 0d0 2d-6)))
    (close-vector b flow)
    (close-value (reduce #'+ b) 0d0 1d-13)
    (dotimes (i 3) (close-value (- (aref trial i) (aref tau i)) (* 2d0 +g+ (aref b i)) 2d-6))
    (let ((matrix (make-array '(3 3) :initial-element 0d0)))
      (dotimes (i 3) (dotimes (z 3) (dotimes (a 3)
        (incf (aref matrix i z) (* (aref q i a) (aref b a) (aref q z a))))))
      (close-vector delta (vector (aref matrix 0 0) (aref matrix 1 1) (aref matrix 2 2)
                                 (aref matrix 1 2) (aref matrix 2 0) (aref matrix 0 1))))
    (let ((work (loop for i below 3 sum (* (aref tau i) (aref b i)))))
      (close-value (paper-projection-work p) work 1d-8)
      (assert (>= work -1d-10))) p))

(defun rotate-tensor (ep q)
  (let ((m (make-array '(3 3))) (r (make-array '(3 3) :initial-element 0d0)))
    (setf (aref m 0 0) (aref ep 0) (aref m 1 1) (aref ep 1) (aref m 2 2) (aref ep 2)
          (aref m 1 2) (aref ep 3) (aref m 2 1) (aref ep 3)
          (aref m 2 0) (aref ep 4) (aref m 0 2) (aref ep 4)
          (aref m 0 1) (aref ep 5) (aref m 1 0) (aref ep 5))
    (dotimes (i 3) (dotimes (z 3) (dotimes (a 3) (dotimes (b 3)
      (incf (aref r i z) (* (aref q i a) (aref m a b) (aref q z b)))))))
    (vector (aref r 0 0) (aref r 1 1) (aref r 2 2)
            (aref r 1 2) (aref r 2 0) (aref r 0 1))))

(control "Elastic trial preserves signed tensor and current strength without a plastic update"
  (let* ((state (make-paper-history #(.003d0 -.001d0 -.002d0 .002d0 0d0 .004d0)))
         (p (verify (project #(-10000d0 -20000d0 -30000d0) state)
                    #(-10000d0 -20000d0 -30000d0) state *q*)))
    (assert (eq (paper-projection-branch p) :elastic))
    (close-vector (history-tensor (paper-projection-history p)) (history-tensor state))))

(control "Analytic zero-mean pure shear solves lambda=(t-c0*cos(phi))/(2G-softening*cos(phi))"
  (let* ((target .005d0) (trial (shear-trial target target))
         (analytic (/ (- (aref trial 0) (* 30000d0 (cos *phi*)))
                      (- (* 2d0 +g+) (* 750000d0 (cos *phi*)))))
         (state (make-paper-history)) (p (verify (project trial state) trial state *q*)))
    (close-value (paper-projection-kps p) analytic)
    (close-vector (paper-projection-plastic-increment p) (vector analytic 0d0 (- analytic)))
    (assert (eq (paper-projection-branch p) :softening))))

(control "Cauchy cohesion is consistently multiplied by supplied J in Kirchhoff stress"
  (let* ((j 1.07d0) (target .004d0) (trial (shear-trial target target j))
         (state (make-paper-history)) (p (verify (project trial state *q* j) trial state *q* j)))
    (close-value (paper-projection-kps p) target)))

(control "Multiple monotonic point updates couple total signed norm rather than native J2 history"
  (let ((state (make-paper-history)) (previous 0d0))
    (dolist (target '(.003d0 .008d0 .015d0 .025d0))
      (let* ((trial (shear-trial (- target previous) target))
             (p (verify (project trial state) trial state *q*)))
        (close-value (paper-projection-kps p) target)
        (close-vector (history-tensor (paper-projection-history p)) (vector target 0d0 (- target) 0d0 0d0 0d0))
        (setf state (paper-projection-history p) previous target)))))

(control "Nonproportional physical shear and principal increment use norm of the accumulated tensor"
  (let* ((state (make-paper-history #(0d0 0d0 0d0 0d0 0d0 .006d0)))
         (trial (shear-trial .008d0 .01d0))
         (p (verify (project trial state) trial state *q*)))
    (close-value (paper-projection-kps p) .01d0)
    (assert (> (abs (- (paper-projection-kps p) .014d0)) .003d0))
    (close-vector (history-tensor (paper-projection-history p)) #(.008d0 0d0 -.008d0 0d0 0d0 .006d0))))

(control "Literal signed reversal reduces kps and increases cohesion without an irreversible maximum"
  (let* ((state (make-paper-history #(.01d0 0d0 -.01d0 0d0 0d0 0d0)))
         (trial (map 'vector #'- (shear-trial .004d0 .006d0)))
         (p (verify (project trial state) trial state *q*)))
    (close-value (paper-projection-kps p) .006d0)
    (close-value (paper-projection-cohesion p) 25500d0 1d-7)
    (assert (< (paper-projection-kps p) (history-kps state)))))

(control "Reversal through zero retains signed tensor orientation"
  (let* ((state (make-paper-history #(.01d0 0d0 -.01d0 0d0 0d0 0d0)))
         (trial (map 'vector #'- (shear-trial .016d0 .006d0)))
         (p (verify (project trial state) trial state *q*)))
    (close-value (paper-projection-kps p) .006d0)
    (close-vector (history-tensor (paper-projection-history p)) #(-.006d0 0d0 .006d0 0d0 0d0 0d0))))

(control "Rotating old tensor and principal basis preserves stress and rotates retained history"
  (let* ((angle .37d0) (cs (cos angle)) (sn (sin angle))
         (q (make-array '(3 3) :initial-contents
                        (list (list cs (- sn) 0d0) (list sn cs 0d0) '(0d0 0d0 1d0))))
         (ep #(.004d0 -.002d0 -.002d0 .001d0 .002d0 .003d0))
         (state (make-paper-history ep)) (rotated (make-paper-history (rotate-tensor ep q)))
         (target (paper-kps (map 'vector #'+ ep #(.005d0 0d0 -.005d0 0d0 0d0 0d0))))
         (trial (shear-trial .005d0 target))
         (p (verify (project trial state) trial state *q*))
         (r (verify (project trial rotated q) trial rotated q)))
    (close-vector (paper-projection-tau r) (paper-projection-tau p) 1d-6)
    (close-value (paper-projection-kps r) (paper-projection-kps p))
    (close-vector (history-tensor (paper-projection-history r))
                  (rotate-tensor (history-tensor (paper-projection-history p)) q))))

(control "All six trial permutations move basis columns consistently and restore output axis order"
  (let* ((state (make-paper-history #(0d0 0d0 0d0 .001d0 .002d0 .003d0)))
         (target (paper-kps #(.004d0 0d0 -.004d0 .001d0 .002d0 .003d0)))
         (trial (shear-trial .004d0 target))
         (reference (project trial state)))
    (dolist (perm '(#(0 1 2) #(0 2 1) #(1 0 2) #(1 2 0) #(2 0 1) #(2 1 0)))
      (let ((q (make-array '(3 3) :initial-element 0d0))
            (input (map 'vector (lambda (i) (aref trial i)) perm)))
        (dotimes (a 3) (setf (aref q (aref perm a) a) 1d0))
        (let ((p (verify (project input state q) input state q)))
          (dotimes (a 3) (close-value (aref (paper-projection-tau p) a)
                                      (aref (paper-projection-tau reference) (aref perm a)) 1d-6))
          (close-vector (history-tensor (paper-projection-history p))
                        (history-tensor (paper-projection-history reference))))))))

(control "Residual tail explicitly solves norm(Ep_old+deltaEp_res) above .02"
  (let* ((state (make-paper-history #(0d0 0d0 0d0 0d0 0d0 .02d0)))
         (target (sqrt (+ (expt .02d0 2) (expt .015d0 2))))
         (trial (shear-trial .015d0 target))
         (p (verify (project trial state) trial state *q*)))
    (close-value (paper-projection-kps p) .025d0)
    (close-value (paper-projection-cohesion p) 15000d0)
    (assert (eq (paper-projection-branch p) :residual))))

(control "Residual-to-softening reversal searches below old coordinate and below the tail"
  (let* ((state (make-paper-history #(.025d0 0d0 -.025d0 0d0 0d0 0d0)))
         (trial (map 'vector #'- (shear-trial .015d0 .01d0)))
         (p (verify (project trial state) trial state *q*)))
    (close-value (paper-projection-kps p) .01d0)
    (assert (eq (paper-projection-branch p) :softening))))

(control "Inputs and copy-returning readers do not expose or mutate retained result state"
  (let* ((ep (vector 0d0 0d0 0d0 0d0 0d0 .003d0)) (state (make-paper-history ep))
         (trial (shear-trial .004d0 .005d0)) (original (copy-seq trial))
         (q (make-array '(3 3) :initial-contents '((1d0 0d0 0d0) (0d0 1d0 0d0) (0d0 0d0 1d0))))
         (p (project trial state q)) (saved (history-tensor (paper-projection-history p))))
    (close-vector trial original)
    (close-vector (history-tensor state) ep)
    (setf (aref trial 0) 999d0 (aref q 0 0) 999d0 (aref ep 5) 999d0)
    (setf (aref (paper-projection-tau p) 0) 999d0
          (aref (paper-projection-fixed-increment p) 0) 999d0
          (aref (history-tensor (paper-projection-history p)) 0) 999d0)
    (close-vector (history-tensor (paper-projection-history p)) saved)
    (close-value (history-kps state) .003d0)))

(control "Captured tensile apex trial remains rejected and committed tensor remains untouched"
  (let* ((state (make-paper-history)) (before (history-tensor state))
         (trial #(42976.78027359978d0 42980.96616175191d0 42998.36671139691d0)))
    (assert (rejected-p (lambda () (project trial state *q* 1.0032291051924629d0))
                        "No admissible"))
    (close-vector (history-tensor state) before)))

(control "Malformed basis, invalid elasticity and non-history inputs reject before state mutation"
  (let ((state (make-paper-history #(0d0 0d0 0d0 0d0 0d0 .003d0))))
    (assert (rejected-p (lambda () (project #(0d0 0d0 0d0) state #2A((2 0 0) (0 1 0) (0 0 1))))))
    (assert (rejected-p (lambda () (project-paper-principal #(0 0 0) -1d0 +nu+ 1d0 state *q*))))
    (assert (rejected-p (lambda () (project-paper-principal #(0 0 0) +e+ .5d0 1d0 state *q*))))
    (assert (rejected-p (lambda () (project-paper-principal #(0 0 0) +e+ +nu+ 0d0 state *q*))))
    (assert (rejected-p (lambda () (project #(0 0 0) #(0 0 0 0 0 0)))))
    (close-value (history-kps state) .003d0)))

(control "Quadratic enumeration retains two real roots and stable small root without cancellation"
  (multiple-value-bind (roots identity) (cl-mpm/models/wang2017-point::real-quadratic-roots 1d0 -1d8 1d0)
    (assert (not identity)) (assert (= (length roots) 2))
    (close-value (reduce #'min roots) 1d-8 1d-22)
    (close-value (reduce #'max roots) 1d8 1d-7)))
(control "Linear, repeated, non-real and identity polynomial cases are explicitly distinguished"
  (close-vector (cl-mpm/models/wang2017-point::real-quadratic-roots 0d0 2d0 -4d0) #(2d0))
  (close-vector (cl-mpm/models/wang2017-point::real-quadratic-roots 1d0 -2d0 1d0) #(1d0))
  (assert (null (cl-mpm/models/wang2017-point::real-quadratic-roots 1d0 0d0 1d0)))
  (assert (nth-value 1 (cl-mpm/models/wang2017-point::real-quadratic-roots 0d0 0d0 0d0))))

(let ((output (first (cl-user::cl-mpm-script-args))) (record (make-hash-table :test 'equal)))
  (assert output)
  (setf (gethash "passed" record) (if *failures* 'yason:false t)
        (gethash "controlsCount" record) (length *labels*)
        (gethash "controlLabels" record) (coerce (reverse *labels*) 'vector)
        (gethash "failures" record) (coerce (reverse *failures*) 'vector)
        (gethash "physicalUpdatesExecuted" record) 0
        (gethash "particleAdapterImplemented" record) 'yason:false
        (gethash "finiteStrainTransportImplemented" record) 'yason:false
        (gethash "irreversibleMaximumApplied" record) 'yason:false
        (gethash "scope" record) "Pure small-strain fixed-frame signed-tensor Soil2 point return; literal reversal may increase cohesion; no slope or scientific validation")
  (ensure-directories-exist output)
  (with-open-file (stream output :direction :output :if-exists :error) (yason:encode record stream)))
(format t "~&WANG2017 POINT: ~D PASS, ~D FAIL; zero physical updates.~%" (length *labels*) (length *failures*))
(uiop:quit (if *failures* 1 0))
