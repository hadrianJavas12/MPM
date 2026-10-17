;;;; Metadata-only ASDF inspection. Never LOAD-SYSTEM a CL-MPM system.
;;;; Run: sbcl --no-sysinit --no-userinit --script scripts/audit-asdf-metadata.lisp OUTPUT.json
(require :asdf)

(defparameter *audit-root*
  (truename (merge-pathnames "../" (uiop:pathname-directory-pathname *load-truename*))))

(defun audit-json-string (value stream)
  (write-char #\" stream)
  (loop for char across value do
    (case char
      (#\" (write-string "\\\"" stream))
      (#\\ (write-string "\\\\" stream))
      (#\Newline (write-string "\\n" stream))
      (#\Return (write-string "\\r" stream))
      (#\Tab (write-string "\\t" stream))
      (otherwise
       (if (< (char-code char) 32)
           (format stream "\\u~4,'0X" (char-code char))
           (write-char char stream)))))
  (write-char #\" stream))

(defun audit-json (value stream)
  (typecase value
    (hash-table
     (write-char #\{ stream)
     (let ((first t))
       (maphash (lambda (key item)
                  (unless first (write-char #\, stream))
                  (setf first nil)
                  (audit-json-string key stream)
                  (write-char #\: stream)
                  (audit-json item stream)) value))
     (write-char #\} stream))
    (string (audit-json-string value stream))
    (null (write-string "null" stream))
    (vector
     (write-char #\[ stream)
     (loop for item across value for first = t then nil do
       (unless first (write-char #\, stream))
       (audit-json item stream))
     (write-char #\] stream))
    (integer (princ value stream))
    (t (error "Unsupported audit JSON value: ~S" value))))

(defun audit-object (&rest pairs)
  (let ((object (make-hash-table :test 'equal)))
    (loop for (key value) on pairs by #'cddr do (setf (gethash key object) value))
    object))

(defun audit-relative (pathname)
  (substitute #\/ #\\ (enough-namestring pathname *audit-root*)))

(defun audit-component (component)
  (audit-object
   "name" (asdf:component-name component)
   "class" (string-downcase (symbol-name (class-name (class-of component))))
   "path" (audit-relative (asdf:component-pathname component))
   "children" (coerce (when (typep component 'asdf:parent-component)
                         (mapcar #'audit-component (asdf:component-children component)))
                       'vector)))

(let* ((output (first (uiop:command-line-arguments)))
       (definitions '("cl-mpm.asd" "cl-mpm-tests.asd"
                      "framework/cl-mpm-framework.asd" "studio/lisp/cl-mpm-studio.asd"
                      "deps/magicl/magicl.asd" "deps/magicl/magicl-gen.asd"
                      "deps/magicl/magicl-examples.asd" "deps/magicl/magicl-tests.asd"
                      "deps/magicl/magicl-transcendental.asd"
                      "deps/swank.live/swank.live.asd" "deps/vgplot/vgplot.asd"))
       (errors nil)
       (systems nil)
       (setup (find-if #'probe-file
                       (list (merge-pathnames "toolchain/quicklisp/setup.lisp" *audit-root*)
                             (merge-pathnames "quicklisp/setup.lisp" (user-homedir-pathname))))))
  (unless output (error "Supply an audit metadata OUTPUT.json path."))
  ;; Quicklisp registers installed dependency definitions. No downloads or QUICKLOAD.
  (when setup (load setup))
  (dolist (directory '("" "framework/" "studio/lisp/" "deps/magicl/"
                       "deps/swank.live/" "deps/vgplot/"))
    (pushnew (merge-pathnames directory *audit-root*) asdf:*central-registry* :test #'equal))
  #+win32 (pushnew :cl-mpm-no-mpi *features*)
  (dolist (relative definitions)
    (handler-case (asdf:load-asd (merge-pathnames relative *audit-root*))
      (error (condition)
        (push (audit-object "definition" relative "error" (princ-to-string condition)) errors))))
  (dolist (name (sort (copy-list (asdf:registered-systems)) #'string<))
    (handler-case
        (let* ((system (asdf:find-system name nil))
               (source (when system (asdf:system-source-file system)))
               (relative (when source (audit-relative source))))
          (when (member relative definitions :test #'string=)
            (push (audit-object
                   "name" name "source_asd" relative
                   "depends_on" (coerce (mapcar (lambda (dependency)
                                                  (if (stringp dependency) dependency
                                                      (with-standard-io-syntax
                                                        (prin1-to-string dependency))))
                                                (asdf:system-depends-on system)) 'vector)
                   "component_tree" (audit-component system)) systems)))
      (error (condition)
        (push (audit-object "system" name "error" (princ-to-string condition)) errors))))
  (with-open-file (stream output :direction :output :if-exists :supersede
                          :if-does-not-exist :create :external-format :utf-8)
    (audit-json
     (audit-object
      "schema_version" 1 "mode" "native-ASDF-definition-introspection"
      "lisp_implementation" (lisp-implementation-type)
      "lisp_version" (lisp-implementation-version)
      "asdf_version" (asdf:asdf-version)
      "features" (coerce (sort (mapcar #'symbol-name *features*) #'string<) 'vector)
      "definitions_requested" (coerce definitions 'vector)
      "systems" (coerce (nreverse systems) 'vector)
      "errors" (coerce (nreverse errors) 'vector)
      "scope" "ASD definitions and component registration only; no CL-MPM source load, compile, test-op, operation plan or solver execution. cl-mpm.asd itself loads the installed asdf-system-connections utility. Components may have feature/operation gates; registration is not runtime loading proof.") stream)
    (terpri stream))
  (format t "Metadata written: ~A (~D systems, ~D errors)~%" output (length systems) (length errors))
  (uiop:quit (if errors 2 0)))
