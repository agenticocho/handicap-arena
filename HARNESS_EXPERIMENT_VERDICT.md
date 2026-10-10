# THE HARNESS EXPERIMENT — BRANCH 4, AND THE CAUSE IS THE FINDING

**Pre-registered in `PREREG_harness.md`, committed as `c189774` before the first run.**

---

## THE RESULT

**The agent produced NOTHING.** One message in the session — the prompt. No assistant reply, no tool call, no
file. `./reachable_cells.py` was never created.

**BRANCH 4 — DOES NOT FINISH.** Per the prereg: *no result, reported as no result, not as a failure.* **Ruling
81 applies directly: it did not happen is not it cannot happen.**

## AND THE CAUSE — FROM THE LOGS, NOT INFERRED

```
HTTP 500: model name=Tiel-Inspired-Coder-9B-UD-Q4_K_M failed to load
(harness retried 5 auto-recovery cycles over ~6 minutes, then ended)
```

**WHY IT COULD NOT LOAD — THE VRAM TENANCY:**

```
card    : 5985 MiB used, 1853 MiB free
tenants : pid 409710   5532 MiB  llama-server --port 5800 --model Tiel-Inspired-Coder-9B-UD-Q4_K_M.gguf
global lease: owner=llama-swap-brain  need=6400MiB  mode=run  expires in 85888s
              policy: "a mode=run holder whose pid is ALIVE is never reclaimable at any age"
```

**ONE 8 GB CARD. A SEAT LEASE HOLDING 5.5 GB. 1.85 GB FREE.** **The runtime tried to load a 5.8 GB model and
failed, five times, and the harness gave up.**

## AND THE TENANT IS ME

**`owner=llama-swap-brain` is the seat I called all evening.** Every `ask()` in `local_task_compare`, every task
1/2/3 measurement, every sweep — **each one hit the `brain` seat, llama-swap kept the model resident, and the
lease it took is explicitly NOT reclaimable while its pid is alive.** **MY OWN MEASUREMENTS LOCKED OUT THE
EXPERIMENT I WAS SETTING UP.** **The lease says `expires in 85888s` — about 24 hours.**

## THIS IS THE REAL BLOCKER FOR THE PROFILE MOVE, AND IT IS NOT ABOUT THE MODEL

**The Chair's decision 3 was: declare the seat's reasoning setting before any profile moves. This is larger.**

**A profile pointed at the Hermes local runtime does not merely inherit an undeclared setting — it COMPETES FOR
ONE GPU WITH THE LLAMA-SWAP SEATS, and the arbitration is not a queue.** **A `mode=run` lease held by a live
process is never reclaimed, at any age.** So:

- **A cabinet profile pointed at the runtime can be locked out INDEFINITELY by a seat lease another agent holds.**
- **The failure presents as `failed to load` after repeated retries — INDISTINGUISHABLE, from the operator's seat,
  from a broken model or a broken preset.**
- **And it is not a one-time startup race: it recurs whenever a seat is warm.**

**THE CAPACITY QUESTION THEREFORE HAS A PRECONDITION NOBODY HAS STATED: before profiles move, VRAM TENANCY HAS TO
BE DECIDED — which process owns the card, and who yields.** **The model's ability was never going to be the
binding constraint on an 8 GB card with a resident-forever seat policy. It just looked that way because every
measurement so far was on the seat, and the seat was the thing holding the card.**

## WHAT I HAVE NOT ESTABLISHED

**Nothing about the harness.** The run produced no turn, so it says nothing about whether an agent with a system
prompt, tool schemas and its own loop does better or worse than the script. **Branch 4 is Branch 4.** **If it had
failed the way Branch 3 describes — the harness making the model WORSE — that would have been about my framing;
this is about the machine, and I am not going to let the two blur because one of them is more interesting.**

**AND THE FIX IS NOT MINE TO APPLY.** Releasing a seat lease or changing the reclaim policy touches infrastructure
other agents depend on. **It is a decision for the Chair, and it is the next one on this thread.**
