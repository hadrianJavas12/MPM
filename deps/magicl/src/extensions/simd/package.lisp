(defpackage #:magicl.simd
  (:use #:cl
        #:magicl
        )
  ;; XXX: This is kind of annoying...
  (:shadowing-import-from #:magicl
                          #:vector
                          #:=
                          #:map
                          #:trace
                          #:every
                          #:some
                          #:notevery
                          #:notany
                          #:make-array)
  )

(magicl:define-backend :simd
  :documentation "Backend for vector/matrix operations written using native sbcl SIMD features."
  :default t)
