;;;; Native triaxial scenario: boundaries.lisp
(in-package :cl-mpm/calibration/triaxial)

(defclass isotropic-pressure (cl-mpm/bc::bc)
  ((pressure :initarg :pressure :reader pressure)))
(defmethod cl-mpm/bc::apply-sim-bc (sim (bc isotropic-pressure) dt)
  (declare (ignore dt))
  (loop for mp across (cl-mpm:sim-mps sim) do
    (let ((scale (* (- (pressure bc)) (cl-mpm/particle:mp-volume mp))))
      (cl-mpm:iterate-over-neighbours
       (cl-mpm:sim-mesh sim) mp
       (lambda (node svp grads fsvp fgrads)
         (declare (ignore svp fsvp fgrads))
         (let ((force (cl-mpm/mesh::node-external-force node)))
           (incf (component force 0) (* scale (cl-mpm/utils::gradients-dx grads)))
           (incf (component force 1) (* scale (cl-mpm/utils::gradients-dy grads)))
           (incf (component force 2) (* scale (cl-mpm/utils::gradients-dz grads)))))))))
