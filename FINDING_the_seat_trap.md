# FINDING: THE SEAT TRAP IS WORSE THAN "NO SEAT SETS --reasoning"

**Measured while setting up the harness experiment. This changes the instruction the Chair gave for how a profile
is pointed at the local runtime.**

---

## WHAT THE INSTRUCTION SAYS

```
hermes -p <profile> config set model.provider llamacpp
hermes -p <profile> config set model.base_url http://127.0.0.1:8080/v1
hermes -p <profile> config set model.name <a real llama-swap alias>
```

## WHAT ACTUALLY HAPPENS — FROM HERMES'S OWN ERROR LOG, NOT FROM A GUESS

**A throwaway profile configured exactly that way, then asked to answer "OK":**

```
provider=custom base_url=http://127.0.0.1:36389/v1 model=brain
HTTP 400: model 'brain' not found
```

**TWO THINGS ARE WRONG, AND BOTH ARE SILENT.**

**1. `model.base_url` IS IGNORED.** The profile declares `http://127.0.0.1:8080/v1`. **The harness used
`http://127.0.0.1:36389/v1`.** The `llamacpp` PROVIDER carries its own endpoint — **the Hermes local runtime —
and the config value does not override it.** So the profile is pointed at a different port than its own config
file says.

**2. THE MODEL MUST BE A PRESET NAME, NOT A LLAMA-SWAP ALIAS.** Port 36389 serves the presets in
`~/.hermes/runtimes/llamacpp/presets.ini`; **`brain` is a llama-swap alias on 8080 and means nothing on 36389.**
The valid names are the eight preset sections: `Ornith-1.5-9B-Q4_K_M`, `Tiel-Inspired-Coder-9B-UD-Q4_K_M`,
`Ministral-3-3B-Instruct-2512-UD-Q4_K_XL`, `MiMo-V2.6-Distill-Qwen-9B-Q4_K_M`,
`Cyber-Tiel-Coder-35B-A3B-MTP-UD-Q4_K_XL`, `Tiel-Coder-35B-A3B-MTP-UD-Q4_K_XL`,
`Ornith-1.5-35B-A3B-Abliterated-TIEL_Calibrated-MTPv2-25G-ICE`, `LFM2.5-VL-1.6B-UD-Q8_K_XL`.

**AND THE FAILURE DOES NOT LOOK LIKE A FAILURE.** Hermes surfaces the 400 to the user as:

```
Your request was not processed. Send it again if you still want me to carry it out.
```

**That reads as a transient hiccup. It is a MISCONFIGURATION THAT WILL RECUR ON EVERY SINGLE TURN** — and a
cabinet agent that receives it will retry, fail identically, and produce nothing, while the operator sees a
message that suggests trying again.

## AND IT EXPLAINS WHY BIRDY WORKS

**`birdy`'s config names `Ornith-1.5-9B-Q4_K_M` — A PRESET NAME.** Its `model.base_url` line is inert. **It works
because the model name is right and the provider supplies the endpoint, NOT because the base_url was set.** So
the recipe that worked for Birdy was not the recipe that was written down; the base_url line is decoration and
the model name is the load-bearing part.

## AND THE CHECK THAT SETTLED A CONFOUND, WHICH IS THE ENTRANT-DIGEST RULE PAYING FOR ITSELF

**The preset loads `~/.hermes/models/Tiel-Inspired-Coder-9B-UD-Q4_K_M.gguf`; my script measured
`~/moltbook_pipeline/models/Tiel-Inspired-Coder-9B-UD-Q4_K_M.gguf`. SAME NAME, TWO PATHS.**

```
~/moltbook_pipeline/models/...gguf   5780112576 bytes   sha256 8bda33873d8cb2cf
~/.hermes/models/...gguf                   76 bytes     <- A SYMLINK to the file above
                                       both digests: 8bda33873d8cb2cf
```

**THE SAME WEIGHTS, so the harness run is comparable to the script measurement.** **Without the digest this was an
unresolvable confound — two same-named models in two directories, and no way to know whether a difference in
results was the harness or the weights. ONE COMMAND SETTLED IT.** That is exactly what the entrant digest was
added for this afternoon, and it earned its keep within the hour.

## WHAT THIS MEANS FOR THE MOVE

**THE DECLARATION THE CHAIR ASKED FOR IS LARGER THAN A NOTE ABOUT `--reasoning`.** Before any profile moves, the
following must be true and CHECKED rather than assumed:

```
1  the model name is a PRESET from presets.ini, not a llama-swap alias
2  it is confirmed by reading the PROFILE'S OWN preset section, not by a list of aliases from elsewhere
3  the endpoint the PROVIDER actually uses is known -- the declared base_url is not evidence of it
4  a TRIVIAL ROUND TRIP is run and the reply is READ, because the failure mode prints as a retry suggestion
5  and only then the reasoning setting, which is a separate question again
```

**ITEM 4 IS THE ONE I WOULD INSIST ON.** Every other item can be true while the agent still produces nothing, and
**a send that is accepted is not a turn that is answered** — which is the same shape as the `target_busy` finding
and the queued-vs-delivered distinction already in the record.
