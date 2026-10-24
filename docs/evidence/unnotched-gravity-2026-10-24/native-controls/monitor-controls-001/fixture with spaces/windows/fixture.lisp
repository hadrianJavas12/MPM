;;;; Trusted synthetic process control; no Quicklisp/MPM/project systems.
(let* ((case-file (second sb-ext:*posix-argv*))
       (output (third sb-ext:*posix-argv*))
       (mode (with-open-file (s case-file) (string-trim '(#\Return #\Newline) (read-line s))))
       (path (format nil "~A/manifest.json" output)))
  (ensure-directories-exist path)
  (flet ((write-state (complete)
           (with-open-file (s path :direction :output :if-exists :supersede)
             (format s "{\"status\":\"fixture\",\"complete\":~A,\"phase\":\"synthetic\",\"timeS\":1.2,\"updates\":0,\"savedFrames\":0}"
                     (if complete "true" "false")))))
    (write-state nil) (format t "Native process fixture only.~%") (finish-output)
    (sleep (if (string= mode "timeout") 30 1.5))
    (write-state (string= mode "success"))
    (sb-ext:exit :code (if (string= mode "success") 0 7))))
