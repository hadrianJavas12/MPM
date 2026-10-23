;;;; Synthetic supervisor test: no project systems or simulation updates.
(dotimes (i 15) (format t "TICK ~D~%" i) (finish-output) (sleep 1))
(format t "FINISHED~%") (finish-output)
(sb-ext:exit :code 7)
