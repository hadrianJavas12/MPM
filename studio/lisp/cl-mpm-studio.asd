;;;; cl-mpm-studio.asd — headless runner behind CL-MPM Studio.
;;;;
;;;; Builds a parameterised chalk-cliff collapse scenario (derived from
;;;; examples/chalk/chalk.lisp) and writes VTK + PNG frames.  Used by the web
;;;; UI (studio/server.js) and directly from the command line:
;;;;   windows\cl-mpm.cmd studio\lisp\run.lisp [config.json] [output-dir]

(defsystem "cl-mpm-studio"
  :description "Parameterised cliff-collapse runner for CL-MPM Studio"
  :license "MIT"
  :depends-on ("cl-mpm"
               "cl-mpm/setup"
               "cl-mpm/damage"
               "cl-mpm/models/chalk"
               "cl-mpm/output"
               "cl-mpm/plotter"
               "vgplot"
               "jonathan"
               "uiop")
  :serial t
  :components ((:file "package")
               (:file "config")
               (:file "scenario")
               (:file "runner")))
