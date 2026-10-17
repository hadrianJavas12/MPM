;;;; P4 loader/owner compatibility only; no solver timesteps or output files.
;;;; windows\cl-mpm.cmd tests\p4-orchestration-compat.lisp B|C|D|E|F
(in-package :cl-user)
(ql:quickload :cl-mpm-framework :silent t)

(defun p4-owned-source-components (component)
  (cond ((typep component 'asdf:cl-source-file)
         (list (truename (asdf:component-pathname component))))
        ((typep component 'asdf:parent-component)
         (mapcan #'p4-owned-source-components
                 (coerce (asdf:component-children component) 'list)))))

(defun p4-stage-for-source (relative)
  (cond ((member relative '("framework/config/package.lisp" "framework/config/parameters.lisp"
                           "framework/package.lisp" "framework/components/geometry.lisp"
                           "framework/simulation.lisp") :test #'equal) #\B)
        ((member relative '("framework/materials/chalk.lisp" "framework/scenarios/cliff/settings.lisp"
                           "framework/output/plotting.lisp") :test #'equal) #\C)
        ((and (uiop:string-prefix-p "framework/scenarios/" relative)
              (equal (pathname-type relative) "lisp")) #\D)))

(let* ((stage-text (or (first (cl-mpm-script-args)) (error "Supply stage B, C, D, E or F.")))
       (stage (char (string-upcase stage-text) 0))
       (plan (jonathan:parse (uiop:read-file-string
                             (cl-mpm-path "docs/architecture/P4_ORCHESTRATION_MIGRATION.json"))
                            :as :hash-table))
       (system (asdf:find-system "cl-mpm-framework"))
       (components (p4-owned-source-components system))
       (checks 0))
  (assert (and (= (length stage-text) 1) (find stage "BCDEF")))
  (assert (null (find-package :cl-mpm-studio)))
  (assert (= (length components) (length (remove-duplicates components :test #'equal))))
  (dolist (id (coerce (gethash "ordered_component_ids" (gethash "current_asdf" plan)) 'list))
    (assert (asdf:find-component system id)))
  (incf checks)
  (format t "~&PASS: Public ASDF IDs remain, implementation paths load once, and Studio is not required.~%")
  (let ((shims nil) (targets-to-reload nil))
    (dolist (record (coerce (gethash "framework_records" plan) 'list))
      (let* ((relative (gethash "source_path" record)) (introduced (p4-stage-for-source relative)))
        (when (and introduced (char<= introduced stage))
          (push relative shims)
          (dolist (target (coerce (gethash "target_paths" record) 'list))
            (assert (member (truename (cl-mpm-path target)) components :test #'equal))
            (pushnew target targets-to-reload :test #'equal))
          ;; If a compatibility path still exists on disk, it must contain forwarding code only.
          (when (probe-file (cl-mpm-path relative))
            (with-open-file (stream (cl-mpm-path relative))
              (let ((*read-eval* nil))
                (loop for form = (read stream nil :eof) until (eq form :eof) do
                  (assert (not (member (first form)
                                       '(defun defclass defgeneric defmethod defvar defparameter)))))))))))
    (incf checks)
    (format t "~&PASS: Applied stage owners resolve directly; old source paths retired or forwarding only.~%")
    (let* ((class-symbols '(cl-mpm/framework:component cl-mpm/framework:material
                            cl-mpm/framework:simulation
                            cl-mpm/framework/cliff::joss-reference-chalk
                            cl-mpm/framework/cliff::joss-reference-sim
                            cl-mpm/framework/cliff::joss-reference-aggregate-sim))
           (classes (mapcar #'find-class class-symbols))
           (generics (list #'cl-mpm/framework:compile-scenario
                           #'cl-mpm/framework:execute-scenario))
           (method-counts (mapcar (lambda (function) (length (sb-mop:generic-function-methods function)))
                                  generics))
           (live (cl-mpm/framework:make-material :von-mises)))
      (let ((*default-pathname-defaults* (cl-mpm-path "output/")))
        (loop repeat 2 do
          (dolist (relative (reverse targets-to-reload))
            (load (cl-mpm-path relative)))))
      (assert (every #'eq classes (mapcar #'find-class class-symbols)))
      (assert (typep live 'cl-mpm/framework:material))
      (assert (eq (first generics) #'cl-mpm/framework:compile-scenario))
      (assert (eq (second generics) #'cl-mpm/framework:execute-scenario))
      (assert (equal method-counts
                     (mapcar (lambda (function) (length (sb-mop:generic-function-methods function)))
                             generics)))
      (incf checks)
      (format t "~&PASS: Canonical owners reload from another directory without replacing classes/live objects or duplicating dispatch.~%")))
  (when (char= stage #\F)
    (assert (equal (truename (asdf:system-source-directory "cl-mpm-framework"))
                   (truename (cl-mpm-path ""))))
    (assert (every (lambda (file) (not (uiop:subpathp file (cl-mpm-path "framework/")))) components))
    (incf checks)
    (format t "~&PASS: Canonical ASDF is at root; framework owns no loaded implementation.~%"))
  (format t "~&P4 ORCHESTRATION COMPATIBILITY: ~D passed; no solver timesteps.~%" checks))
(uiop:quit 0)
