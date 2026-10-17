# Native source-freeze evidence

Snapshot contracts 3/3, corrected native snapshot contracts 7/7, material diagnostics 9/9, and bounded VM/MC strict P3 comparisons passed. Source, FASL and actual Windows DLL path/hash proof is retained for native snapshots and CLI VM. MC uses the existing live suite with captured source hashes; its cached FASL identity is separate.

Initial VM001 failed before simulation because bootstrap artifacts violated the output freshness guard; failure, sources, cache and logs are retained. The fix moves them under source/. No full Joss run was restarted. G1/G3 remain partial; no scientific validation is claimed.
