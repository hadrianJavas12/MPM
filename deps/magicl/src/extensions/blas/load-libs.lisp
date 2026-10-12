(in-package #:magicl.foreign-libraries)

#+:magicl.use-mkl (print "Loading MKL")
#-:magicl.use-mkl (print "Loading BLAS")

(print "Loading blas libraries")
(cffi:define-foreign-library libblas
  #+:magicl.use-accelerate
  (:darwin "libBLAS.dylib" :search-path #P"/System/Library/Frameworks/Accelerate.framework/Frameworks/vecLib.framework/Versions/A/")
  #-:magicl.use-accelerate
  (:darwin (:or
            "/opt/homebrew/opt/lapack/lib/libblas.dylib"
            "/usr/local/opt/lapack/lib/libblas.dylib"
            "libblas.dylib" ))
  #+:magicl.use-mkl
  (:unix  "libmkl_rt.so")
  #-:magicl.use-mkl
  (:unix  (:or "libblas.so"
               "libblas.so.3"
               "libopenblas.so"
               "libblis.so"
               ))
  (:windows (:or "libopenblas.dll" "libopenblas" "libblas.dll" "blas.dll"))
  (t (:default "libblas")))

(pushnew 'libblas *foreign-libraries*)
(export 'libblas)

(defvar *blas-loaded* nil)

(unless *blas-loaded*
  (cffi:load-foreign-library 'libblas)
  (setf *blas-loaded* t))

(magicl:define-backend :blas
  :documentation "Backend for BLAS functionality written in Fortran."
  :default t)
