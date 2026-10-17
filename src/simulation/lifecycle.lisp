(in-package :cl-mpm/framework)

(defvar *input-root* nil)
(defun case-path (relative)
  (merge-pathnames relative (or *input-root* (asdf:system-source-directory "cl-mpm"))))
(defun read-parameter-json (path)
  "Read one object using Yason's per-object duplicate-key checks; keep null distinct from false."
  (with-open-file (stream path)
    (let ((input (yason:parse stream :object-as :hash-table :object-key-fn #'identity
                              :json-booleans-as-symbols nil :json-nulls-as-keyword t
                              :json-arrays-as-vectors nil)))
      (unless (hash-table-p input) (error "Parameter file must contain a JSON object: ~A" path))
      (loop for character = (read-char stream nil) while character
            unless (find character '(#\Space #\Tab #\Newline #\Return))
              do (error "Unexpected content after parameter object in ~A" path))
      input)))
(defun read-parameters (relative &key schema)
  (let* ((path (case-path relative)) (input (read-parameter-json path)))
    ;; Preserve historical schema coercion/defaults while checking raw duplicates first.
    (if schema (cl-mpm/framework/config:load-config path) input)))

(defgeneric compile-scenario (scenario simulation)
  (:documentation "Validate compatible components and return a fresh backend configuration."))
(defgeneric execute-scenario (scenario simulation config output-directory)
  (:documentation "Execute native physics with run-local component adapters."))
(defmethod compile-scenario (scenario simulation)
  (declare (ignore simulation)) (error "Unknown scenario ~S" scenario))

(defun finite-number (value name &key (minimum 0d0) inclusive)
  (unless (and (realp value)
               (not (sb-ext:float-nan-p (float value 1d0)))
               (not (sb-ext:float-infinity-p (float value 1d0)))
               (if inclusive (>= value minimum) (> value minimum)))
    (error "~A must be finite and ~A ~A" name (if inclusive ">=" ">") minimum))
  value)

(defun check-kind (component allowed)
  (unless (member (component-kind component) allowed)
    (error "Incompatible ~A kind ~S; supported here: ~S"
           (type-of component) (component-kind component) allowed)))

(defun overlay (config component mappings)
  "Map only explicitly supplied component options; preserve backend defaults."
  (dolist (mapping mappings config)
    (destructuring-bind (key name &optional (scale 1d0)) mapping
      (let ((marker (gensym)))
        (let ((value (option component key marker)))
          (unless (eq value marker)
            (setf (gethash name config) (if (numberp value) (* scale value) value))))))))

(defun validate-simulation (simulation)
  (compile-scenario (simulation-scenario simulation) simulation)
  simulation)

(defun run-simulation (simulation &key output)
  "Validate then execute. Output must be fresh so evidence cannot be overwritten."
  (unless output (error "Specify :OUTPUT explicitly for every simulation run."))
  (let* ((scenario (simulation-scenario simulation))
         (config (compile-scenario scenario simulation))
         (directory (uiop:ensure-directory-pathname output)))
    (when (and (probe-file directory)
               (or (remove "source-provenance.json" (uiop:directory-files directory)
                           :key #'file-namestring :test #'equal)
                   (remove "source" (uiop:subdirectories directory)
                           :key (lambda (p) (car (last (pathname-directory p)))) :test #'equal)))
      (error "Output directory is not empty: ~A. Choose a new directory." directory))
    (execute-scenario scenario simulation config directory)))
