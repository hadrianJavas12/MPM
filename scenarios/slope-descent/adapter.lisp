(in-package :cl-mpm/framework)

(defmethod compile-scenario ((scenario (eql :slope-descent)) (case simulation))
  (cl-mpm/scenario/slope-descent:compile-configuration case))

(defmethod execute-scenario ((scenario (eql :slope-descent)) (case simulation) config directory)
  (declare (ignore scenario))
  (cl-mpm/scenario/slope-descent:run (simulation-material case) config directory))
