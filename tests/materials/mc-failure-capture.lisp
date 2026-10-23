;;;; Failure capture/replay controls only; no MPM updates or spatial simulations.
;;;; windows\cl-mpm.cmd tests\materials\mc-failure-capture.lisp [FRESH.json]
(in-package :cl-user)
(ql:quickload :cl-mpm-framework :silent t)

(defpackage :cl-mpm/tests/mc-failure-capture
  (:use :cl :cl-mpm/models/mc-evolution))
(in-package :cl-mpm/tests/mc-failure-capture)

(defparameter *checks* 0)
(defparameter *pure-fixture-diagnostic* nil)
(defparameter *native-fixture-diagnostic* nil)
(defparameter *output-path*
  (let ((arguments (cl-user::cl-mpm-script-args)))
    (when (> (length arguments) 1) (error "Supply at most one fresh output JSON path."))
    (when arguments
      (let ((path (pathname (first arguments))))
        (unless (and (pathname-name path) (string-equal (or (pathname-type path) "") "json"))
          (error "Failure-capture report requires a .json file path."))
        (when (probe-file path) (error "Failure-capture report must not already exist: ~A" path))
        path))))
(defmacro capture-check (label &body forms)
  `(progn ,@forms (incf *checks*) (format t "~&PASS: ~A~%" ,label)))

(defun capture-material-error (thunk)
  (handler-case
      (progn (funcall thunk) (error "Expected a material-integration-error."))
    (material-integration-error (condition) condition)))

(defun capture-law (&key (variant :perfect) (stress-measure :cauchy) (psi 0d0))
  (make-evolution-law :variant variant :points '((0d0 30d0) (.01d0 35d0) (.1d0 33d0))
                      :cohesion-points '((0d0 10d3) (.01d0 12d3) (.1d0 11d3))
                      :peak-kappa .01d0 :psi psi :stress-measure stress-measure
                      :strain-assumption "Failure-capture fixture; not Wang failed-update evidence"))

(defun failure-fixture ()
  (let ((trial (vector 40d3 40d3 40d3))
        (law (capture-law)))
    (values (capture-material-error
             (lambda () (project-principal trial 24d6 .2d0 1.0123456789012345d0 law .02d0)))
            trial law)))

(defun json-roundtrip (record)
  (let ((encoded (with-output-to-string (stream) (yason:encode record stream))))
    (with-input-from-string (stream encoded)
      (yason:parse stream :object-as :hash-table :json-arrays-as-vectors t))))

(defun freeze-state (value &optional seen)
  ;; Same kind of complete bound-slot fingerprint as the native MC point suite;
  ;; it observes current/committed state without changing either transaction.
  (cond ((or (null value) (numberp value) (symbolp value)) value)
        ((stringp value) (copy-seq value))
        ((typep value 'magicl:matrix/double-float)
         (list :matrix (copy-list (magicl:shape value))
               (coerce (cl-mpm/utils:fast-storage value) 'list)))
        ((consp value) (cons (freeze-state (car value) seen) (freeze-state (cdr value) seen)))
        ((arrayp value)
         (list :array (array-dimensions value)
               (loop for i below (array-total-size value)
                     collect (freeze-state (row-major-aref value i) seen))))
        ((or (typep value 'standard-object) (typep value 'structure-object))
         (if (member value seen :test #'eq) (list :cycle (class-name (class-of value)))
             (list (class-name (class-of value))
                   (loop for slot in (sb-mop:class-slots (class-of value))
                         for name = (sb-mop:slot-definition-name slot)
                         collect (list name (if (slot-boundp value name)
                                                (freeze-state (slot-value value name) (cons value seen))
                                                :unbound))))))
        (t (error "Unhandled native state object ~S." (type-of value)))))

(defun compliance-voigt (values e nu)
  (let ((strain (make-array 6 :element-type 'double-float :initial-element 0d0))
        (g (/ e (* 2d0 (+ 1d0 nu)))))
    (dotimes (i 3)
      (setf (aref strain i)
            (/ (- (elt values i) (* nu (loop for k below 3 unless (= i k) sum (elt values k)))) e)))
    (loop for i from 3 below 6 do (setf (aref strain i) (/ (elt values i) g)))
    (cl-mpm/utils:voigt-from-list (coerce strain 'list))))

(capture-check "Known zero-dilation apex still rejects, preserving legacy reason/details and exact inputs"
  (multiple-value-bind (condition trial law) (failure-fixture)
    (declare (ignore law))
    (let ((record (integration-error-diagnostic condition)))
      (setf *pure-fixture-diagnostic* record)
      (assert (string= (integration-error-reason condition)
                       "No admissible coupled active-set solution; no apex clamp or strength floor applied"))
      (assert (equalp (getf (integration-error-details condition) :trial) (coerce trial 'list)))
      (assert (= (getf (integration-error-details condition) :old-kappa) .02d0))
      (assert (integerp (getf (integration-error-details condition) :evaluations)))
      (assert (hash-table-p record))
      (assert (equalp (gethash "trialKirchhoffPa" record) trial))
      (assert (= (gethash "youngsModulusPa" record) 24d6))
      (assert (= (gethash "poissonRatio" record) .2d0))
      (assert (= (gethash "deformationJacobian" record) 1.0123456789012345d0))
      (assert (= (gethash "oldKappa" record) .02d0)))))

(capture-check "Captured trial, law tables and assumption text do not alias caller inputs"
  (multiple-value-bind (condition trial law) (failure-fixture)
    (let* ((record (integration-error-diagnostic condition))
           (before (json-roundtrip record)))
      (setf (aref trial 0) -999d3
            (second (first (evolution-law-points law))) 10d0
            (second (first (evolution-law-cohesion-points law))) 1d0
            (char (evolution-law-strain-assumption law) 0) #\X)
      (assert (equalp record before)))))

(capture-check "In-memory and JSON-roundtrip payloads reproduce the same pure-projector failure"
  (let* ((original (failure-fixture))
         (record (integration-error-diagnostic original)))
    (dolist (replay-record (list record (json-roundtrip record)))
      (let ((replayed (capture-material-error
                       (lambda () (replay-integration-diagnostic replay-record)))))
        (assert (equalp record (integration-error-diagnostic replayed)))
        (assert (string= (integration-error-reason original) (integration-error-reason replayed)))
        (assert (equalp (integration-error-details original) (integration-error-details replayed)))))))

(capture-check "Replay uses supplied J rather than a default or inferred Jacobian"
  (let* ((record (json-roundtrip (integration-error-diagnostic (failure-fixture))))
         ;; At J=3 the same Cauchy-strength cone contains this hydrostatic trial.
         ;; A hidden J=1 fallback would incorrectly reproduce the rejection.
         (trial (gethash "trialKirchhoffPa" record)))
    (setf (gethash "deformationJacobian" record) 3d0)
    (let ((accepted (replay-integration-diagnostic record)))
      (assert (equalp (projection-tau accepted) trial))
      (assert (null (projection-active accepted))))))

(capture-check "Complete law parameters survive capture/JSON replay for all declared variants and stress measures"
  (dolist (variant '(:perfect :h :hs))
    (dolist (measure '(:cauchy :kirchhoff))
      (let* ((law (capture-law :variant variant :stress-measure measure))
             (condition (capture-material-error
                         (lambda () (project-principal #(80d3 80d3 80d3)
                                                       24d6 .2d0 1.01d0 law .02d0))))
             (record (json-roundtrip (integration-error-diagnostic condition)))
             (law-record (gethash "law" record))
             (replayed (capture-material-error
                        (lambda () (replay-integration-diagnostic record)))))
        (assert (string= (gethash "variant" law-record) (string-downcase (symbol-name variant))))
        (assert (equalp (gethash "points" law-record) #(#(0d0 30d0) #(.01d0 35d0) #(.1d0 33d0))))
        (assert (equalp (gethash "cohesionPoints" law-record) #(#(0d0 10d3) #(.01d0 12d3) #(.1d0 11d3))))
        (assert (= (gethash "psi" law-record) 0d0))
        (assert (string= (gethash "stressMeasure" law-record) (string-downcase (symbol-name measure))))
        (assert (string= (gethash "strainAssumption" law-record) (evolution-law-strain-assumption law)))
        (assert (= (gethash "peakKappa" law-record) .01d0))
        (assert (equalp record (integration-error-diagnostic replayed)))))))

(capture-check "Associated psi is retained and malformed replay records cannot invent J or schema"
  (let* ((law (capture-law :psi :associated))
         ;; Invalid elasticity deliberately exercises the pre-return failure path.
         (condition (capture-material-error
                     (lambda () (project-principal #(40d3 40d3 40d3) 24d6 .5d0 1.1d0 law .02d0))))
         (record (json-roundtrip (integration-error-diagnostic condition)))
         (replayed (capture-material-error (lambda () (replay-integration-diagnostic record)))))
    (assert (string= (gethash "psi" (gethash "law" record)) "associated"))
    (assert (string= (integration-error-reason replayed) "Invalid finite principal return input"))
    (remhash "deformationJacobian" record)
    (assert (handler-case (progn (replay-integration-diagnostic record) nil)
              (error (error) (search "Missing required MC diagnostic field" (princ-to-string error))))))
  (let ((record (json-roundtrip (integration-error-diagnostic (failure-fixture)))))
    (setf (gethash "schemaVersion" record) 2)
    (assert (handler-case (progn (replay-integration-diagnostic record) nil)
              (error (error) (search "Unsupported MC integration diagnostic schema" (princ-to-string error)))))))

(capture-check "Native rejected apex captures actual J and leaves every bound state slot/external strain unchanged"
  (let* ((law (make-evolution-law :variant :perfect :points '((0d0 30d0))
                                 :cohesion 10d3 :psi 0d0 :stress-measure :cauchy
                                 :strain-assumption "Native unchanged-state rejection fixture"))
         (mp (make-instance 'particle-mc-evolution :E 24d6 :nu .2d0
                                                  :evolution-law law :enable-plasticity t)))
    (setf (magicl:tref (cl-mpm/particle:mp-deformation-gradient mp) 0 0) 1.1d0)
    (cl-mpm/particle:constitutive-model mp (compliance-voigt #(-80d3 -100d3 -90d3 0d0 0d0 0d0)
                                                           24d6 .2d0) 1d-4)
    (cl-mpm/particle::new-loadstep-mp mp)
    (let* ((before (freeze-state mp))
           (strain (compliance-voigt #(20d3 20d3 20d3 0d0 0d0 0d0) 24d6 .2d0))
           (strain-before (freeze-state strain))
           (condition (capture-material-error
                       (lambda () (cl-mpm/particle:constitutive-model mp strain 1d-4))))
           (record (integration-error-diagnostic condition))
           (replayed (capture-material-error (lambda () (replay-integration-diagnostic record)))))
      (setf *native-fixture-diagnostic* record)
      (assert (equalp before (freeze-state mp)))
      (assert (equalp strain-before (freeze-state strain)))
      (assert (= (gethash "deformationJacobian" record)
                 (cl-mpm/fastmaths:det-3x3 (cl-mpm/particle:mp-deformation-gradient mp))))
      (assert (string= (integration-error-reason condition) (integration-error-reason replayed))))))

(when *output-path*
  (ensure-directories-exist *output-path*)
  (with-open-file (stream *output-path* :direction :output :if-exists :error
                                      :if-does-not-exist :create)
    (yason:encode
     (cl-mpm/models/mc-evolution::%diagnostic-object
      "passed" t "controlsCount" *checks* "physicalUpdatesExecuted" 0
      "scope" "Synthetic pure-projector and native constitutive rejection fixtures; JSON replay and unchanged native state; not original Wang failed-update evidence"
      "originalWangFailedStateCaptured" 'yason:false
      "scientificallyValidated" 'yason:false
      "pureFixture" *pure-fixture-diagnostic* "nativeFixture" *native-fixture-diagnostic*)
     stream)))
(format t "~&MC FAILURE CAPTURE: ~D controls passed; no MPM updates executed.~%" *checks*)
(uiop:quit 0)
