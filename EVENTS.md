# EVENT FORMATS — disciplines, teams, and the events that actually answer questions

The single bout produces **one number**, which is precisely the thing that makes global leaderboards
useless. The fix is not a better number. It is **more than one number, and more than one model.**

Two ideas carry the whole event book:

> **A profile beats a score.** A decathlon tells you a model is strong at structured output, weak at
> code, fast, and forgets long context. A rank tells you it is 47th.
>
> **The relay is the real deployment.** Nobody runs one local model for everything. They run a small
> router, a bigger worker, maybe a critic. **The tag team is that architecture, made measurable.**

---

## 1. The event book

| event | format | what it answers |
|---|---|---|
| **Single bout** | 3 rounds, one model | baseline competence, one belt |
| **Cage match** | 2 models, same prompt, blind, deterministic scoring | head-to-head, one round at a time |
| **Biathlon** | accuracy **×** throughput, misses cost time | *the real deployment trade* |
| **Triathlon** | 3 disciplines, may cross divisions | generalist or specialist? |
| **Decathlon** | 10 disciplines, points table | **the profile** |
| **Marathon** | long-context endurance, hundreds of rounds | does attention decay? |
| **Relay / tag team** | N models, baton at defined handoffs | **can chaining beat a single bigger model?** |
| **Team vs team** | line-ups, best-of-N, substitutions between rounds | squad depth |

---

## 2. Biathlon — the event that matters most commercially

Real biathlon: you ski, you shoot, **a miss costs a penalty loop**, and you are ranked on total time
*including* penalties. That is exactly the local-inference trade-off, and nobody measures it.

**Rules**
- **Ski leg** — throughput, measured as mean latency across the round (or tokens/sec).
- **Shoot leg** — accuracy on the round's task, scored by parser/test as always.
- **Penalty** — each failed trial adds a fixed time penalty, set per event in *seconds*:
  `penalty_seconds = k × mean_latency_of_the_round`, `k` declared in the event config.
- **Ranking = total time = skiing time + penalties. Lowest wins.**

**Why this is the right event:** a model that is 4× faster and 20% less accurate should win some
events and lose others, and which one it is depends entirely on `k` — the cost of being wrong. That
is a *real* engineering decision, it is different for every application, and the arena turns it into
a number instead of an argument.

**Worked example from our own Featherweight card** (declared `k = 1.0`, so a miss costs one round's
worth of latency):

| entrant | accuracy | mean latency | misses | ski time | penalties | **total** |
|---|---|---|---|---|---|---|
| LFM2-350M (0.40 GB) | 3/9 | 0.19 s | 6 | 1.71 s | 6 × 0.19 = 1.14 s | **2.85 s** |
| Qwen3.5-2B (1.61 GB) | 6/9 | 8.23 s | 3 | 74.1 s | 3 × 8.23 = 24.7 s | **98.8 s** |

**The 350M wins the biathlon by 35×.** It is *less* accurate and *far* better value, and the single-bout
score of 0.33 vs 0.67 would have told you the opposite story. **Both numbers are true. Only the event
tells you which one applies to your use case.**

---

## 3. Relay / tag team — the event that mirrors production

**The question everyone actually has:** *can I get 8B-quality output on a 4 GB budget by chaining
models?* A relay answers it with a number.

**Rules**
- Each leg is a **round**, run by a declared model. Handoffs are explicit and typed.
- **Leg 1 (router/planner)** may emit a plan or a routing decision rather than an answer.
- **Leg 2 (worker)** receives leg 1's output verbatim as context. **No human editing, no retries.**
- **Leg 3 (critic, optional)** may accept or revise leg 2's answer; the **final** answer is scored.
- **Scoring is identical to a single bout** — same parsers, same executed tests, no judges.
- **A dropped baton is a DNF.** If leg 1 produces nothing usable, the team scores zero. Passing
  garbage downstream is a *failure*, not a recovery.

**Division accounting for teams — the rule that keeps the ladder honest:**

> **A team's division is the SUM of its members' measured footprints.**

A 350M + 2B team competes as a 2.01 GB entry — inside Featherweight, legitimately. But a 2B + 9B
team measures ~7.2 GB and therefore fights in **Lightweight**. **You cannot field three giants and
call yourself a featherweight.** This falls out of measuring on a scale rather than declaring a class,
which is the same reason the weigh-in exists.

**The most valuable relay on the board** is the cheapest one: *does a 350M router + a 2B worker beat
a single 2B?* If chaining helps, that is a finding the entire local community wants and nobody has
measured reproducibly.

---

## 4. Cage match

Two models, same prompt, **blind, deterministic scoring, one winner per round.** No judges, no
criteria, no debate about style.

**The rebuttal variant (the watchable one):** both answer; each is then shown the *other's* answer and
may revise; the **final** answer is scored. That is a genuine exchange — a real MMA round — and it
stays entirely deterministic because only the last output is graded.

**Rejected:** a model judging a model. That is a family member marking the exam, and it is the single
most common way a benchmark becomes worthless.

---

## 5. Decathlon — the profile

Ten disciplines, one card, **points table rather than a pass rate** so a model strong in two events
and hopeless in eight is visibly *specialised* instead of just low-ranked.

Candidate disciplines (each must be deterministically scorable):

1. JSON schema compliance · 2. tool selection · 3. code repair (tests executed) ·
4. long-context needle retrieval · 5. multi-turn constraint retention · 6. refusal calibration
(two error rates, not one score) · 7. arithmetic without a calculator · 8. instruction conflict
resolution · 9. context-window efficiency (correct at the smallest ctx that works) ·
10. throughput

**A decathlon winner is not a champion — it gets a medal.** Belts stay with division title fights.
Otherwise a model with one good day claims a belt it never defended.

---

## 6. Marathon

Long-context endurance: hundreds of rounds, **facts planted at known depths**, scored on **retention
decay across depth and position**. The output is a curve, not a score — and the curve is the finding.
Almost every local model degrades in a characteristic way, and almost nobody can tell you where.

---

## 7. Team vs team

Line-ups of N, best-of-N rounds, **substitutions allowed between rounds but not within one**. Scored
as a series. This is the format that rewards *squad depth* — and it is the one that most resembles how
a serious local deployment actually looks: several models, chosen per job, with a fallback.

---

## 8. How events map to belts

| event type | awards |
|---|---|
| Single bout, title on the line | **belts** and **dan grades** |
| Relay / team | **team belts** — held by the *line-up*, void if the roster changes |
| Decathlon, triathlon, biathlon | **medals** (a profile, not a rank) |
| Cage match | **record** (W/L), no belt unless a title is staked |
| Marathon | **records** per context length |

**Rule:** a belt requires a **division title fight on certified results**. Everything else is a medal
or a record. This is what stops a lucky decathlon from being mistaken for a championship.

---

## 9. Build order

1. **Biathlon** — cheapest to implement, immediately useful, computed from data we already collect.
2. **Relay** — highest value per line of code; answers the community's real question.
3. **Cage match** — trivial once runs are deterministic; it is a scheduling wrapper.
4. **Decathlon** — needs more tasks first; the tasks are the moat, not the event logic.
5. **Team vs team, marathon** — need the submission and certification pipeline to be worth running.
