;;;; Existing declarations extracted without numerical changes.
(in-package :cl-mpm/framework)

(defclass component ()
  ((kind :initarg :kind :reader component-kind)
   (options :initarg :options :reader component-options)))

(defun option (component key &optional default)
  (getf (component-options component) key default))

(defun make-component (class kind options allowed)
  (unless (and (keywordp kind) (evenp (length options)))
    (error "A component needs a keyword kind and keyword/value options."))
  (loop for tail on options by #'cddr for key = (first tail)
        unless (member key allowed) do (error "Unknown ~A option ~S" class key))
  (let ((keys (loop for tail on options by #'cddr collect (first tail))))
    (unless (= (length keys) (length (remove-duplicates keys)))
      (error "Duplicate component option in ~S" options)))
  (make-instance class :kind kind :options (copy-list options)))
