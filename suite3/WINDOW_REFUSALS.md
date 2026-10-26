# Every block that did not yield a linked row — classified

Counts below are computed from the block records in `suite3/runs/`, not typed.

* REFUSED: **9** — non-zero exit, no row. Nothing was scored.
* EXPECTED non-zero exit with a row: **4** — scored.
* MISFILED: **5** — row written, but this wrapper's block record failed to link the coordinate (my instrument defect; the path is resolved here).
* MISSING: **0** — no row and no explanation.

## REFUSED

### labyrinth / bonsai-9b / cell_01

* record `labyrinth_bonsai-9b_cell01_20261026-135539.meta.json` · started 2026-10-26T13:55:39-0700 · shape suite-served
* **exit 11** after 0.1 s · artifact: none
* it said: `labyrinth_run: exit 11: the model identity card /home/chilly1/workspace/ocho_arena/suite3/runs/labyrinth_identity_bonsai-9b_20261026-135539.json is missing quant; spec §3 makes all four required and none substitutable`
* release: port_closed=True · vram 1789 vs baseline 1789 · :58595 200

### labyrinth / mimo-9b / cell_01

* record `labyrinth_mimo-9b_cell01_20261026-135535.meta.json` · started 2026-10-26T13:55:35-0700 · shape suite-served
* **exit 11** after 0.1 s · artifact: none
* it said: `labyrinth_run: exit 11: the model identity card /home/chilly1/workspace/ocho_arena/suite3/runs/labyrinth_identity_mimo-9b_20261026-135535.json is missing quant; spec §3 makes all four required and none substitutable`
* release: port_closed=True · vram 1789 vs baseline 1789 · :58595 200

### labyrinth / ministral-3b / cell_01

* record `labyrinth_ministral-3b_cell01_20261026-135527.meta.json` · started 2026-10-26T13:55:27-0700 · shape suite-served
* **exit 11** after 0.1 s · artifact: none
* it said: `labyrinth_run: exit 11: the model identity card /home/chilly1/workspace/ocho_arena/suite3/runs/labyrinth_identity_ministral-3b_20261026-135527.json is missing quant; spec §3 makes all four required and none substitutable`
* release: port_closed=True · vram 1789 vs baseline 1789 · :58595 200

### labyrinth / ornith-9b / cell_01

* record `labyrinth_ornith-9b_cell01_20261026-135530.meta.json` · started 2026-10-26T13:55:30-0700 · shape suite-served
* **exit 11** after 0.1 s · artifact: none
* it said: `labyrinth_run: exit 11: the model identity card /home/chilly1/workspace/ocho_arena/suite3/runs/labyrinth_identity_ornith-9b_20261026-135530.json is missing quant; spec §3 makes all four required and none substitutable`
* release: port_closed=True · vram 1789 vs baseline 1789 · :58595 200

### snake / bonsai-9b / None

* record `snake_bonsai-9b_cell_20261026-141354.meta.json` · started 2026-10-26T14:13:54-0700 · shape driver-owned
* **exit 2** after 0.1 s · artifact: none
* it said: `snake_run.py: error: unrecognized arguments: --ngl 99 --ctx 8192 --parallel 1`
* release: port_closed=True · vram 1779 vs baseline 1779 · :58595 200

### snake / mimo-9b / None

* record `snake_mimo-9b_cell_20261026-141352.meta.json` · started 2026-10-26T14:13:52-0700 · shape driver-owned
* **exit 2** after 0.1 s · artifact: none
* it said: `snake_run.py: error: unrecognized arguments: --ngl 99 --ctx 8192 --parallel 1`
* release: port_closed=True · vram 1779 vs baseline 1779 · :58595 200

### snake / mimo-9b / None

* record `snake_mimo-9b_cell_20261026-142424.meta.json` · started 2026-10-26T14:35:02-0700 · shape cpu-only (certified driver: -c 65536 -ngl 0)
* **exit -15** after 638.3 s · artifact: none
* it said: `  loaded in 4.0s   reasoning probe: thinking OFF -- a one-token question answered in a few tokens`
* release: port_closed=False · vram 5911 vs baseline 1790 · :58595 200

### snake / ministral-3b / None

* record `snake_ministral-3b_cell_20261026-141217.meta.json` · started 2026-10-26T14:12:17-0700 · shape driver-owned
* **exit 2** after 0.1 s · artifact: none
* it said: `snake_run.py: error: unrecognized arguments: --ngl 99 --ctx 8192 --parallel 1`
* release: port_closed=True · vram 1779 vs baseline 2143 · :58595 200

### snake / ornith-9b / None

* record `snake_ornith-9b_cell_20261026-141350.meta.json` · started 2026-10-26T14:13:50-0700 · shape driver-owned
* **exit 2** after 0.1 s · artifact: none
* it said: `snake_run.py: error: unrecognized arguments: --ngl 99 --ctx 8192 --parallel 1`
* release: port_closed=True · vram 1779 vs baseline 1779 · :58595 200

## EXPECTED non-zero exit, row scored

* mastermind / bonsai-9b — exit 5: an answered turn inconsistent with feedback — the cabinet documents this as normal for a model (exit_meaning in suite/suite.py) · `mastermind_bonsai-9b_cell_20261026-135235.meta.json`
* mastermind / mimo-9b — exit 5: an answered turn inconsistent with feedback — the cabinet documents this as normal for a model (exit_meaning in suite/suite.py) · `mastermind_mimo-9b_cell_20261026-135043.meta.json`
* mastermind / ministral-3b — exit 5: an answered turn inconsistent with feedback — the cabinet documents this as normal for a model (exit_meaning in suite/suite.py) · `mastermind_ministral-3b_cell_20261026-134808.meta.json`
* mastermind / ornith-9b — exit 5: an answered turn inconsistent with feedback — the cabinet documents this as normal for a model (exit_meaning in suite/suite.py) · `mastermind_ornith-9b_cell_20261026-134840.meta.json`

## MISFILED — the row exists, my block record missed it

* chess / ministral-3b / 2026-10-26T13:47:24-0700 — resolved to `/home/chilly1/workspace/cabinet_results/main/CHESS_GAME_ministral-3b-suite3.json` (written inside the block window) · `chess_ministral-3b_cell_20261026-134724.meta.json`
* snake / bonsai-9b / 2026-10-26T13:59:09-0700 — resolved to `/home/chilly1/workspace/ocho_arena/probes/SNAKE_Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0_s1.json` (written inside the block window) · `snake_bonsai-9b_cell_20261026-135909.meta.json`
* snake / mimo-9b / 2026-10-26T13:57:15-0700 — resolved to `/home/chilly1/workspace/ocho_arena/probes/SNAKE_MiMo-V2.6-Distill-Qwen-9B-Q4_K_M_s1.json` (written inside the block window) · `snake_mimo-9b_cell_20261026-135715.meta.json`
* snake / ministral-3b / 2026-10-26T13:55:43-0700 — resolved to `/home/chilly1/workspace/ocho_arena/probes/SNAKE_Ministral-3-3B-Instruct-2512-UD-Q4_K_XL_s1.json` (written inside the block window) · `snake_ministral-3b_cell_20261026-135543.meta.json`
* snake / ornith-9b / 2026-10-26T13:55:59-0700 — resolved to `/home/chilly1/workspace/ocho_arena/probes/SNAKE_Ornith-1.5-9B-Q4_K_M_s1.json` (written inside the block window) · `snake_ornith-9b_cell_20261026-135559.meta.json`

