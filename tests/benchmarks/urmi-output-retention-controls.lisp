;;;; FIRST NEW pure Windows SBCL file/error controls. No material or MPM load.
;;;; windows/cl-mpm.cmd tests/benchmarks/urmi-output-retention-controls.lisp FRESH_OUTPUT
(in-package :cl-user)
(require :asdf)
(defvar *retention-frozen* nil)
(defvar *retention-directory* nil)
(defvar *retention-exit* 1)
(unless *retention-frozen*
  (load (cl-mpm-path "scripts/lisp/native-source-snapshot.lisp"))
  (snapshot-require-fresh-runtime)
  (let* ((arguments (cl-mpm-script-args))
         (directory (and (first arguments)
                         (uiop:ensure-directory-pathname (merge-pathnames (first arguments))))))
    (unless (and directory (= (length arguments) 1)) (error "Provide one fresh output directory."))
    (when (and (probe-file directory) (or (uiop:directory-files directory) (uiop:subdirectories directory)))
      (error "Preserve previous output-retention evidence."))
    (let ((copied nil) (records nil))
      (dolist (relative '("tests/benchmarks/urmi-output-retention-controls.lisp"
                          "scenarios/urmi-damage40/output-streams.lisp"
                          "scenarios/urmi-damage40/runner.lisp" "cl-mpm-framework.asd"
                          "scripts/lisp/native-source-snapshot.lisp" "windows/init.lisp" "windows/env.cmd"))
        (let* ((from (cl-mpm-path relative)) (to (merge-pathnames (concatenate 'string "source/" relative) directory))
               (bytes (case-source-bytes from)))
          (ensure-directories-exist to) (uiop:copy-file from to)
          (assert (equalp bytes (case-source-bytes to)))
          (push to copied)
          (push (snapshot-object "path" (enough-namestring to directory) "originalPath" (namestring (truename from))
                                 "bytes" (length bytes) "sha256" (snapshot-sha256-bytes bytes)) records)))
      (snapshot-write-json (merge-pathnames "source/source-manifest.json" directory)
        (snapshot-object "scope" "Only selected output-retention/runner integration/bootstrap sources; no engine/material/native DLL loading"
                         "files" (coerce (reverse records) 'vector)))
      (let ((*native-snapshot-context* (snapshot-register-native directory records))
            (*retention-frozen* t) (*retention-directory* directory))
        (flet ((proof (name)
                 (snapshot-write-json (merge-pathnames name directory)
                   (snapshot-object "files" (coerce (mapcar (lambda (path)
                     (snapshot-object "path" (enough-namestring path directory) "sha256" (snapshot-sha256 path))) copied) 'vector)))))
          (proof "source-proof-before.json")
          (snapshot-check-plan "cl-mpm-framework/urmi-output-streams")
          (asdf:load-system "cl-mpm-framework/urmi-output-streams")
          (dolist (name '("CL-MPM" "CL-MPM/PARTICLE" "CL-MPM/FRAMEWORK"))
            (assert (null (find-package name))))
          (assert (null (snapshot-module-path "kirchoff.dll")))
          (snapshot-verify-file (merge-pathnames "source/tests/benchmarks/urmi-output-retention-controls.lisp" directory))
          (load (merge-pathnames "source/tests/benchmarks/urmi-output-retention-controls.lisp" directory))
          (dolist (path copied) (snapshot-verify-file path))
          (proof "source-proof-after.json")
          (snapshot-write-json (merge-pathnames "runtime-provenance.json" directory)
            (snapshot-object "lispImplementation" (lisp-implementation-type) "lispVersion" (lisp-implementation-version)
              "machineType" (machine-type) "windowsFeaturePresent" (if (member :win32 *features*) t :false)
              "verifiedAsdfActions" (coerce (reverse (getf *native-snapshot-context* :actions)) 'vector)
              "loadedOwnedSystem" "cl-mpm-framework/urmi-output-streams"
              "kirchoffDllMapped" (if (snapshot-module-path "kirchoff.dll") t :false)
              "materialCalls" 0 "mpmUpdates" 0
              "scope" "Actual Windows SBCL file behavior and one independent output macro system only; no physics/MPM or restart validation"))))))
  (uiop:quit *retention-exit*))

(defpackage :cl-mpm/tests/urmi-output-retention
  (:use :cl)
  (:local-nicknames (:owned :cl-mpm/scenario/urmi-damage40/output-streams)))
(in-package :cl-mpm/tests/urmi-output-retention)
(defvar *passed* nil) (defvar *failures* nil)
(defvar *observations* (make-hash-table :test #'equal))
(define-condition fixture-error (error) ((tag :initarg :tag :reader fixture-tag)))
(defun fresh (name) (merge-pathnames (concatenate 'string "fixtures/" name) cl-user::*retention-directory*))
(defun bytes (path) (cl-user::case-source-bytes path))
(defun same-bytes (path expected) (assert (probe-file path)) (assert (equalp (bytes path) expected)))
(defun note-file (key path)
  (setf (gethash key *observations*)
        (cl-user::snapshot-object "path" (enough-namestring path cl-user::*retention-directory*)
          "bytes" (length (bytes path)) "sha256" (cl-user::snapshot-sha256 path))))
(defmacro control (name &body body)
  `(handler-case
       (progn ,@body (push ,name *passed*) (format t "~&PASS: ~A~%" ,name) (finish-output))
     (error (condition)
       (push (list ,name (princ-to-string condition)) *failures*)
       (format t "~&FAIL: ~A: ~A~%" ,name condition) (finish-output))))

(ensure-directories-exist (fresh "fixture-placeholder"))
(control "actual-legacy-abort-deletion-versus-owned-flushed-byte-retention"
  (let* ((legacy (fresh "legacy-abort.csv")) (retained (fresh "retained-error.csv"))
         (original (make-condition 'fixture-error :tag :primary)) (caught nil) (expected nil) (opened nil))
    ;; No explicit deletion is performed. The observed removal below, if any,
    ;; is native WITH-OPEN-FILE's own abort-close behavior on its fresh fixture.
    (handler-case
        (with-open-file (stream legacy :direction :output :if-exists :error)
          (write-string "frame,value" stream) (terpri stream)
          (write-string "0,1" stream) (terpri stream) (finish-output stream)
          (assert (probe-file legacy)) (error original))
      (fixture-error (condition) (setf caught condition)))
    (assert (eq caught original))
    (assert (not (probe-file legacy)))
    (setf caught nil)
    (handler-case
        (owned:with-retained-output-file (stream retained)
          (setf opened stream)
          (write-string "frame,value" stream) (terpri stream)
          (write-string "0,1" stream) (terpri stream) (finish-output stream)
          (setf expected (bytes retained)) (error original))
      (fixture-error (condition) (setf caught condition)))
    (assert (eq caught original)) (assert (not (open-stream-p opened)))
    (same-bytes retained expected)
    (setf (gethash "legacyAbortRemovedItsFreshFixture" *observations*) t)
    (note-file "ownedErrorRetainedExactPreviouslyFlushedBytes" retained)))

(control "nested-three-output-streams-retain-bytes-and-original-error"
  (let ((paths (mapcar #'fresh '("nested-state.csv" "nested-particles.csv" "nested-history.csv")))
        (original (make-condition 'fixture-error :tag :nested)) (caught nil) (opened nil) (expected nil))
    (handler-case
        (owned:with-retained-output-file (a (first paths))
          (owned:with-retained-output-file (b (second paths))
            (owned:with-retained-output-file (c (third paths))
              (setf opened (list a b c))
              (loop for stream in opened for index from 0 do
                (format stream "header~%~D,actual~%" index) (finish-output stream))
              (setf expected (mapcar #'bytes paths)) (error original))))
      (fixture-error (condition) (setf caught condition)))
    (assert (eq caught original)) (assert (every (lambda (stream) (not (open-stream-p stream))) opened))
    (mapc #'same-bytes paths expected)
    (loop for path in paths for index from 0 do (note-file (format nil "nestedRetained~D" index) path))))

(control "nonlocal-multiple-value-return-retains-output"
  (let ((path (fresh "nonlocal-return.csv")) (expected nil) (opened nil))
    (assert (equal (multiple-value-list
      (catch 'exit-now
        (owned:with-retained-output-file (stream path)
          (setf opened stream) (write-string "actual nonlocal output" stream) (finish-output stream)
          (setf expected (bytes path)) (throw 'exit-now (values 7 :retained))))) '(7 :retained)))
    (assert (not (open-stream-p opened))) (same-bytes path expected) (note-file "nonlocalRetained" path)))

(control "normal-close-flushes-buffer-and-preserves-multiple-values"
  (let ((path (fresh "normal-close.csv")) (opened nil))
    (assert (equal (multiple-value-list
      (owned:with-retained-output-file (stream path)
        (setf opened stream) (write-string "normal,actual" stream) (values 3 :closed))) '(3 :closed)))
    (assert (not (open-stream-p opened)))
    (same-bytes path (map '(vector (unsigned-byte 8)) #'char-code "normal,actual"))
    (note-file "normalCloseRetained" path)))

(control "existing-output-file-is-rejected-without-overwrite-or-body-entry"
  (let ((path (fresh "existing-output.csv")) (entered nil) (caught nil) (expected nil))
    (owned:with-retained-output-file (stream path) (write-string "original,unchanged" stream))
    (setf expected (bytes path))
    (handler-case
        (owned:with-retained-output-file (stream path)
          (setf entered t) (write-string "replacement must never happen" stream))
      (file-error (condition) (setf caught condition)))
    (assert caught) (assert (not entered)) (same-bytes path expected) (note-file "existingFileUntouched" path)))

(control "synthetic-cleanup-error-is-reported-without-replacing-primary-exit"
  (let* ((primary (make-condition 'fixture-error :tag :original))
         (secondary (make-condition 'fixture-error :tag :synthetic-close))
         (captured nil) (diagnostics (make-string-output-stream))
         (*error-output* diagnostics))
    (flet ((broken-close (stream &key abort)
             (assert (eq stream :synthetic-stream)) (assert (null abort)) (error secondary)))
      (handler-case
          (unwind-protect (error primary)
            (owned::%close-retained-output :synthetic-stream nil #'broken-close))
        (fixture-error (condition) (setf captured condition)))
      (assert (eq captured primary))
      (assert (search "Owned Urmi output CLOSE failed" (get-output-stream-string diagnostics)))
      (assert (eq (catch 'keep-nonlocal
                    (unwind-protect (throw 'keep-nonlocal :original-nonlocal)
                      (owned::%close-retained-output :synthetic-stream nil #'broken-close))) :original-nonlocal))
      (assert (search "Owned Urmi output CLOSE failed" (get-output-stream-string diagnostics)))
      (setf captured nil)
      (handler-case (owned::%close-retained-output :synthetic-stream t #'broken-close)
        (fixture-error (condition) (setf captured condition)))
      (assert (eq captured secondary)))
    (setf (gethash "cleanupFailureControlScope" *observations*)
          "Synthetic internal close-function injection only; no actual OS/disk close failure claimed")))

;; This is only a source integration check, not an executed MPM/runner test.
(let* ((runner (uiop:read-file-string
                (merge-pathnames "source/scenarios/urmi-damage40/runner.lisp" cl-user::*retention-directory*)))
       (needle "cl-mpm/scenario/urmi-damage40/output-streams:with-retained-output-file")
       (count (loop for position = (search needle runner) then (search needle runner :start2 (+ position (length needle)))
                    while position count t)))
  (assert (= count 5)) (assert (null (search "(with-open-file " runner)))
  (setf (gethash "runnerFiveStreamWrappers" *observations*) count
        (gethash "runnerIntegrationScope" *observations*) "Static source occurrence only; runner/MPM NOT_EXECUTED"))
(dolist (name '("CL-MPM" "CL-MPM/PARTICLE" "CL-MPM/FRAMEWORK")) (assert (null (find-package name))))
(assert (null (cl-user::snapshot-module-path "kirchoff.dll")))
(unless *failures* (assert (= (length *passed*) 6)))
(cl-user::snapshot-write-json (merge-pathnames "result.json" cl-user::*retention-directory*)
  (cl-user::snapshot-object "passed" (if *failures* :false t) "passedGroups" (coerce (reverse *passed*) 'vector)
    "failures" (coerce (reverse *failures*) 'vector) "materialCalls" 0 "mpmUpdates" 0
    "observations" *observations*
    "scope" "FIRST pure SBCL file/error controls, no engine/material/DLL/MPM. No missing old CSV/state reconstruction or restart guarantee."))
(setf cl-user::*retention-exit* (if *failures* 1 0))
