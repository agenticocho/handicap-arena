# WORK ORDER — get at least one model past each cabinet

**For Ocho. From Chilly, at the operator's instruction.** The operator's words: *"have him keep working on
getting at least one model to pass each cabinet. If we don't have the right models in Chilly's zoo, tell me
and I'll download them."*

---

## 1. WHAT CHANGED TONIGHT — READ THIS FIRST, BECAUSE IT REMOVES TWO BLOCKERS

**Both were assumed to be model-capability problems. Neither was.**

### The model path did not exist

`build_bundle` calls `ent().weights_info()` on a BARE entrant. `ModelEntrant.__init__` required
`model_path`. **So `--entrant model` raised `TypeError` before a single prompt — unreachable, not
untested** — and it was shared by every cabinet built from the template, plus `sokoban2`.

**Fixed at the call site** (`cmd_run` already holds the constructed `ent`, so it passes
`weights=ent.weights_info()`), and **the digest now lands in the record**: real sha256, real byte count.

**And note what my first fix did, because it is the lesson:** I made the constructor tolerant instead of
fixing the call site — **which converted a loud crash into a record that said `path: null` while a path had
been supplied.** *A plausible wrong number replacing a refusal to produce one.* The crash was the better
failure.

### The answer format was unwinnable, and no amount of asking fixed it

A real 4B (Qwen3.5-4B-UD-Q4_K_XL) ran end to end. It answered **`{`** — 20 times out of 20 — and the cabinet
correctly refused to score it: **`NO_LEGAL_ACTION_PRODUCED`, exit 2, zero measured.**

The raw answer, captured in the record, was a JSON document with a hallucinated `contract_id`, a
`magnitude`, and this field:

```
"direction": "U D L R ."      <- the model read our alphabet line as a FIELD VALUE
```

**THE LETTER WAS IN THERE. The reader correctly would not open a JSON object** — R3 says one action token
and nothing else, and a reader that guesses is the defect R3 exists for.

**What did NOT work:** the prompt already said *"A word, a number, two letters, or a sentence is not an
answer."* Adding an explicit imperative shape line: no change. `/no_think`: no change.

**What worked, first try:**

```
GBNF grammar on the sampler:
    root ::= "U" | "D" | "L" | "R" | "." | "GIVE UP"

01_first_dig      ->  'GIVE UP'    3 of 3, 4 tokens, stop=True
04_the_only_door  ->  'U'
```

**A sampler constraint is a mechanism; a clearer sentence is a request.** *Ask four times and be ignored;
make it structurally impossible to answer wrongly and get a legal token every time.*

## 2. THE FIRST REAL RESULT — AND IT IS A BAD ONE ABOUT THE MODEL

```
level 01  -- one pearl, one letter, the reference solves it in ONE move   ->  the model GIVES UP
level 04  -- PROVEN UNWINNABLE by exhaustive search                       ->  the model PLAYS 'U'
```

**It abstained on the solvable level and played the provably-lost one.** That is the exact inverse of the
faculty DIG DUG exists to measure. **Caveat: 01 is 3-of-3; 04 is n=1.** But this is the shape of what a
working instrument produces, and it is the first honest model number the Arcade has.

## 3. THE WORK

1. **Put the GBNF grammar into each cabinet's request** — it belongs in the MODEL PATH, not in a note. The
   alphabet is already declared in each prompt; **constrain the sampler to exactly that alphabet and the
   abstention token, and record the grammar string IN THE BUNDLE** so a reader can see what the model was
   allowed to say. *A constraint nobody wrote down is indistinguishable from a model that behaved.*
2. **Then run each cabinet's `model` entrant against a real served model, on the leased 4B and on the
   larger residents**, and report the first readable field per cabinet.
3. **`--reasoning` and `--max-tokens` must both be recorded per run**, and both are now known to matter:
   `--reasoning` is a NO-OP for granite (measured); thinking OFF answered 5/5 where the default produced
   nothing at three token ceilings; and an 8-token cap makes a JSON-prone model emit an opening brace.
4. **The digest fix and the grammar must be re-frozen per cabinet** — the freeze gate fired twice tonight on
   my own edits, refused, and gave exit 6. **Do not bypass it.** Re-freeze, re-run, and expect numbers to
   move.
5. **One caveat I could not close, and will not paper over:** the record's top-level `reasoning` came back
   `None` on the second run and `off` on the first, with the same flag passed. **One of those reads is
   wrong. Find out which.**

## 4. THE MODEL QUESTION — THE OPERATOR'S OFFER, AND MY ANSWER SO FAR

**He has offered to download models. My read: not yet, and here is why.**

**The zoo is deep** — ~37 GGUFs, 350M to 27B, including Ornith-1.5-9B (his resident chief),
Tiel-Inspired-Coder-9B, Qwen3.5-4B, granite-3.3-2B, and several 27B-class. **Availability was never the
constraint:** the two things blocking a real run were a constructor signature and an answer format, and
**both were ours.**

**So: run what we already have first, across a range of sizes, under the grammar.** *A 350M, a 2B, a 4B, a
9B, and a 27B, on one cabinet, is five data points and they cost us nothing.* **That tells us whether the
binding constraint is scale, family, or the cabinet — and only then is a download an informed purchase.**

**If a gap does emerge, the shape it will take is probably not "bigger."** Tonight says the failure modes
are *format* (now mechanically solved) and *spatial/multi-step planning* (which is a family question, not a
size question). **If it is a family question, tell the operator the specific thing we lack — e.g. a model
known for spatial or grid reasoning — not "a better model."**

**Chair's standing position on downloads: propose the gap, name the model, and let the operator buy.** *A
download is a decision about disk and their time; a measurement is the thing that tells them which one.*
