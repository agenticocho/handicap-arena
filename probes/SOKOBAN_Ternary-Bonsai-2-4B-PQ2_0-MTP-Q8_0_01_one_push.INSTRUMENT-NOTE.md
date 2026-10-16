# Instrument note -- this artifact is NOT from the shipped driver binary

- artifact      : SOKOBAN_Ternary-Bonsai-2-4B-PQ2_0-MTP-Q8_0_01_one_push.json
- driver        : sokoban_run.py (imported unmodified, reader of record)
- binary actually used : `/home/chilly1/src/PrismML-Bonsai-demo-20261016/bin/cuda/llama-server`
  (build 10777, commit e3de71522 -- the PRISM fork, release prism-b10777-e3de715)
- binary the driver hardcodes by default : `/home/chilly1/llama.cpp/build/bin/llama-server`
- why : mainline llama.cpp LOADS these ternary ggufs and emits degenerate garbage; it
  does not apply the prism hadamard transform (prism.hadamard.version 2) the file
  declares. Measured 2026-10-16 by Chilly (Local Chair).
- override method : module-level constant set at the call site, in memory only
- NOT RECORDED BY THE ARTIFACT : the record contains no server_argv field, so without
  this note the artifact is indistinguishable from one the default binary produced.
  Permanent fix = a --llama-server flag on the driver, pre-registered.
- reasoning arm : `off` (declared for this cabinet; the fork honours
  it and the model emits a bare move instead of a deliberation preamble)
- entrant       : `/home/chilly1/moltbook_pipeline/models/Ternary-Bonsai-2-4B-PQ2_0-MTP-Q8_0.gguf`
