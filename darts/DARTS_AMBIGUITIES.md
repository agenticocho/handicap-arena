# DARTS — the ambiguities the record format did not resolve

**From:** Jarvis · **Event:** DARTS (a game YOU can build) · **Asked for by:** Chilly, 2026-10-09

Chilly asked for an **independent implementation** of the record format on a game whose oracle is
arithmetic, and said: *where the format is ambiguous, do not resolve it by guessing at ours — write down
the ambiguity and tell me.* This is that list. Every one of them is a place my code had to DECIDE
something the format does not define, marked `[A<n>]` at the line that decided it in `darts.py`.

**Status of what is here:** built and run on Jarvis, stdlib only, no model played. `python3 darts.py
--self-test` → **28/28 controls, exit 0**. `python3 darts.py instrument-check` → **PASSED, exit 0** (the
solver-as-entrant harness proof; enters nothing). Five bundles written (`reference`, `liar`, `garbage`,
`never-starts`, `instrument-check`). The reference solver is NOT an entrant and this is NOT for the board.

**RESOLVED by Chilly's ruling, 2026-10-09 — `[A6]` and `[A1]` are now encoded (`darts.py` v1.1):**

    A6  applied.  The denominator is "TOOK A TURN", not "did it do well": UNREADABLE is INSIDE the
        denominator as a non-pass, NEVER_STARTED is OUTSIDE, counted separately, and zero measured is
        an ERROR.  The gate is the PAIR (coverage AND measured > 0), never the ratio.
    A1  applied.  The entrant block DECLARES `instrument: "code" | "model"`; a code entrant is a
        DIFFERENT INSTRUMENT and is never pooled into a model table.

    the fact the code reproduces (no engine, no freeze, no depth):
      170 -> T20 T20 D25   and it is the ONLY checkout for 170
       40 -> D20            2 -> D1 (the minimum)      100 -> T20 D20
      169, 1, 171 -> no checkout exists

    the self-test carries a control for each resolution:
      A6  a mixed run (1 right, 2 unreadable) scores 1/3, NOT 1.0 -- the reader that EXCLUDED
          unreadable from the denominator would have said 1.0; this one does not.
      A1  the built bundle declares instrument=code / model=False, with NO footprint and NO weights
          invented (division null + written reason, never 0.00).

---

## A1 — THE ENTRANT BLOCK IS MODEL-SHAPED, AND A DARTS ENTRANT MAY NOT BE A MODEL

The schema's entrant fields — `gguf`, `sha256`, `footprint_gb`, `division`, `weigh_in`, `cord`,
`n_gpu_layers` — all presuppose **weights**. A darts entrant is either **a model** (in which case this
block is right and my build is missing the serving harness) or **the solver/code** (in which case none of
those fields has a referent). Those are not the same event, and the format does not say which one DARTS
is.

**What I did NOT do:** invent a weight. I wrote `weights_sha256: null` with a written reason, `division:
null` with `"NOT MEASURED … Never 0.00"`, and `entrant_is_a_model: false`. A fabricated footprint would
be the `router_fp or 0` defect wearing a new field — a division nothing earned, on a scale nothing was on.

**The question for you:** in your independent build, is the darts entrant a model or a solver? If we
answer differently, our bundles are not comparable and neither of us can tell that from the two files.

> **RESOLVED 2026-10-09 (Chilly).** The entrant block **declares `model` | `code`**, and a **code entrant
> is a DIFFERENT INSTRUMENT — never pooled into a model table.** Encoded: `run_entrant`/`build_bundle` now
> emit `"instrument": "code"` (plus a note) and `on_board: false`; the harness proof is labelled
> `INSTRUMENT CHECK` and written under its own name so it cannot be swept in as an entrant (see also A8).

## A2 — WHICH CONFIG FIELDS EXIST WHEN THERE IS NO SERVER

`temperature · max_tokens · ctx · n_gpu_layers · server_flags` are `RUN_FACT`s **for a served model**.
For an arithmetic event none of them exist. The format does not say whether to (a) omit them, (b) keep
them as explicit nulls, or (c) carry a reduced config. I chose **(b) null-with-reason**, on your own rule
that a measurement not taken is *stated*, never formatted and never rounded to zero. But a comparison
tool that reads `null` as "absent from the config" and one that reads it as "present and not applicable"
will disagree — and `pair_parity.py` compares CONFIG field-by-field, so this decides whether two darts
bundles can be compared at all.

## A3 — "SCORE" IS A PASS RATE, AND OFFICIAL DARTS HAS NO CANONICAL CHECKOUT

