;;;; NEW optional capture controls only: synthetic rejections, never the lost fine update.
;;;; windows\cl-mpm.cmd tests\materials\mc-composite-apex-failure-capture.lisp output\FRESH
;;;; Eight groups; six helper-only failures, seven optional projector calls (two
;;;; native, two replay, three direct), nine optional replay attempts, one strict
;;;; replay schema rejection, one synthetic strict delegate; zero MPM updates.
(in-package :cl-user)
(require :asdf)
(setf *read-default-float-format* 'double-float)
(defvar *capture-frozen* nil)
(defvar *capture-directory* nil)
(defvar *capture-exit* 1)
(unless *capture-frozen* (load (cl-mpm-path "scripts/lisp/native-source-snapshot.lisp")))
(unless *capture-frozen*
  (let* ((arguments (cl-mpm-script-args))
         (directory (and (= (length arguments) 1)
                         (uiop:ensure-directory-pathname (merge-pathnames (first arguments))))))
    (unless directory (error "Provide one fresh capture-control output directory."))
    (when (and (probe-file directory) (or (uiop:directory-files directory) (uiop:subdirectories directory)))
      (error "Capture-control output must be fresh."))
    (snapshot-require-fresh-runtime)
    (multiple-value-bind (copied records) (snapshot-case-sources directory *load-truename*)
      (dolist (required '("source/materials/models/plastic/mc-composite-apex/package.lisp"
                          "source/materials/models/plastic/mc-composite-apex/diagnostics.lisp"
                          "source/materials/models/plastic/mc-composite-apex/projection.lisp"
                          "source/materials/models/plastic/mc-composite-apex/native.lisp"))
        (unless (find required records :test #'string= :key (lambda (row) (gethash "path" row)))
          (error "Required optional capture source was not frozen: ~A" required)))
      (snapshot-write-json (merge-pathnames "source/source-manifest.json" directory)
       (snapshot-object "scope" "New optional capture controls copied before project load; no original failure input"
                        "files" (coerce records 'vector)))
      (let ((*native-snapshot-context* (snapshot-register-native directory records))
            (*capture-frozen* t) (*capture-directory* directory))
        (snapshot-check-plan "cl-mpm/settings") (ql:quickload :cl-mpm/settings :silent t)
        (setf (symbol-value (find-symbol "*OPTIMISE-SETTING*" "CL-MPM/SETTINGS"))
              '(optimize (speed 3) (safety 1) (debug 1) (compilation-speed 0)))
        (dolist (system '("yason" "cl-mpm" "cl-mpm/models/mc-composite-apex"))
          (snapshot-check-plan system) (ql:quickload system :silent t))
        (write-case-source-provenance directory copied nil)
        (rename-file (merge-pathnames "source-provenance.json" directory)
                     (merge-pathnames "source-provenance-before.json" directory))
        (snapshot-write-json (merge-pathnames "source-proof-before.json" directory)
         (snapshot-object "files" (coerce (mapcar (lambda (path)
           (snapshot-object "path" (enough-namestring path directory) "sha256" (snapshot-sha256 path))) copied) 'vector)))
        (snapshot-verify-file (merge-pathnames "source/case.lisp" directory))
        (load (merge-pathnames "source/case.lisp" directory))
        (dolist (path copied) (snapshot-verify-file path))
        (write-case-source-provenance directory copied nil)
        (rename-file (merge-pathnames "source-provenance.json" directory)
                     (merge-pathnames "source-provenance-after.json" directory))
        (snapshot-write-json (merge-pathnames "source-proof-after.json" directory)
         (snapshot-object "files" (coerce (mapcar (lambda (path)
           (snapshot-object "path" (enough-namestring path directory) "sha256" (snapshot-sha256 path))) copied) 'vector))))))
  (uiop:quit *capture-exit*))

(defpackage :cl-mpm/tests/mc-composite-apex-failure-capture
  (:use :cl)
  (:local-nicknames (:mc :cl-mpm/models/mc-evolution) (:ap :cl-mpm/models/mc-composite-apex)))
(in-package :cl-mpm/tests/mc-composite-apex-failure-capture)

(defparameter *planned-groups*
  '("helper-preserves-condition-and-owns-json-tree"
    "synthetic-analytic-rejection-captures-named-checks"
    "optional-in-memory-and-json-replay"
    "strict-and-optional-replay-variant-firewall"
    "base-and-detailed-capture-failures-preserve-original-error"
    "native-rejection-preserves-complete-state-and-external-strain"
    "successful-return-does-not-build-diagnostic"
    "delegated-strict-condition-is-untouched"))
(defvar *passed* nil)
(defvar *failures* nil)
(defvar *helper-only-failures* 0)
(defvar *projector-calls* 0)
(defvar *native-calls* 0)
(defvar *optional-replay-attempts* 0)
(defvar *optional-replay-projector-calls* 0)
(defvar *inside-optional-replay* nil)
(defvar *strict-replay-attempts* 0)
(defvar *strict-delegate-calls* 0)
(defvar *mpm-attempts* 0)
(defvar *analytic-record* nil)
(defvar *native-record* nil)
(defconstant +e+ 1d8)
(defconstant +nu+ .3d0)
(defconstant +j+ 1.0123456789012345d0)
(defconstant +old-kappa+ .02d0)

(defmacro control (name &body body)
  `(handler-case
       (progn ,@body (push ,name *passed*) (format t "~&PASS: ~A~%" ,name))
     (error (condition)
       (push (list ,name (princ-to-string condition)) *failures*)
       (format t "~&FAIL: ~A: ~A~%" ,name condition))))

(defmacro with-function (name function &body body)
  (let ((saved (gensym "SAVED-FUNCTION")))
    `(let ((,saved (symbol-function ',name)))
       (unwind-protect
            (progn (setf (symbol-function ',name) ,function) ,@body)
         (setf (symbol-function ',name) ,saved)))))

(defmacro with-synthetic-rejection (&body body)
  ;; This is an injected rejection of an otherwise valid new fixture. It tests
  ;; capture wiring independently of the corrected roundoff arithmetic.
  `(with-function mc::admissible-candidate-p
       (lambda (candidate residual tolerance)
         (declare (ignore candidate residual tolerance)) nil)
     ,@body))

(defun object (&rest entries) (apply #'mc::%diagnostic-object entries))
(defun fixture-law ()
  (mc:make-evolution-law :variant :perfect
    :points '((0d0 30d0) (.1d0 31d0))
    :cohesion-points '((0d0 1d4) (.1d0 1.1d4))
    :peak-kappa .037d0 :psi 0d0 :stress-measure :cauchy
    :strain-assumption "Synthetic optional capture fixture; no actual lost-update evidence"))
(defun json-roundtrip (record)
  (with-input-from-string (stream (with-output-to-string (output) (yason:encode record output)))
    (yason:parse stream :object-as :hash-table :json-arrays-as-vectors t)))
(defun capture-material-error (thunk)
  (let* ((seen nil)
        (condition
          (handler-case
              (handler-bind ((mc:material-integration-error (lambda (value) (push value seen))))
                (funcall thunk)
                (error "Expected a material-integration-error."))
            (mc:material-integration-error (value) value))))
    (assert (= (length seen) 1))
    (assert (eq (first seen) condition))
    condition))
(defun helper-failure (reason trial law checks-thunk &rest details)
  (incf *helper-only-failures*)
  (capture-material-error
   (lambda () (apply #'ap::%composite-integration-fail
                    reason trial +e+ +nu+ +j+ law +old-kappa+ checks-thunk details))))
(defun optional-replay (record)
  (incf *optional-replay-attempts*)
  (let ((*inside-optional-replay* t)) (ap:replay-integration-diagnostic record)))
(defun must-error (thunk)
  (unless (handler-case (progn (funcall thunk) nil) (error () t))
    (error "Malformed or mismatched replay record was accepted.")))
(defun assert-identity (condition reason details)
  (assert (eq (class-name (class-of condition)) 'mc:material-integration-error))
  (assert (eq (mc:integration-error-reason condition) reason))
  (assert (equalp (mc:integration-error-details condition) details)))
(defun fingerprint (value &optional seen)
  (cond ((or (null value) (numberp value) (symbolp value) (characterp value)) value)
        ((stringp value) (copy-seq value))
        ((typep value 'magicl:matrix/double-float)
         (list :matrix (copy-list (magicl:shape value)) (coerce (cl-mpm/utils:fast-storage value) 'list)))
        ((consp value) (cons (fingerprint (car value) seen) (fingerprint (cdr value) seen)))
        ((arrayp value) (list :array (array-dimensions value)
                         (loop for i below (array-total-size value)
                               collect (fingerprint (row-major-aref value i) seen))))
        ((or (typep value 'structure-object) (typep value 'standard-object))
         (if (member value seen :test #'eq) :cycle
             (list (class-name (class-of value))
              (loop for slot in (sb-mop:class-slots (class-of value))
                    for name = (sb-mop:slot-definition-name slot)
                    collect (list name (if (slot-boundp value name)
                      (fingerprint (slot-value value name) (cons value seen)) :unbound))))))
        (t (error "Unhandled native fingerprint value ~S." (type-of value)))))
(defun mutable-json-objects (value)
  (cond ((stringp value) (list value))
        ((hash-table-p value)
         (let ((objects (list value)))
           (maphash (lambda (key item)
                      (setf objects (nconc objects (mutable-json-objects key) (mutable-json-objects item)))) value)
           objects))
        ((vectorp value) (cons value (loop for item across value append (mutable-json-objects item))))
        (t nil)))
(defun assert-no-shared-json-storage (left right)
  (assert (null (intersection (mutable-json-objects left) (mutable-json-objects right) :test #'eq))))
(defun strain-from-tau (tau)
  (let ((shear (/ +e+ (* 2d0 (+ 1d0 +nu+)))))
    (cl-mpm/utils:voigt-from-list
     (loop for i below 6 collect
       (if (< i 3)
           (/ (- (elt tau i) (* +nu+ (loop for k below 3 unless (= k i) sum (elt tau k)))) +e+)
           (/ (elt tau i) shear))))))
(defun native-call (particle strain)
  (incf *native-calls*)
  (cl-mpm/particle:constitutive-model particle strain 1d-4))

(defun run-controls ()
  (control "helper-preserves-condition-and-owns-json-tree"
    (let* ((reason (copy-seq "Synthetic helper capture rejection"))
           (trial (vector 5d4 4d4 3d4)) (law (fixture-law))
           (label (copy-seq "owned-label"))
           (values (vector 1d0 2d0 3d0))
           (checks (object "stage" label "values" values
                           "nonfiniteDerived"
                           (vector sb-ext:double-float-positive-infinity
                                   sb-ext:double-float-negative-infinity
                                   (sb-kernel:make-double-float #x7ff80000 0))))
           (details (list :fixture (vector 9d0 8d0)))
           (first (apply #'helper-failure reason trial law (lambda () checks) details))
           (second (apply #'helper-failure reason trial law (lambda () checks) details))
           (record (mc:integration-error-diagnostic first))
           (other (mc:integration-error-diagnostic second))
           (before (json-roundtrip record)))
      (assert-identity first reason details)
      (assert (equalp record before))
      (assert-no-shared-json-storage record other)
      (assert-no-shared-json-storage record checks)
      (assert (= (length (gethash "points" (gethash "law" record))) 2))
      (assert (= (gethash "deformationJacobian" record) +j+))
      (assert (= (gethash "oldKappa" record) +old-kappa+))
      (assert (equalp (gethash "nonfiniteDerived" (gethash "checks" record))
                      (vector (object "numberKind" "nonfinite" "value" "positive-infinity")
                              (object "numberKind" "nonfinite" "value" "negative-infinity")
                              (object "numberKind" "nonfinite" "value" "nan"))))
      (setf (aref trial 0) -999d0
            (second (first (mc:evolution-law-points law))) 10d0
            (second (first (mc:evolution-law-cohesion-points law))) 1d0
            (char (mc:evolution-law-strain-assumption law) 0) #\X
            (char reason 0) #\X (char label 0) #\X (aref values 0) 999d0)
      (assert (equalp record before))
      (assert (equalp other before))
      (let ((caller-before (fingerprint (list trial law reason label values))))
        (setf (aref (gethash "trialKirchhoffPa" record) 0) 123d0
              (aref (aref (gethash "points" (gethash "law" record)) 0) 1) 11d0
              (char (gethash "strainAssumption" (gethash "law" record)) 0) #\Y
              (char (gethash "schema" record) 0) #\Y
              (aref (gethash "values" (gethash "checks" record)) 0) 123d0)
        (assert (equalp caller-before (fingerprint (list trial law reason label values))))
        (assert (equalp other before)))))

  (control "synthetic-analytic-rejection-captures-named-checks"
    (let* ((trial (vector 5d4 4d4 3d4)) (law (fixture-law))
           (before (fingerprint (list trial law)))
           (condition (with-synthetic-rejection
                        (capture-material-error
                         (lambda () (ap:project-principal-with-apex trial +e+ +nu+ +j+ law +old-kappa+)))))
           (record (mc:integration-error-diagnostic condition))
           (checks (gethash "checks" record)) (metrics (gethash "checks" checks)))
      (assert (equalp before (fingerprint (list trial law))))
      (assert (equal (mc:integration-error-reason condition)
                     "Composite apex compliance, flow, yield or work identity failed"))
      (assert (null (mc:integration-error-details condition)))
      (assert (equal (gethash "schema" record) "cl-mpm.mc-composite-apex.principal-failure"))
      (assert (equal (gethash "materialVariant" record) "perfect-mc-composite-apex"))
      (assert (equal (gethash "stage" checks) "identity-validation"))
      (assert (= (length metrics) 8))
      (assert (equalp (map 'vector (lambda (metric) (gethash "name" metric)) metrics)
                      #("admissible-candidate" "minimum-multiplier" "shear-flow-error-pa"
                        "compliance-error-pa" "plastic-volume-error-pa" "work-identity-error-pa"
                        "finite-energy" "energy-margin-pa")))
      (assert (equal (gethash "outcome" (aref metrics 0)) "FAIL"))
      (dolist (index '(2 3 4))
        (assert (= (gethash "limit" (aref metrics index)) (gethash "stressTolerancePa" checks))))
      (assert (= (gethash "limit" (aref metrics 5)) (gethash "workTolerancePa" checks)))
      (assert (= (gethash "limit" (aref metrics 7)) (- (gethash "workTolerancePa" checks))))
      (assert (equalp record (json-roundtrip record)))
      (setf *analytic-record* record)))

  (control "optional-in-memory-and-json-replay"
    (assert *analytic-record*)
    (dolist (record (list *analytic-record* (json-roundtrip *analytic-record*)))
      (let ((condition (with-synthetic-rejection
                         (capture-material-error (lambda () (optional-replay record))))))
        (assert (equalp record (mc:integration-error-diagnostic condition)))
        (assert (equal (gethash "reason" record) (mc:integration-error-reason condition))))))

  (control "strict-and-optional-replay-variant-firewall"
    (assert *analytic-record*)
    (let ((before *projector-calls*) (original (json-roundtrip *analytic-record*))
          (forbidden-strict-calls 0))
      (with-function mc:project-principal
          (lambda (&rest arguments) (declare (ignore arguments))
            (incf forbidden-strict-calls) (error "Optional capsule reached the strict projector."))
        (incf *strict-replay-attempts*)
        (must-error (lambda () (mc:replay-integration-diagnostic *analytic-record*))))
      (assert (zerop forbidden-strict-calls))
      (dolist (edit (list
                    (lambda (record) (setf (gethash "schema" record) "cl-mpm.mc-evolution.principal-failure"))
                    (lambda (record) (setf (gethash "schema" record) "cl-mpm.wang2017.native-failure"))
                    (lambda (record) (setf (gethash "schemaVersion" record) 2))
                    (lambda (record) (remhash "materialVariant" record))
                    (lambda (record) (setf (gethash "materialVariant" record) "composite-apex"))
                    (lambda (record) (remhash "deformationJacobian" record))
                    (lambda (record) (setf (gethash "variant" (gethash "law" record)) "unknown"))))
        (let ((record (json-roundtrip *analytic-record*)))
          (funcall edit record)
          (must-error (lambda () (optional-replay record)))))
      (assert (= before *projector-calls*))
      (assert (equalp original *analytic-record*))))

  (control "base-and-detailed-capture-failures-preserve-original-error"
    (let* ((reason (copy-seq "Original helper failure remains authoritative"))
           (trial (vector 5d4 4d4 3d4)) (law (fixture-law)) (details (list :retained 17))
           (checks-calls 0)
           (invalid (apply #'helper-failure reason trial nil
                           (lambda () (incf checks-calls) (object)) details)))
      (assert-identity invalid reason details)
      (assert (null (mc:integration-error-diagnostic invalid)))
      (assert (zerop checks-calls))
      (let ((builder-calls 0))
        (with-function ap::%composite-failure-diagnostic
            (lambda (&rest arguments)
              (declare (ignore arguments)) (incf builder-calls)
              (error 'mc:material-integration-error :reason "Injected base capture failure"))
          (let ((condition (apply #'helper-failure reason trial law
                                  (lambda () (incf checks-calls) (object)) details)))
            (assert-identity condition reason details)
            (assert (null (mc:integration-error-diagnostic condition)))))
        (assert (= builder-calls 1)) (assert (zerop checks-calls)))
      (dolist (thunk (list (lambda () (error 'mc:material-integration-error :reason "Injected checks failure"))
                          (lambda () (object "unsupportedValue" #'identity))))
        (let* ((condition (apply #'helper-failure reason trial law thunk details))
               (record (mc:integration-error-diagnostic condition)))
          (assert-identity condition reason details)
          (assert (hash-table-p record))
          (assert (stringp (gethash "checksCaptureError" record)))
          (assert (not (nth-value 1 (gethash "checks" record))))
          (assert (equalp (gethash "trialKirchhoffPa" record) trial))
          (assert (equalp record (json-roundtrip record)))))))

  (control "native-rejection-preserves-complete-state-and-external-strain"
    (let* ((particle (make-instance 'ap:particle-mc-composite-apex
                      :E +e+ :nu +nu+ :evolution-law (fixture-law) :enable-plasticity t))
           (f (cl-mpm/particle:mp-deformation-gradient particle)))
      (dotimes (i 3) (dotimes (k 3) (setf (magicl:tref f i k) (if (= i k) 1d0 0d0))))
      (setf (magicl:tref f 0 0) +j+)
      (native-call particle (strain-from-tau #(5d4 4d4 3d4 0d0 0d0 0d0)))
      (cl-mpm/particle::new-loadstep-mp particle)
      (assert (ap:particle-last-apex-active particle))
      (let* ((before (fingerprint particle))
             (strain (strain-from-tau #(7d4 6d4 4d4 0d0 0d0 0d0)))
             (strain-before (fingerprint strain))
             (condition (with-synthetic-rejection
                          (capture-material-error (lambda () (native-call particle strain)))))
             (record (mc:integration-error-diagnostic condition)))
        (assert (equalp before (fingerprint particle)))
        (assert (equalp strain-before (fingerprint strain)))
        (assert (= (gethash "deformationJacobian" record)
                   (cl-mpm/fastmaths:det-3x3 (cl-mpm/particle:mp-deformation-gradient particle))))
        (assert (= (gethash "oldKappa" record) (mc:particle-kappa-committed particle)))
        (setf *native-record* (json-roundtrip record))
        (setf (aref (gethash "trialKirchhoffPa" record) 0) -99d0
              (aref (gethash "deviator" (gethash "checks" record)) 0) -99d0
              (char (gethash "strainAssumption" (gethash "law" record)) 0) #\X)
        (assert (equalp before (fingerprint particle)))
        (assert (equalp strain-before (fingerprint strain))))))

  (control "successful-return-does-not-build-diagnostic"
    (let ((capture-calls 0) (trial (vector 5d4 4d4 3d4)) (law (fixture-law)))
      (let ((before (fingerprint (list trial law))))
        (with-function ap::%composite-failure-diagnostic
            (lambda (&rest arguments) (declare (ignore arguments))
              (incf capture-calls) (error "Successful return attempted diagnostic capture."))
          (assert (typep (ap:project-principal-with-apex trial +e+ +nu+ +j+ law +old-kappa+)
                         'ap:apex-projection)))
        (assert (zerop capture-calls))
        (assert (equalp before (fingerprint (list trial law)))))))

  (control "delegated-strict-condition-is-untouched"
    (let* ((reason (copy-seq "Synthetic strict delegate condition"))
           (details (list :sentinel (vector 1d0)))
           (diagnostic (object "schema" "strict-delegate-sentinel"))
           (condition (make-condition 'mc:material-integration-error
                        :reason reason :details details :diagnostic diagnostic))
           (capture-calls 0))
      (with-function ap::%composite-failure-diagnostic
          (lambda (&rest arguments) (declare (ignore arguments))
            (incf capture-calls) (error "Strict delegation attempted optional capture."))
        (with-function mc:project-principal
            (lambda (&rest arguments) (declare (ignore arguments))
              (incf *strict-delegate-calls*) (error condition))
          (let ((caught (capture-material-error
                         (lambda () (ap:project-principal-with-apex
                                     #(-1d3 -2d3 -3d3) +e+ +nu+ +j+ (fixture-law) +old-kappa+)))))
            (assert (eq caught condition))
            (assert (eq (mc:integration-error-diagnostic caught) diagnostic))
            (assert (eq (mc:integration-error-details caught) details))
            (assert (eq (mc:integration-error-reason caught) reason)))))
      (assert (zerop capture-calls)))))

(let ((original (symbol-function 'ap:project-principal-with-apex)))
  (with-function cl-mpm:update-sim
      (lambda (&rest arguments) (declare (ignore arguments))
        (incf *mpm-attempts*) (error "Capture controls forbid MPM updates."))
    (with-function ap:project-principal-with-apex
        (lambda (&rest arguments)
          (incf *projector-calls*)
          (when *inside-optional-replay* (incf *optional-replay-projector-calls*))
          (apply original arguments))
      (run-controls))))

(unless (and (equal (reverse *passed*) *planned-groups*)
             (= *helper-only-failures* 6) (= *projector-calls* 7) (= *native-calls* 2)
             (= *optional-replay-attempts* 9) (= *optional-replay-projector-calls* 2)
             (= *strict-replay-attempts* 1) (= *strict-delegate-calls* 1) (zerop *mpm-attempts*))
  (push (list "exact-planned-groups-and-call-counts" "Execution differed from the eight new groups and declared counts.")
        *failures*))
(let ((report (object
               "passed" (if *failures* 'yason:false t)
               "plannedGroups" (coerce *planned-groups* 'vector)
               "passedGroups" (coerce (reverse *passed*) 'vector)
               "failedGroups" (coerce (reverse *failures*) 'vector)
               "explicitHelperOnlyFailures" *helper-only-failures*
               "optionalProjectorCalls" *projector-calls* "nativeConstitutiveCalls" *native-calls*
               "optionalReplayAttempts" *optional-replay-attempts*
               "optionalReplayProjectorCalls" *optional-replay-projector-calls*
               "strictReplaySchemaRejectionAttempts" *strict-replay-attempts*
               "syntheticStrictDelegateCalls" *strict-delegate-calls*
               "physicalUpdateAttempts" *mpm-attempts* "originalFineFailureReplayCalls" 0
               "syntheticAnalyticFailure" *analytic-record* "syntheticNativeFailure" *native-record*
               "nativeBackend" (cl-user::snapshot-native-proof)
               "scope" "Eight NEW optional failure-capture controls; synthetic injected admissibility rejections and owned native state; no actual lost fine-update replay, old suite, MPM update, landslide or scientific validation")))
  (with-open-file (stream (merge-pathnames "result.json" cl-user::*capture-directory*)
                          :direction :output :if-exists :error :external-format :utf-8)
    (yason:encode report stream)))
(setf cl-user::*capture-exit* (if *failures* 1 0))
(format t "~&COMPOSITE CAPTURE: ~D/~D new groups; ~D helper failures, ~D optional calls, ~D native calls, ~D replay attempts; ~D MPM updates.~%"
        (length *passed*) (length *planned-groups*) *helper-only-failures* *projector-calls*
        *native-calls* *optional-replay-attempts* *mpm-attempts*)
