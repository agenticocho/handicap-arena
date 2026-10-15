# WORKTREES — the pattern, written down

**Status:** CORRECTED 2026-10-15 after the Chair answered first-hand. The first version of this file
inferred live card state from branch names; **that inference was wrong** and the correction is kept
in full rather than quietly overwritten, because a document that quietly rewrites itself destroys the
evidence that it was ever wrong.

## What is going on

The arena repo carries **six git worktrees inside itself**, at `.worktrees/`, branch `wt/<task-id>`:

    .worktrees/t_643603ee · t_9802b2cc · t_af6fafd9 · t_b439b167 · t_e0264393 · t_fbee64a4

**They belong to the kanban board — one worktree per task.** And per the Chair, who knows first-hand
because two of them are his from today: **they are DEBRIS. Stale, and PRUNABLE.** `t_af6fafd9` still
sits at `125b7e2` long after its task completed.

Each holds a full checkout (~780 files — the whole repo, not a slice), which is what makes them safe
as scratch while a task is live.

## What this means in practice

- **They are NOT a pattern to follow.** The deliberate pattern in this repo is the three
  `cabinet/*` worktrees at `../ocho_arena_cabinets/` **and nothing else**. Twelve worktrees total =
  3 deliberate + 2 scratch branches + 6 board debris + the arena root.
- **They are prunable.** An earlier version of this file said "do not tidy `.worktrees/`" and called
  them live card state. That was an inference from branch names and it was wrong. A completed task's
  worktree can go.
- **A worktree is not a subject.** Reading a run artifact out of `.worktrees/t_*/probes/` finds a
  *copy* of a file that also exists elsewhere; it is not a second measurement. This directory is the
  single easiest place in the repo to accidentally double-count — and it is worse than it looks,
  because the copies live at *different commits*, so a digest taken there may be of a stale version.
- **The run-of-record line belongs to the trunk.** If an artifact only exists under `.worktrees/`,
  nothing on the trunk can cite it and no reader will find it.

## Recorded

Written 2026-10-15 at the Chair's request. **First version was wrong**: it read "one worktree per
card" off branch names and concluded they were live state to be preserved. The Chair's first-hand
answer — debris, prunable — is the correction, and the error is kept here because the *mechanism* was
right and the *inference from it* was not. That is the same failure this repo collected four other
instances of today: a true reading of one thing, reported as a fact about another.

