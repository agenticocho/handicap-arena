# WORKTREES — the pattern, written down

**Status:** READ, not inferred. Every claim below was re-derived from disk (branch names, worktree
list, file counts). The mechanism was *told* to me by the Chair first-hand; it is written here only
because the disk agrees with it independently.

## What is going on

The arena repo carries **six git worktrees inside itself**, at `.worktrees/`:

    .worktrees/t_643603ee    branch wt/t_643603ee    782 files
    .worktrees/t_9802b2cc    branch wt/t_9802b2cc    783 files
    .worktrees/t_af6fafd9    branch wt/t_af6fafd9    768 files
    .worktrees/t_b439b167    branch wt/t_b439b167    786 files
    .worktrees/t_e0264393    branch wt/t_e0264393    783 files
    .worktrees/t_fbee64a4    branch wt/t_fbee64a4    783 files

**They belong to the kanban board — one worktree per card.** Each `t_` suffix is a **card id**, and
the branch is named for it. The identification is not a guess: `t_b439b167` is the card the Chair
cites for sokoban's `PREREG_sokoban_instrument2.md` (the re-freeze pre-registration), and that
worktree exists here with that exact name.

Each worktree holds a **full checkout** (~780 files — the whole repo, not a slice), which is what
makes them safe as scratch: an agent can run, commit, and even force things in one without the
trunk ever seeing it.

## Why it exists

**So that experiments do not land on the trunk until they are wanted.** A change is made on a card's
branch, reviewed or discarded, and the trunk stays linear and fetchable. The alternative — committing
in place and reverting — puts the experiment in the permanent record, which is a different thing.

The three `cabinet/*` worktrees at `../ocho_arena_cabinets/` are NOT this pattern. Those are
**durable per-cabinet homes** with their own frozen criteria; the `.worktrees/t_*` ones are
**transient per-task scratch**. Same mechanism, opposite intent. Confusing them is how a cabinet's
history gets mistaken for someone's afternoon experiment.

## What this means in practice

- **Do not tidy `.worktrees/`.** They are live card state, not stale leftovers. A missing one means
  a card was closed or abandoned, not that a directory is untracked clutter.
- **A worktree is not a subject.** Reading a run artifact out of `.worktrees/t_*/probes/` finds a
  copy of a file that also exists elsewhere; it is not a second measurement. This directory is the
  single easiest place in the repo to accidentally double-count.
- **The run-of-record line belongs to the trunk, not to a worktree.** If an artifact only exists
  under `.worktrees/`, nothing on the trunk can cite it and no reader will find it.

## Recorded

Written on 2026-10-15 at the Chair's request, after he answered the question I had put to him. The
instinct to write this down rather than leave it implicit is his; the verification is mine.
