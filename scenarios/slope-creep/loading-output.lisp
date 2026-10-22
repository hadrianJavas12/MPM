(in-package :cl-mpm/scenario/slope-creep)

(defmacro with-pusher-history ((stream pusher output) &body body)
  "Open extra contact evidence only for driven cases; gravity output is unchanged."
  (let ((continue (gensym "CONTINUE")))
    `(flet ((,continue (,stream) ,@body))
       (if ,pusher
           (cl-mpm/output/history:with-retained-history
               (,stream (merge-pathnames "loading-history.csv" ,output)
                        :direction :output :if-exists :supersede :if-does-not-exist :create)
             (format ,stream "frame,time_s,commanded_settlement_m,measured_patch_settlement_m,reaction_upward_N_per_m,mapped_reaction_upward_N_per_m,active_contacts,separated_contacts,max_compression_gap_m,max_separation_gap_m,command_work_rectangle_J_per_m~%")
             (,continue ,stream))
           (,continue nil)))))

(defun write-pusher-state (stream pusher sim frame manifest)
  (when pusher
    (let ((values (pusher-observations pusher)))
      (format stream "~D" frame)
      (dolist (value (cons (cl-mpm::sim-time sim) values))
        (format stream ",~,16E" (float value 1d0)))
      (terpri stream) (finish-output stream)
      (setf (gethash "pusherCommandedSettlementM" manifest) (first values)
            (gethash "pusherMeasuredPatchSettlementM" manifest) (second values)
            (gethash "pusherReactionUpwardNPerM" manifest) (third values)
            (gethash "pusherActiveContacts" manifest) (fifth values)
            (gethash "pusherSeparatedContacts" manifest) (sixth values)
            (gethash "pusherCommandWorkRectangleJPerM" manifest) (ninth values)))))
