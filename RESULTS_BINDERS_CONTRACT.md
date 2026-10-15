# THE RESULTS WRITE CONTRACT — where a writer writes, where a reader reads, and where both REFUSE

Declared **once**, in `cabinet_root.py`, and landed with the migration of the 22 `<worktree>/results`
binders (card `t_fdf55800`, ruling `DECISION_results_binder_era.md`, sha256 `55bea450…`).

**WHY THIS FILE IS AT THE ROOT AND NOT IN `results/README.md`.** `results/README.md` is TRACKED and
inside the legacy record: editing it changes the tree object `0bcaaa0188b35f0bdd17e3ca824a977cac2d94a1`
that makes the four `results` trees copies-of-one, and `test_declared_root.py` check 6 fails — the very
declaration the writers depend on. A contract line about the record cannot be written *into* the record.

## THE TWO SCOPES, AND NOTHING ELSE

| role | scope | call |
|---|---|---|
| reader of the record | the DECLARED DOMAIN | `cabinet_root.domain()` / `domain_paths(pattern)` / `domain_find(*parts)` |
| writer of a result | ONE PATH, OR A REFUSAL | `cabinet_root.results_dir()` — never a fallback |

A reader's scope is a LIST, not a walk, and the count it contributed is printed with it (`  scope  …`):
a count without its scope is not a count. A writer resolves its destination **once, at the point of
use**; `cabinet_root.Refusal` is a `SystemExit`, so it exits non-zero, names the remedy, and writes
**nothing** — a caught refusal is a fallback with better manners.

## WHERE EACH WRITER WRITES, AFTER THIS LANDING

| writer | destination | state |
|---|---|---|
| `run_card.py` | `results_dir()` | landed (`t_af6fafd9`, `125b7e2`) |
| `annotate_superseded.py` | `results_dir()/supersessions` | landed (`t_fdf55800`, `2528a48`) |
| `canonicalise_filenames.py` | rewrites ONLY inside `results_dir()`; the legacy-record bytes are never a target | landed (`t_fdf55800`, `73b680f`) |
| `chess_game.py` | `results_dir()` | landed (`t_fdf55800`, `16381bc`) |
| `depth_test.py`, `depth_test2.py` | `results_dir()/depth` | **DECIDED, NOT LANDED** — `t_86fa52a2`; their `OUT` still names the legacy record by ABSOLUTE literal |
| `darts/darts.py` | `results_dir()/darts` | **DECIDED, NOT LANDED** — `t_86fa52a2`; `--out` still defaults into `<worktree>/darts/results` |

The two rows marked **DECIDED, NOT LANDED** are decisions of the Chair, carried in
`RESULTS_BINDERS_MANIFEST.json` as `deferred:t_86fa52a2`. They are named here so that a reader of this
contract is not told a destination the code does not yet resolve to.

## NO NEW WRITE LANDS IN A GIT TREE

`results_dir()` resolves to `<declared ROOT>/<this worktree's cabinet>`, where the root comes from
`git config --local arena.cabinetResults` (carried by the git COMMON dir, outside every worktree) or
`CABINET_RESULTS` for one invocation. It **REFUSES** when there is no declaration, when the root
resolves inside a git working tree, or when it resolves inside the repository's git directory. The
legacy record is **DECLARED IN PLACE** and is not written by anything after this landing; the three
duplicate copies under the cabinets are declared copies, not a second record.

Check it, rather than believe it:

```
python3 scripts/list_results_binders.py .     # residue by destination, in any form; exit non-zero while > 0
python3 test_declared_root.py                 # the declarations' own controls; exit 0 in all four trees
```
