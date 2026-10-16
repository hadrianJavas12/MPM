;;;; Fresh bounded old-source baseline; bootstrap with the main Windows launcher.
;;;; ARGS = (copied-old-root trusted-copied-case fresh-output-directory).
;;;; The numerical CLI/helper/ASDF/models are loaded from copied-old-root.
;;;; Third-party Quicklisp/OpenBLAS remain those selected by main windows/init.
(in-package :cl-user)
(let* ((arguments (cl-mpm-script-args))
       (old-root (and (first arguments)
                      (uiop:ensure-directory-pathname
                       (uiop:parse-native-namestring (first arguments)))))
       (case-file (and (second arguments)
                      (uiop:parse-native-namestring (second arguments))))
       (output (and (third arguments)
                    (uiop:ensure-directory-pathname
                     (uiop:parse-native-namestring (third arguments))))))
  (unless (and (= (length arguments) 3) old-root case-file output
               (probe-file old-root) (probe-file case-file))
    (error "Supply copied-old-root, trusted case and fresh output directory."))
  (when (or (uiop:subpathp output old-root) (uiop:subpathp old-root output))
    (error "Old-source root and output must be separate trees."))
  ;; The old CLI independently checks a fresh project runtime, all selected
  ;; ASDF source paths/private FASLs and the actual copied DLL mapping.
  (let ((*cl-mpm-root* (truename old-root))
        (*default-pathname-defaults* (truename old-root))
        (sb-ext:*posix-argv*
          (list (first sb-ext:*posix-argv*) "--end-toplevel-options"
                (namestring case-file) (namestring output))))
    (load (merge-pathnames "run-case.lisp" old-root))))