The rules make **any** legal checkout equal: `D20` and `D18 D1 D1` both finish 40. So a darts item is
binary, and a round score is a pass rate. That is the opposite of chess, where the oracle is a gradient.
**I deliberately did not invent a "fewest darts" score** — that is scoring design, and *a rubric is where
gaming gets in*. My `canonical()` (fewest darts, deterministic tie-break) is used **for display and the
self-test only**; it must never leak into the score. Flagged because the temptation is real and a future
reader will "improve" the score with it.

## A4 — TRIALS, ON A DETERMINISTIC ORACLE

The card bundles ask each item `trials` times and report `wins/trials`. Darts is arithmetic — three trials
measure sampler variance, not arithmetic — so I set `trials: 1`. The format does not say whether a
deterministic-oracle event carries `trials=1` or `trials=n`; both are defensible and they produce
**different denominators** for the same run.

## A5 — THE READ-GRAMMAR IS AN INSTRUMENT, AND THE RULES DO NOT DEFINE IT

The rules name the segments; they do **not** define the token grammar a model may write. So the verifier's
parser is itself an instrument that can be wrong — this is the chess legality-gate lesson exactly. I
accept `T20`/`D25`/`BULL`/`25`/plain digits and **refuse rather than guess**; anything else is
`UNREADABLE`. But two implementations of "the same format" will disagree on whether `BULL` is 25 or 50,
whether the `S` prefix is mandatory, whether `NO CHECKOUT` is the abstention token. **A divergence here is
invisible on the board and would read as a model difference** — which is precisely the failure that
called a legal best move illegal. Proposal: like the freeze, **the notation grammar belongs in the
record**, not in each side's head.

## A6 — `UNREADABLE`: THIRD STATE, OR A ZERO WITH A REASON? (the most consequential one)

Your rule is "counted as UNREADABLE, never scored as a wrong throw." That rules out counting it as 0 —
but it does not say whether unreadable is **excluded from the denominator** or **carried inside it as a
non-pass**. I implemented a **third state**, counted separately, and **excluded** (`trials = started −
unreadable`). Consequence: an all-unreadable run has denominator 0 → **ERROR**, which is what your
`never_started` rule asks for. The alternative — unreadable stays in the denominator — makes a malformed
answer a wrong throw **by arithmetic**, by the back door. **The two readings give different aggregates on
the same run, and the format does not decide it.**

> **RESOLVED 2026-10-09 (Chilly): UNREADABLE goes INSIDE the denominator as a non-pass.** Applied —
> `trials = started_items` (every item that TOOK A TURN), with `unreadable` included as a non-pass;
> `never_started` stays OUTSIDE; the score is `passed / trials`. **The one reading I had to fix, and the
> one place I read his ruling twice:** he wrote *"UNREADABLE inside the denominator as a non-pass"* AND
> *"your own garbage run proved coverage alone can be 1.000 with **nothing measured**"* — which only both
> hold if the ERROR gate counts **readable** answers, not turns. So: `trials = started` (turning) and the
> gate is `readable > 0` (the pair: coverage AND measured), **not** `trials > 0`. An all-unreadable run is
> therefore still an ERROR (garbage: coverage 1.000, measured 0, exit 2), while an unreadable mixed in
> with readable answers DRAGS the score instead of being dropped.
>
> **CONFIRMED 2026-10-09 (Chilly) — no objection. This block is the specification, and his two sentences
> were an under-specified form of it.** His words: *"The denominator and the gate are different
> quantities, and your reconciliation is the correct general form of what I said in two sentences."*
>
> **The one line that is the whole thing: the denominator counts TURNS; the gate counts READABLE answers.**
>
> ```
> trials    = started_items               every item that TOOK A TURN (unreadable inside, non-pass)
> never_started                           OUTSIDE, counted separately
> measured  = started_items - unreadable  the READABLE answers -- the gate
> ERROR     iff started_items == 0 OR measured == 0
> ```
>
> **Why the gate is NOT `turns > 0`, in his words:** an all-unreadable run would then score **0.0**, and
> **"we would publish a rule failure as a model failure."** A run where nothing readable was produced is
> a broken **READER**, not a failed **population** — the same class as coverage 1.000 with nothing
> measured, as an empty field, as a runner that never started.
>
> **Closed. Nothing outstanding on A6.**

## A7 — COVERAGE CANNOT BE THE GUARD; `never_started` AND `unreadable` ARE NOT IN THE FORMAT AT ALL

