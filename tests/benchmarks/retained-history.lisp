;;;; Diagnostic file lifecycle only: no framework loading or physical timesteps.
(in-package :cl-user)
(load (cl-mpm-path "src/output/retained-history.lisp"))

(defvar *retained-history-checks* 0)
(defmacro history-check (label &body body)
  `(progn ,@body (incf *retained-history-checks*)
          (format t "~&PASS: ~A~%" ,label)))

(defun history-rows (path)
  (with-open-file (stream path)
    (loop for row = (read-line stream nil) while row collect row)))

(let* ((directory (merge-pathnames
                   (format nil "retained-history-~A/" (symbol-name (gensym "TEST-")))
                   (uiop:temporary-directory)))
       (path (merge-pathnames "history.csv" directory)))
  (ensure-directories-exist path)
  (unwind-protect
       (progn
         (history-check "Two flushed rows and original error survive an abnormal exit"
           (let* ((original (make-condition 'simple-error :format-control "injected body failure"))
                  (caught (handler-case
                              (cl-mpm/output/history:with-retained-history
                                  (stream path :direction :output :if-exists :supersede
                                               :if-does-not-exist :create)
                                (format stream "time_s,displacement_m~%")
                                (format stream "0,0~%") (finish-output stream)
                                (format stream "1,0.002~%") (finish-output stream)
                                (error original))
                            (error (condition) condition))))
             (assert (eq original caught))
             (assert (probe-file path))
             (assert (equal (history-rows path)
                            '("time_s,displacement_m" "0,0" "1,0.002")))))
         (history-check "Normal completion flushes output and preserves all body values"
           (assert (equal
                    (multiple-value-list
                     (cl-mpm/output/history:with-retained-history
                         (stream path :direction :output :if-exists :supersede
                                      :if-does-not-exist :create)
                       (declare (type stream stream))
                       (write-string "completed" stream)
                       (values :first nil 3)))
                    '(:first nil 3)))
           (assert (equal (history-rows path) '("completed"))))
         (history-check "Cleanup failure preserves the original body error"
           (let* ((original (make-condition 'simple-error :format-control "original body failure"))
                  (caught
                    (flet ((cl-mpm/output/history::close-retained-stream (stream)
                             (close stream :abort nil)
                             (error "injected cleanup failure")))
                      (handler-case
                          (cl-mpm/output/history:with-retained-history
                              (stream path :direction :output :if-exists :supersede
                                           :if-does-not-exist :create)
                            (write-string "retained" stream)
                            (error original))
                        (error (condition) condition)))))
             (assert (eq original caught))
             (assert (equal (history-rows path) '("retained")))))
         (history-check "Normal cleanup failure is signalled"
           (let ((caught
                   (flet ((cl-mpm/output/history::close-retained-stream (stream)
                            (close stream :abort nil)
                            (error "injected normal cleanup failure")))
                     (handler-case
                         (cl-mpm/output/history:with-retained-history
                             (stream path :direction :output :if-exists :supersede
                                          :if-does-not-exist :create)
                           (write-string "finished before cleanup failure" stream)
                           :body-success)
                       (error (condition) condition)))))
             (assert (typep caught 'simple-error))
             (assert (equal (history-rows path) '("finished before cleanup failure"))))))
    (when (probe-file path) (delete-file path))
    (when (probe-file directory) (uiop:delete-empty-directory directory))))

(format t "~&RETAINED HISTORY CONTROLS: ~D passed; no physical updates executed.~%"
        *retained-history-checks*)
(uiop:quit 0)
