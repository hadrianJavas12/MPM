;;;; Stand-in for the `swank.live` library.
;;;;
;;;; Upstream CL-MPM calls (swank.live:update-swank) inside long solver loops
;;;; to keep an interactive SLIME/Sly session responsive.  The real library is
;;;; not on Quicklisp; batch and Windows runs do not need it.  This system is
;;;; only registered by windows/init.lisp, so a real swank.live found in
;;;; ~/quicklisp/local-projects is not shadowed on other setups.

(defsystem "swank.live"
  :description "No-op stand-in for swank.live (headless runs)."
  :version "0.0.0"
  :components ((:file "swank-live")))
