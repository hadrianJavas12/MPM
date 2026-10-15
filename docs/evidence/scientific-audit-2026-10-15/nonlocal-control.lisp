;;;; Diagnostic only: two controlled material points; no accepted output modified.
;;;; Calls the real native delocalisation and kernel, without damage integration.
(in-package :cl-user)
(ql:quickload :cl-mpm-studio :silent t)
(in-package :cl-mpm-studio)

(let* ((config (load-config (cl-user::cl-mpm-path "studio/reference/joss-bay-accepted-collapse.json")))
       (output (cl-user::cl-mpm-path "output/scientific-audit-2026-10-15/nonlocal-control.json")))
  (setf (gethash "meshSize" config) 1d0
        (gethash "mpsPerCell" config) 1
        (gethash "workers" config) 1)
  (cl-mpm/utils:set-workers 1)
  (let* ((sim (make-joss-reference-sim config))
         (mesh (cl-mpm:sim-mesh sim))
         (a (aref (cl-mpm:sim-mps sim) 0))
         (b (aref (cl-mpm:sim-mps sim) 1))
         (result (make-hash-table :test #'equal)))
    (setf (cl-mpm:sim-mps sim) (vector a b))
    (loop for mp in (list a b) for x in '(2d0 2.3d0) do
      (setf (cl-mpm/utils:varef (cl-mpm/particle:mp-position mp) 0) x
            (cl-mpm/utils:varef (cl-mpm/particle:mp-position mp) 1) 2d0
            (cl-mpm/particle:mp-volume mp) 1d0
            (cl-mpm/particle::mp-local-length mp) 0.5d0
            (cl-mpm/particle::mp-enable-damage mp) t))
    (setf (cl-mpm/particle::mp-true-local-length a) 0.1d0
          (cl-mpm/particle::mp-true-local-length b) 0.5d0
          (cl-mpm/particle::mp-damage-y-local a) 0d0
          (cl-mpm/particle::mp-damage-y-local b) 100d0)
    (cl-mpm/damage::update-delocalisation-list mesh (cl-mpm:sim-mps sim))
    (cl-mpm/damage::delocalise-damage sim)
    (let* ((actual-ab (cl-mpm/damage::weight-func-mps mesh a b (sqrt (* 0.5d0 0.5d0))))
           (actual-ba (cl-mpm/damage::weight-func-mps mesh b a (sqrt (* 0.5d0 0.1d0))))
           (expected-radius (sqrt (* 0.1d0 0.5d0)))
           (expected-ab (cl-mpm/damage::weight-func-mps mesh a b expected-radius))
           (expected-ba (cl-mpm/damage::weight-func-mps mesh b a expected-radius)))
      (setf (gethash "kind" result) "Native two-point transient nonlocal kernel counterexample"
            (gethash "dataModified" result) "Synthetic diagnostic inputs only; no accepted artifact changes"
            (gethash "nominalRadius" result) 0.5d0
            (gethash "trueRadiusA" result) 0.1d0
            (gethash "trueRadiusB" result) 0.5d0
            (gethash "separation" result) 0.3d0
            (gethash "actualUnnormalizedWeightAFromB" result) actual-ab
            (gethash "actualUnnormalizedWeightBFromA" result) actual-ba
            (gethash "symmetricDamagedRadiusWeightAFromB" result) expected-ab
            (gethash "symmetricDamagedRadiusWeightBFromA" result) expected-ba
            (gethash "actualAveragedDriveA" result) (cl-mpm/particle::mp-damage-ybar a)
            (gethash "actualAveragedDriveB" result) (cl-mpm/particle::mp-damage-ybar b)
            (gethash "symmetricKernelContractSatisfied" result)
            (if (< (abs (- actual-ab actual-ba)) 1d-12) t :false)
            (gethash "acceptedRunImpactQuantified" result) :false)
      (assert (> (abs (- actual-ab actual-ba)) 0.1d0))
      (assert (= expected-ab expected-ba 0d0))
      (assert (> (cl-mpm/particle::mp-damage-ybar a) 0d0)))
    (with-open-file (stream output :direction :output :if-exists :supersede)
      (write-string (jonathan:to-json result) stream))
    (format t "~&NATIVE NONLOCAL DIAGNOSTIC: ~A~%" (jonathan:to-json result))))
(uiop:quit 0)
