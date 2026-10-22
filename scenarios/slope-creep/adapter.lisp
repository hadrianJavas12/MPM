(in-package :cl-mpm/framework)

(defmethod compile-scenario ((scenario (eql :slope-creep)) (case simulation))
  (cl-mpm/scenario/slope-creep:compile-configuration case))

(defmethod execute-scenario ((scenario (eql :slope-creep)) (case simulation) config directory)
  (declare (ignore scenario))
  (cl-mpm/scenario/slope-creep:run (simulation-material case) config directory))

