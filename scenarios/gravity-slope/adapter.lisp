(in-package :cl-mpm/framework)

(defmethod compile-scenario ((scenario (eql :gravity-slope)) (case simulation))
  (cl-mpm/scenario/gravity-slope:compile-configuration case))

(defmethod execute-scenario ((scenario (eql :gravity-slope)) (case simulation) config directory)
  (declare (ignore scenario))
  (cl-mpm/scenario/gravity-slope:run (simulation-material case) config directory))
