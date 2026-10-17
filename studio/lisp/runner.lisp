;;;; CLI compatibility adapter; native stepping/output live in framework/.
(in-package :cl-mpm-studio)

(eval-when (:load-toplevel :execute)
  (dolist (name '(colour-function png-file-complete-p save-frame numbered))
    (setf (fdefinition name)
          (fdefinition (find-symbol (symbol-name name) :cl-mpm/framework/cliff)))))

(defun run (config output-dir)
  (cl-mpm/framework/cliff:run config output-dir :cliff-builder #'make-cliff-sim))

(defun default-output-dir ()
  (asdf:system-relative-pathname "cl-mpm" "output/cliff/"))

(defun main (args)
  "Entry point. ARGS = ([config.json] [output-dir] [custom-model.lisp]).
Without a config every parameter takes its schema default; the output
directory defaults to the config file's directory, else output/cliff/.
Returns a process exit code."
  (destructuring-bind (&optional config-path output-dir custom-path) args
    (handler-case
        (let* ((config-path (and config-path (uiop:parse-native-namestring config-path)))
               (config (load-config config-path))
               (output-dir (cond (output-dir (uiop:ensure-directory-pathname
                                              (uiop:parse-native-namestring output-dir)))
                                 (config-path (uiop:pathname-directory-pathname config-path))
                                 (t (default-output-dir)))))
          (when (eq (param config "constitutiveModel") :custom)
            (load-custom-model
             (and custom-path (uiop:parse-native-namestring custom-path))))
          (run config output-dir)
          (format t "~&SUCCESS~%")
          0)
      (error (e)
        (format *error-output* "~&ERROR: ~A~%" e)
        1))))
