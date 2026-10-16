;;;; Windows CLI source provenance. No constitutive or solver implementation.
(in-package :cl-user)
(require :asdf)
#-win32
(error "Native source snapshot/module provenance currently requires Windows; no snapshot claim was made.")

(defparameter *native-snapshot-helper-source* *load-truename*)
(defvar *native-snapshot-context* nil)

#+win32 (cffi:define-foreign-library snapshot-kernel32 (t (:default "kernel32")))
#+win32 (cffi:define-foreign-library snapshot-bcrypt (t (:default "bcrypt")))
#+win32 (cffi:use-foreign-library snapshot-kernel32)
#+win32 (cffi:use-foreign-library snapshot-bcrypt)

(defun case-source-bytes (path)
  (with-open-file (stream path :element-type '(unsigned-byte 8))
    (let ((bytes (make-array (file-length stream) :element-type '(unsigned-byte 8))))
      (unless (= (read-sequence bytes stream) (length bytes))
        (error "Short source read: ~A" path))
      bytes)))

(defun snapshot-sha256-bytes (bytes)
  "Windows CNG SHA-256; hash the actual octets, including line endings."
  (cffi:with-foreign-object (provider :pointer)
    (cffi:with-foreign-string (algorithm "SHA256" :encoding :utf-16le)
      (unless (zerop (cffi:foreign-funcall ("BCryptOpenAlgorithmProvider" :library snapshot-bcrypt :convention :stdcall)
                       :pointer provider :pointer algorithm :pointer (cffi:null-pointer)
                       :uint32 0 :int32))
        (error "Cannot open Windows SHA-256 provider.")))
    (let ((handle (cffi:mem-ref provider :pointer)))
      (unwind-protect
           (cffi:with-foreign-object (digest :uint8 32)
             (cffi:with-pointer-to-vector-data (input bytes)
               (unless (zerop (cffi:foreign-funcall ("BCryptHash" :library snapshot-bcrypt :convention :stdcall)
                                :pointer handle :pointer (cffi:null-pointer) :uint32 0
                                :pointer input :uint32 (length bytes)
                                :pointer digest :uint32 32 :int32))
                 (error "Windows SHA-256 failed.")))
             (string-downcase
              (format nil "~{~2,'0X~}" (loop for i below 32 collect (cffi:mem-aref digest :uint8 i)))))
        (cffi:foreign-funcall ("BCryptCloseAlgorithmProvider" :library snapshot-bcrypt :convention :stdcall)
          :pointer handle :uint32 0 :int32)))))

(defun snapshot-sha256 (path) (snapshot-sha256-bytes (case-source-bytes path)))

(defun snapshot-object (&rest pairs)
  (let ((object (make-hash-table :test #'equal)))
    (loop for (key value) on pairs by #'cddr do (setf (gethash key object) value))
    object))

(defun snapshot-json (value stream)
  "Small bootstrap writer: JSON is needed before loading any project system."
  (labels ((string-value (value)
             (write-char #\" stream)
             (loop for character across value do
               (case character
                 (#\" (write-string "\\\"" stream)) (#\\ (write-string "\\\\" stream))
                 (#\Newline (write-string "\\n" stream)) (#\Return (write-string "\\r" stream))
                 (#\Tab (write-string "\\t" stream))
                 (otherwise (if (< (char-code character) 32)
                                (format stream "\\u~4,'0X" (char-code character))
                                (write-char character stream)))))
             (write-char #\" stream))
           (array-value (values)
             (write-char #\[ stream)
             (loop for value in values for first = t then nil do
               (unless first (write-char #\, stream)) (snapshot-json value stream))
             (write-char #\] stream)))
    (typecase value
      (null (write-string "null" stream))
      (string (string-value value))
      (hash-table
       (write-char #\{ stream)
       (loop for key being the hash-keys of value using (hash-value item)
             for first = t then nil do
         (unless first (write-char #\, stream)) (string-value key)
         (write-char #\: stream) (snapshot-json item stream))
       (write-char #\} stream))
      (vector (array-value (coerce value 'list)))
      (list (array-value value))
      (integer (format stream "~D" value))
      (t (cond ((eq value t) (write-string "true" stream))
               ((eq value :false) (write-string "false" stream))
               (t (error "Unsupported bootstrap JSON value ~S" value)))))))

(defun snapshot-write-json (path value)
  (with-open-file (stream path :direction :output :if-exists :error
                              :if-does-not-exist :create :external-format :utf-8)
    (snapshot-json value stream) (terpri stream)))

(defun snapshot-path-key (path)
  (string-downcase (substitute #\/ #\\ (namestring (truename path)))))

(defun snapshot-same-path-p (left right)
  (string= (snapshot-path-key left) (snapshot-path-key right)))

(defun snapshot-module-path (name)
  "Ask Windows for the module actually mapped in this process, not a CFFI hint."
  (cffi:with-foreign-string (module-name name :encoding :utf-16le)
    (let ((handle (cffi:foreign-funcall ("GetModuleHandleW" :library snapshot-kernel32 :convention :stdcall)
                    :pointer module-name :pointer)))
      (unless (cffi:null-pointer-p handle)
        (cffi:with-foreign-object (buffer :uint16 32768)
          (let ((count (cffi:foreign-funcall ("GetModuleFileNameW" :library snapshot-kernel32 :convention :stdcall)
                         :pointer handle :pointer buffer :uint32 32768 :uint32)))
            (unless (< 0 count 32768) (error "Cannot resolve loaded module ~S." name))
            (truename (cffi:foreign-string-to-lisp buffer :encoding :utf-16le :count (* 2 count)))))))))

(defun snapshot-require-fresh-runtime ()
  (dolist (name '("CL-MPM" "CL-MPM/PARTICLE" "CL-MPM/CONSTITUTIVE" "CL-MPM/SETTINGS" "CL-MPM/FRAMEWORK"))
    (when (find-package name)
      (error "Native snapshot needs a fresh process; project package already exists: ~A" name)))
  (when (snapshot-module-path "kirchoff.dll")
    (error "Native snapshot needs a fresh process; kirchoff.dll is already loaded.")))

(defun snapshot-case-sources (directory case-file)
  "Copy the complete first-party source payload; return paths and SHA-256 records."
  (let ((copied nil) (records nil))
    (labels ((copy-one (from to)
               (let ((before (case-source-bytes from)))
                 (ensure-directories-exist to) (uiop:copy-file from to)
                 (unless (equalp before (case-source-bytes to))
                   (error "Source copy is not byte-identical: ~A" from))
                 (push to copied)
                 (push (snapshot-object "path" (enough-namestring to directory)
                                        "originalPath" (namestring (truename from))
                                        "bytes" (length before) "sha256" (snapshot-sha256-bytes before)) records)))
             (copy-tree-sources (from to)
               (when (probe-file from)
                 (dolist (path (uiop:directory-files from))
                   (when (member (pathname-type path) '("lisp" "asd") :test #'string-equal)
                     (copy-one path (merge-pathnames (file-namestring path) to))))
                 (dolist (path (uiop:subdirectories from))
                   (copy-tree-sources path (merge-pathnames
                                           (make-pathname :directory (list :relative (car (last (pathname-directory path))))) to))))))
      (dolist (relative '("src/" "materials/" "framework/" "scenarios/"))
        (copy-tree-sources (cl-mpm-path relative) (merge-pathnames (concatenate 'string "source/" relative) directory)))
      (dolist (relative '("cl-mpm.asd" "config/git-commit-version.txt" "libs/kirchoff.dll"))
        (copy-one (cl-mpm-path relative) (merge-pathnames (concatenate 'string "source/" relative) directory)))
      (dolist (relative '("cl-mpm-simulation.asd" "cl-mpm-materials.asd"))
        (when (probe-file (cl-mpm-path relative))
          (copy-one (cl-mpm-path relative) (merge-pathnames (concatenate 'string "source/" relative) directory))))
      (copy-one case-file (merge-pathnames "source/case.lisp" directory))
      (copy-one (cl-mpm-path "scripts/run-case.lisp") (merge-pathnames "source/run-case.lisp" directory))
      (copy-one *native-snapshot-helper-source* (merge-pathnames "source/scripts/lisp/native-source-snapshot.lisp" directory))
      (dolist (relative '("windows/init.lisp" "windows/env.cmd" "windows/cl-mpm.cmd"))
        (copy-one (cl-mpm-path relative) (merge-pathnames (concatenate 'string "source/bootstrap/" relative) directory)))
      (copy-one (cl-mpm-path "studio/schema.json") (merge-pathnames "source/inputs/studio/schema.json" directory))
      (dolist (relative '("calibration/" "studio/reference/"))
        (dolist (path (directory (merge-pathnames "*.json" (cl-mpm-path relative))))
          (copy-one path (merge-pathnames (concatenate 'string "source/inputs/" relative (file-namestring path)) directory)))))
    (values (nreverse copied) (nreverse records))))

(defun snapshot-first-party-system-p (system)
  (let ((source (asdf:system-source-file system)))
    (and source
         (or (and *native-snapshot-context*
                  (uiop:subpathp (truename source) (getf *native-snapshot-context* :source)))
             (and (uiop:subpathp (truename source) (truename (cl-mpm-path "")))
                  (not (uiop:subpathp source (cl-mpm-path "deps/")))
                  (not (uiop:subpathp source (cl-mpm-path "toolchain/"))))))))

(defun snapshot-verify-file (path)
  (let* ((context *native-snapshot-context*) (actual (truename path))
         (row (gethash (snapshot-path-key actual) (getf context :index))))
    (unless (uiop:subpathp actual (getf context :source))
      (error "ASDF component escapes frozen source: ~A" actual))
    (unless row (error "Selected source is absent from pre-load manifest: ~A" actual))
    (unless (string= (gethash "sha256" row) (snapshot-sha256 actual))
      (error "Frozen source changed after copy: ~A" actual))
    actual))

(defun snapshot-check-component (component operation &optional (event "planned"))
  (when (and *native-snapshot-context* (typep component 'asdf:cl-source-file))
    (let* ((system (asdf:component-system component))
           (first-party (snapshot-first-party-system-p system))
           (source (if first-party (snapshot-verify-file (asdf:component-pathname component))
                       (truename (asdf:component-pathname component))))
           (outputs (when (typep operation 'asdf:compile-op) (asdf:output-files operation component)))
           (inputs (when (typep operation 'asdf:load-op) (asdf:input-files operation component))))
      (when first-party
        (snapshot-verify-file (asdf:system-source-file system))
        (dolist (output outputs)
          (unless (uiop:subpathp output (getf *native-snapshot-context* :cache))
            (error "First-party FASL escapes private cache: ~A" output)))
        (dolist (input inputs)
          (unless (uiop:subpathp input (getf *native-snapshot-context* :cache))
            (error "First-party load input escapes private cache: ~A" input))))
      (push (snapshot-object "system" (asdf:component-name system)
                             "event" event
                             "operation" (string-downcase (symbol-name (class-name (class-of operation))))
                             "source" (namestring source) "firstParty" (if first-party t :false)
                             "outputs" (coerce (mapcar #'namestring outputs) 'vector)
                             "loadInputs" (coerce (loop for input in inputs collect
                                                   (snapshot-object "path" (namestring input)
                                                                    "sha256" (when (and (string= event "performing")
                                                                                         (probe-file input))
                                                                               (snapshot-sha256 input)))) 'vector))
            (getf *native-snapshot-context* :actions)))))

(defun snapshot-check-plan (system)
  (dolist (action (asdf/plan:plan-actions (asdf:make-plan 'asdf:sequential-plan 'asdf:load-op system)))
    (snapshot-check-component (asdf/action:action-component action) (asdf/action:action-operation action))))

(defun snapshot-preload-native-dll ()
  (unless (getf *native-snapshot-context* :dll-preloaded)
    (let ((dll (snapshot-verify-file (merge-pathnames "libs/kirchoff.dll" (getf *native-snapshot-context* :source)))))
      (when (snapshot-module-path "kirchoff.dll")
        (error "kirchoff.dll was loaded before the selected native bridge."))
      (cffi:load-foreign-library (uiop:native-namestring dll))
      (let ((actual (snapshot-module-path "kirchoff.dll")))
        (unless (and actual (snapshot-same-path-p actual dll))
          (error "Windows loaded a different kirchoff module: ~A" actual)))
      (setf (getf *native-snapshot-context* :dll-preloaded) t))))

;; Active only inside this CLI's dynamically bound context. ASDF operate and
;; its existing system-connection hooks still perform the actual loads.
(defmethod asdf:perform :before ((operation asdf:compile-op) (component asdf:cl-source-file))
  (snapshot-check-component component operation "performing"))
(defmethod asdf:perform :before ((operation asdf:load-op) (component asdf:cl-source-file))
  (snapshot-check-component component operation "performing")
  (when (and *native-snapshot-context*
             (string= (asdf:component-name (asdf:component-system component)) "cl-mpm/ext"))
    (snapshot-preload-native-dll)))

(defun snapshot-register-native (directory records)
  (let* ((source (truename (merge-pathnames "source/" directory)))
         (cache (merge-pathnames "native-cache/" directory))
         (index (make-hash-table :test #'equal)))
    (dolist (row records)
      (setf (gethash (snapshot-path-key (merge-pathnames (gethash "path" row) directory)) index) row))
    (dolist (name (copy-list (asdf:registered-systems)))
      (let ((system (asdf:find-system name nil)))
        (when (and system (snapshot-first-party-system-p system))
          (when (asdf:component-loaded-p system) (error "First-party system already loaded: ~A" name))
          (asdf:clear-system name))))
    (setf asdf:*central-registry*
          (append (list source (merge-pathnames "framework/" source))
                  (remove-if (lambda (path)
                               (and (pathnamep path) (probe-file path)
                                    (some (lambda (relative) (snapshot-same-path-p path (cl-mpm-path relative)))
                                          '("" "framework/" "studio/lisp/")))) asdf:*central-registry*)))
    (asdf:initialize-output-translations
     (list :output-translations
           (list (merge-pathnames "**/*.*" source) (merge-pathnames "**/*.*" cache))
           :inherit-configuration))
    (let ((*native-snapshot-context* (list :output directory :source source :cache cache :index index :records records :actions nil)))
      (dolist (relative '("cl-mpm.asd" "cl-mpm-simulation.asd" "cl-mpm-materials.asd" "framework/cl-mpm-framework.asd"))
        (let ((path (merge-pathnames relative source)))
          (when (probe-file path) (snapshot-verify-file path) (asdf:load-asd path))))
      *native-snapshot-context*)))

(defun frozen-case-components (directory)
  "Compatibility guard for callers inspecting the framework file-component tree."
  (let ((root (truename (merge-pathnames "source/" directory))) (files nil))
    (labels ((visit (component)
               (cond ((typep component 'asdf:cl-source-file)
                      (let ((path (truename (asdf:component-pathname component))))
                        (unless (uiop:subpathp path root) (error "ASDF component escapes frozen source: ~A" path))
                        (push path files)))
                     ((typep component 'asdf:parent-component) (map nil #'visit (asdf:component-children component))))))
      (visit (asdf:find-system "cl-mpm-framework")))
    (nreverse files)))

(defun snapshot-native-proof ()
  (let* ((expected (snapshot-verify-file (merge-pathnames "libs/kirchoff.dll" (getf *native-snapshot-context* :source))))
         (actual (snapshot-module-path "kirchoff.dll"))
         (mc (find-symbol "CPPMOHRCOULOMB" "CL-MPM/EXT")))
    (unless (and actual (snapshot-same-path-p actual expected) mc (fboundp mc))
      (error "Copied native MC backend was not loaded; refusing an unrecorded fallback."))
    (snapshot-object "modulePath" (namestring actual) "sha256" (snapshot-sha256 actual)
                     "verifiedBy" "GetModuleHandleW/GetModuleFileNameW" "nativeMcEntryPresent" t)))

(defun snapshot-external-math-modules ()
  (coerce (loop for name in '("libopenblas.dll" "libblas.dll" "blas.dll" "liblapack.dll" "lapack.dll"
                             "libgfortran-5.dll" "libquadmath-0.dll" "libgcc_s_seh-1.dll" "libwinpthread-1.dll")
                for path = (snapshot-module-path name) when path
                collect (snapshot-object "module" name "path" (namestring path) "sha256" (snapshot-sha256 path))) 'vector))

(defun write-case-source-provenance (directory copied components)
  (declare (ignore components))
  (dolist (path copied) (snapshot-verify-file path))
  (snapshot-write-json
   (merge-pathnames "source-provenance.json" directory)
   (snapshot-object
    "sourceSnapshotExactLoadedBytes" t "copiedByteEqualityBeforeLoad" t
    "scope" "Selected first-party ASDF sources, copied case/inputs and actual copied kirchoff DLL; third-party dependencies remain external."
    "copiedFiles" (coerce (mapcar (lambda (path) (enough-namestring path directory)) copied) 'vector)
    "verifiedAsdfActions" (coerce (reverse (getf *native-snapshot-context* :actions)) 'vector)
    "nativeBackend" (snapshot-native-proof) "externalMathModuleProbes" (snapshot-external-math-modules)
    "compilerPolicy" (prin1-to-string (symbol-value (find-symbol "*OPTIMISE-SETTING*" "CL-MPM/SETTINGS")))
    "storedGitVersionFile" (uiop:read-file-string
                             (merge-pathnames "config/git-commit-version.txt" (getf *native-snapshot-context* :source)))
    "executedSourceIdentity" "Pre-load source-manifest.json SHA-256 records; launch collector records commit attribution separately."
    "features" (coerce (sort (mapcar #'symbol-name *features*) #'string<) 'vector)
    "openblasThreads" (uiop:getenv "OPENBLAS_NUM_THREADS") "ompThreads" (uiop:getenv "OMP_NUM_THREADS")
    "privateFaslCache" (namestring (getf *native-snapshot-context* :cache))
    "limits" #("Third-party dependency sources/FASLs remain installed external dependencies."
                "Math module probes do not enumerate every loaded process DLL."
                "Trusted cases may execute arbitrary non-ASDF LOADs; those are outside the ASDF source claim."))))
