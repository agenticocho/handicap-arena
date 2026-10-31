# Contributors

This repository is the record of **The Handicap Arena**: cabinet-sized tasks for local models, run on
consumer hardware under a GPU tenancy rule, where the instrument that scores a game has to be
certifiable before any model number is believed.

It was built at two sites, by two Chairs and the agents each of them runs.

## Site 1 — `chilly` (Linux, Ubuntu 26.04, Ryzen 5 5600, RTX 3060 Ti 8 GB)

The working site. It hosts the cabinets, the harnesses, the GPU windows and the measurement discipline
that most of the findings describe. Commits appear under several identities because the work was done
by the Chair and by the agents it dispatches — `Handicap Arena` is the automated worker identity, and
`chilly`, `Chilly`, `tiel`, `ocho` and `ocho2` are the named agents and their sessions.

Responsibilities: the cabinet harnesses and their drivers, the frozen prompts and scorers, the GPU
lease and window sequencing, the instrument audits, the FINDINGS written up here, and the ruling set
that decides what a number is allowed to claim.

## Site 2 — the peer Chair, macOS (`Jarvis`)

Four commits, all on the instrument side, all reproduced or adopted here after review rather than
accepted on trust:

| commit | what it is |
|---|---|
| `0aa79b4` | the state side of the binding contract — a derived schema, nine rules and nine controls |
| `5cf1125` | DARTS v1.1 — encoding A6 and A1, plus the instrument-check harness |
| `82d56fc` | FINDING 011 — the card's GPU failure has two modes; a power cycle clears the hang, not the driver defect |
| `414e0c0` | the correction to FINDING 011 — the cure is 615.71.09, not 580; one sample had been read as a series |

## What is genuinely joint

Two things here are not one site quoting the other:

1. **A cross-box agreement at the instrument layer.** The Mastermind run produced the same rowset
   digest on both machines before any model number was trusted. Two boxes that agree on the rows and
   *then* compare scores are doing something different from two boxes comparing scores.
2. **Two independent implementations of the render format.** The same output format was written twice,
   independently, which is why a disagreement between them is evidence rather than a bug report.

## A note on what this repository is not

It is a working record, not a polished release. Absolute paths from the measuring machine appear
throughout the artifacts — that is provenance, not decoration: a result you cannot re-derive on the
box that produced it is a story. One tailnet address was removed from `FINDINGS/011` before this
repository was made readable; the historical blobs still contain it, because rewriting history would
invalidate every commit hash cited in the correspondence that produced these findings.

No credentials, tokens or keys appear anywhere in this repository or its history.
