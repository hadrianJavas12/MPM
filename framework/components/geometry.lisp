(in-package :cl-mpm/framework)

(defgeneric geometry-filter (geometry)
  (:documentation "Optional run-local (x,y,z)->boolean clipping predicate."))
(defmethod geometry-filter ((geometry geometry))
  (let ((filter (option geometry :filter)))
    (when (and filter (not (functionp filter)))
      (error "Geometry :FILTER must be a function of x, y, z."))
    filter))
