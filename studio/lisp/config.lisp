;;;; config.lisp — run parameters, validated against studio/schema.json.
;;;;
;;;; The schema is shared with studio/server.js, so CLI runs and UI runs
;;;; accept exactly the same keys, defaults and ranges.

(in-package :cl-mpm-studio)

(defparameter *schema-path*
  (merge-pathnames "../schema.json" (asdf:system-source-directory "cl-mpm-studio"))
  "Location of the shared parameter schema.")

(defun read-json-file (path)
  "Parse the JSON file at PATH into nested hash tables (floats as doubles)."
  (let ((*read-default-float-format* 'double-float))
    (jonathan:parse (uiop:read-file-string path) :as :hash-table)))

(defun schema ()
  (gethash "parameters" (read-json-file *schema-path*)))

(defun exact-real (x)
  "jonathan parses JSON decimals as single-floats (0.3 -> 0.30000001192...d0
when widened). RATIONALIZE recovers the decimal the user actually wrote."
  (if (floatp x) (rationalize x) x))

(defun coerce-param (spec value)
  "Coerce VALUE according to the schema entry SPEC, falling back to the default
and clamping numbers into [min, max]."
  (let ((type (gethash "type" spec))
        (default (exact-real (gethash "default" spec)))
        (value (exact-real value)))
    (flet ((clamp (x) (max (exact-real (gethash "min" spec))
                           (min (exact-real (gethash "max" spec)) x))))
      (cond
        ((string= type "number")
         (float (clamp (if (realp value) value default)) 1d0))
        ((string= type "integer")
         (round (clamp (if (realp value) value default))))
        ((string= type "boolean")
         ;; jonathan: true -> T, false -> NIL; anything else -> default.
         (cond ((eq value t) t)
               ((null value) nil)
               (t default)))
        ((string= type "enum")
         (let ((choice (if (member value (gethash "values" spec) :test #'equal) value default)))
           (intern (string-upcase choice) :keyword)))
        (t default)))))

(defun load-config (&optional path)
  "Return a hash table of validated parameters (string keys).
Keys missing from the JSON file at PATH (or all keys, when PATH is NIL)
take their schema default."
  (let ((input (if path (read-json-file path) (make-hash-table :test #'equal)))
        (config (make-hash-table :test #'equal)))
    (maphash (lambda (key spec)
               (multiple-value-bind (value present) (gethash key input)
                 (setf (gethash key config)
                       (coerce-param spec (if present value (gethash "default" spec))))))
             (schema))
    config))

(defun param (config key)
  "Value of parameter KEY (a schema key such as \"meshSize\")."
  (multiple-value-bind (value present) (gethash key config)
    (unless present (error "Unknown studio parameter ~S" key))
    value))

(defun describe-config (config &optional (stream *standard-output*))
  (let ((keys (sort (loop for k being the hash-keys of config collect k) #'string<)))
    (format stream "~&Parameters:~%")
    (dolist (k keys)
      (format stream "  ~18A ~A~%" k (gethash k config)))))
