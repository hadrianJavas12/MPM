;;;; studio/lisp/run.lisp — command-line entry point for the cliff scenario.
;;;;
;;;;   windows\cl-mpm.cmd studio\lisp\run.lisp                       defaults -> output\cliff\
;;;;   windows\cl-mpm.cmd studio\lisp\run.lisp my.json               -> next to my.json
;;;;   windows\cl-mpm.cmd studio\lisp\run.lisp my.json output\run1   explicit output dir
;;;;
;;;; Keys and ranges of the JSON file: studio/schema.json.

(in-package :cl-user)

(format t "~&Loading CL-MPM (the first run compiles everything and can take a few minutes)...~%")
(finish-output)
(ql:quickload :cl-mpm-studio :silent t)
(uiop:quit (cl-mpm-studio:main (cl-mpm-script-args)))
