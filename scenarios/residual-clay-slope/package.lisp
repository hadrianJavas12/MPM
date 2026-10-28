(defpackage :cl-mpm/scenario/residual-clay-slope
  (:use :cl)
  (:local-nicknames (:fw :cl-mpm/framework) (:mc :cl-mpm/models/mc-evolution)
                    (:gs :cl-mpm/scenario/gravity-slope) (:u :cl-mpm/scenario/urmi-damage40))
  (:import-from :cl-mpm/scenario/urmi-damage40
    #:obj #:value #:component #:write-json #:force-ratio #:force-numerator2
    #:force-denominator2 #:free-ke #:free-nodal-mass #:stable-dt))
