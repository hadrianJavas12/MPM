;;;; Same engine equations; project-only compiler policy and separate FASL cache.
(in-package :cl-user)
(require :asdf)
(ql:quickload :cl-mpm/settings :silent t)
(asdf:initialize-output-translations
 (list :output-translations
       (list (cl-mpm-path "src/**/*.*")
             (cl-mpm-path "output/reference-reproduction-2026-10-14/fast-cache-safe/src/**/*.*"))
       (list (cl-mpm-path "studio/lisp/**/*.*")
             (cl-mpm-path "output/reference-reproduction-2026-10-14/fast-cache-safe/studio/lisp/**/*.*"))
       :inherit-configuration))
(setf (symbol-value (find-symbol "*OPTIMISE-SETTING*" :cl-mpm/settings))
      '(optimize (speed 3) (safety 1) (debug 1) (compilation-speed 0)))
(ql:quickload :cl-mpm-studio :silent t)
(uiop:quit (cl-mpm-studio:main (cl-mpm-script-args)))
