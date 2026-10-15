;;;; Compatibility adapter for existing Studio/exported Lisp entry points.
;;;; Reusable native simulation ownership lives in cl-mpm-framework.

(defsystem "cl-mpm-studio"
  :description "Parameterised cliff-collapse runner for CL-MPM Studio"
  :license "MIT"
  :depends-on ("cl-mpm-framework")
  :serial t
  :components ((:file "package")
               (:file "config")
               (:file "custom-model")
               (:file "scenario")
               (:file "runner")
               (:file "reference-joss")))
