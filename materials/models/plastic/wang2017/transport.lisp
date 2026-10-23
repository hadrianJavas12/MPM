;;;; Rotation-only transport of a signed spatial tensor, not an Fp evolution law.
(in-package :cl-mpm/models/wang2017-native)

(defun %checked-matrix (matrix rows columns name)
  (mc-evolution::%adapter-checked-matrix matrix rows columns name))

(defun %tensor-matrix (components)
  (cl-mpm/utils:voight-to-matrix
   (cl-mpm/utils:voigt-from-list (coerce (paper::checked-tensor components) 'list))))

(defun %matrix-tensor (matrix)
  (copy-seq (cl-mpm/utils:fast-storage (cl-mpm/utils:matrix-to-voight matrix))))

(defun proper-polar-rotation (increment)
  "Owned proper R from A=RU. A is the engine strain increment, never total F.
No modification of A, eigenvalue clamp, reflected rotation, or plastic stretch."
  (%checked-matrix increment 3 3 "Wang transport increment")
  (unless (> (cl-mpm/fastmaths:det-3x3 increment) 0d0)
    (mc-evolution::integration-fail "Wang transport requires positive nonsingular det(A)"))
  (multiple-value-bind (u singular vt) (magicl:svd (magicl:scale increment 1d0))
    (dotimes (i 3)
      (unless (> (magicl:tref singular i i) 0d0)
        (mc-evolution::integration-fail "Wang polar decomposition is singular")))
    (let ((rotation (magicl:@ u vt)))
      (%checked-matrix rotation 3 3 "Wang polar rotation")
      (unless (< (abs (- (cl-mpm/fastmaths:det-3x3 rotation) 1d0)) 1d-10)
        (mc-evolution::integration-fail "Wang polar rotation is not proper"))
      (let ((identity (magicl:@ (magicl:transpose rotation) rotation)))
        (dotimes (i 3) (dotimes (j 3)
          (unless (< (abs (- (magicl:tref identity i j) (if (= i j) 1d0 0d0))) 1d-10)
            (mc-evolution::integration-fail "Wang polar rotation is not orthonormal")))))
      rotation)))

(defun transport-paper-tensor (tensor increment)
  "Return owned (VALUES R Ep R^T, R), in physical xx yy zz yz zx xy order.
This is a corotational transport approximation; it does not transport elastic strain."
  (let* ((rotation (proper-polar-rotation increment))
         (transported (magicl:@ rotation (%tensor-matrix tensor) (magicl:transpose rotation))))
    (values (%matrix-tensor transported) rotation)))