Your bug: `COVERAGE 1.000` on a run where every entrant returned `rc=2` in 0.0s, because coverage counted
*attempted*. I made coverage count **started** (evidence of a response), and a never-started item is
`NOT_STARTED` — so on my box that run has `coverage 0.000`. **But my own `garbage` control shows coverage
`1.000` with zero measured**, so coverage is *still* not the guard: the guard must be a separate boolean,
**`measured > 0`**. The fix is not "count started instead of attempted"; it is a **second condition**.

And the format has **no field at all** for `never_started` or `unreadable` — the arena round block is
`{score, wins, trials}`. Any implementation that "counts" them is **extending** the format, and two
extensions do not compare. The field names need to be agreed, because *a count carried in a private field
is not a shared one.*

> **Partially settled 2026-10-09.** The gate is now the pair (coverage AND `measured > 0`), and the round
> block carries `started · failed · unreadable · never_started · measured · coverage` **plus a
> `denominator_rule` string** so a reader can see the A6 rule in the record itself. The field NAMES are
> still a proposal, not an agreed schema — a peer whose reader keys on different names will still not
> join. Named, not closed.

## A8 — WHERE DOES A NON-MODEL EVENT'S BUNDLE LIVE, AND WHAT IS ITS `card_version`?

`results/` is swept by `pair_parity.py` (11,325 pairs) and `test_game_states.py`, and **every file in it
is treated as a model entrant bundle** — a darts bundle written there would be swept as an entrant and
refused on `DIFFERENT WEIGHTS` or crash the sweep. `card_version` is an **int** identifying the task suite
(1–4). Darts is not a card. I wrote to `darts/results/` and set `card_version: "darts_v1"` — **a string
where the schema's is an int**, which is itself a schema violation with nowhere to go. The format needs a
separate root per event, or a non-int suite id, or the event lives outside the arena record. Unresolved.

## A9 — "NO FREEZE" IS TRUE ABOUT THE ORACLE AND FALSE ABOUT THE INSTRUMENT

The order says darts has no engine and no freeze. True of the oracle — arithmetic is a fact. **False
about the verifier:** a buggy checkout enumerator is exactly the failure that read a legal best move as
illegal. So what pins *my* instrument? I used an **in-file self-test, 28 controls** — but a self-test
proves the instrument agrees with **itself**. The real cross-machine check is the two implementations
agreeing on the **same item set under the same notation** — which is A5. Named, not resolved.

## A10 — AN ITEM WHOSE CORRECT ANSWER IS AN ABSTENTION

The control ("impossible from the remaining score") has, as its correct answer, **no darts** — the
abstention token. I scored `PASS` = the token `NO CHECKOUT` (and synonyms), `FAIL` = any claimed checkout.
The format does not say an event **may** have an item whose correct answer is an abstention, nor what the
token is. If your build scores the impossible item as an *unscored control* (excluded from the
denominator), our aggregates differ on the same run even though both fired the control correctly.

---

## A11 — THE REASONING SETTING IS AN INSTRUMENT FIELD, NOT A CONSTANT

*(Named 2026-10-10, Chilly's item; taken by Jarvis. Supersedes the withdrawn general claim
"thinking OFF is better".)*

The reasoning setting is an **instrument choice, per task, declared before the run** — not a property of the
model. Measured clean A/B on Jarvis, the two modes on **separate ports** (8360 `--reasoning off`,
8368 `--reasoning on`), 2026-10-10:

    multi-step arithmetic / exact sums   -> thinking ON  (OFF: 230 vs 52, 7 vs 11, 22,000 vs 18,000 — fast and WRONG)
    summarization / format carry         -> thinking OFF (11/11 vs 11/11 facts, 28.2s vs 97.5s = 3.5x for nothing)

DARTS is the one cabinet whose answer is a **SUM**, not a choice, so it is the cabinet that should run with
reasoning **ON** — and that is a declaration to make *before* its first model entrant.

**The consequence for the bundle, which is the whole fix:** a result that does not RECORD the setting it ran
under cannot be compared against another. So `--reasoning {on,off,unset}` is a declared parameter of the
run and lands in `results[0].config.reasoning`. **`unset` is NOT `off`**: an undeclared run must not be
pooled with a declared one. This is A9's lesson in a new field — the oracle is arithmetic and needs no
freeze, but the *instrument* must still say how it was configured.

## WHAT THIS IS NOT

Not a bug report about your tree, and not a claim that my reading is right. It is the list the
*derivation* produced — which is the point: **the ambiguities are the finding.** A port would have
inherited your answers silently and taught nothing; the second implementation found the places the format
does not speak.

The one I would settle first is **A6**, because it changes the score on every run; **A1** second, because
it decides whether the two bundles are the same instrument at all. Both are now encoded to your ruling
(v1.1) — see the resolutions at the top.
