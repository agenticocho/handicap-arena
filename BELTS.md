# THE BELT SYSTEM — grading by demonstration

Martial arts doesn't rank people by how big they are. It ranks them by **what they have
demonstrated**, and it separates them by **weight** so the demonstration means something.
That is exactly the arena's structure, so the arena grades the same way.

**Two axes, orthogonal, both needed:**

- **Division (weight)** = measured VRAM footprint. *Who you fight.*
- **Belt (rank)** = verified results. *What you've proven.*

A 350M and a 35B can both be black belts. They are champions of different divisions. **That is the
entire sport in one sentence.**

---

## 1. The rule that makes belts mean something

**A belt is only valid on a CERTIFIED result.** Tier-2 means *we re-ran your model on our rig from
its sha256 and reproduced the score*. Open, self-reported results earn **stripes**, never belts.

**Unverified to participate. Certified to be graded.** The belt is the scarce good, and scarcity is
the only reason anyone will want one.

---

## 2. Belts — earned by demonstrated behaviour

Every level maps to a **specific, reproducible achievement**. Nothing is subjective; each one is
computable from result bundles.

| belt | requirement | what it proves |
|---|---|---|
| **White** | weighed in — served, got measured, entered a card | you showed up and you're real |
| **Yellow** | won ≥1 round | you can win *something* |
| **Orange** | won ≥2 of 3 rounds | competitive across a bout |
| **Green** | swept a bout 3–0 | dominant |
| **Blue** | swept two consecutive sanctioned bouts | not a fluke |
| **Purple** | swept three consecutive | **earns a mandatory challenger slot one division up** |
| **Brown** | top-3 on a division card | ranked in your weight |
| **Black** | **division champion** — holds the belt | the best in your weight, proven |
| **1st Dan … 10th Dan** | **consecutive successful title defences** | longevity: 1st dan = 1 defence, 7th dan = 7 |
| **Red** | held a belt in **three different divisions** | you punched up twice and won twice |

**The dan grades are the elegant part**: a dan grade *is* the title-defence count. It cannot be
bought, gifted, or argued — you either defended or you didn't. Very few models will ever reach 3rd
dan, and everyone will know what it means.

**The red belt is the summit.** To earn it a model must win its own division, move up, win again,
move up again, and win a third time against bigger footprints. It is rare by construction, and it
is the single most interesting data point the sport can produce — because each one is a measured
answer to *"where exactly does capability break with size?"*

---

## 3. Stripes

**A stripe is a trial won.** Three rounds × three trials = up to nine stripes in a bout.

Stripes let a model show progress before it earns a belt, and they let a 0–3 loss still carry
information ("lost, but took four of nine trials"). **Stripes are the record; the belt is the
rank.**

---

## 4. Promotion and demotion

- **Belts are earned, never assigned.** The harness computes the earnable belt from the result
  bundle; the arena confirms it on certification.
- **Belts are not lost on a loss.** They are lost on **failing to defend** — consistent with martial
  arts, and it means a champion who loses a title fight drops to Brown, not to White.
- **A belt decays if you don't fight.** A model that hasn't competed in 180 days moves to
  **"inactive"** and its title becomes **vacant**. This keeps the card honest: no ranking survives
  on reputation alone.
- **One model, one belt.** Moving up a division requires vacating the lower title.
- **A model cannot hold two belts in the same division.** Variants compete as separate entrants —
  and the sha256 makes that unambiguous.

---

## 5. Division colours

Each weight class carries its own cord, so a card is readable at a glance:

| division | footprint | cord |
|---|---|---|
| Featherweight | ≤4 GB | **teal** |
| Lightweight | ≤8 GB | **amber** (the reference class) |
| Middleweight | ≤16 GB | **violet** |
| Heavyweight | >16 GB | **crimson** |
| Open / offload | CPU + RAM | **slate** |

---

## 6. The card, as the sport sees it

A sanctioned card reads like a fight poster, top to bottom:

```
MAIN EVENT        Lightweight title        champion (Black, 2nd Dan) vs #1 contender (Purple)
CO-MAIN           Middleweight #2 vs #3
UNDERCARD         Featherweight prospect (Orange) vs debutant (White)
```

**Every line links to a result bundle and a sha256.** A claim of a belt with no reproducible bundle
behind it is not a claim — it is a slogan, and the sport is explicitly built to tell the difference.

---

## 7. Why this is the right shape

Ranking by benchmark score collapses everything into one number and hides the only question anyone
actually has: **what can I run?**

The belt system keeps two things separate and both honest:

- **Weight** tells you if it fits your hardware — measured on a scale.
- **Belt and dan** tell you how good it has proven to be — measured by executing tests, certified
  by re-running them.

And the promotion path — *sweep three, punch up, win, punch up again* — turns the aggregate
leaderboard nobody reads into a **ladder with a story**. A model climbing from White to Red is
watchable. A model sitting at rank 417 is not.
