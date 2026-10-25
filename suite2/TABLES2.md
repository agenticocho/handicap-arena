<!-- TABLE:sokoban -->
| entrant | compute path | L1 one_push | L2 two_boxes | L3 corner_waiting | moves L1/L2/L3 | not_an_action L1/L2/L3 | blocked L1/L2/L3 | RESIGN at | gen tokens | wall s | peak pid VRAM | release |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bonsai-9b | -ngl 99 · ctx 4096· PQ2_0 - 2.13 bpw (group 128) · slots 1 · build b10777-e3de71522 · pid 2373068 start 2026-10-25T13:41:08-0700 | SOLVED | no (gave_up) | no (gave_up) | 1/4/3 | 0/0/0 | 0/6/5 | —/10/8 | 2/536/173 | 4.9/14.0/9.1 | 2560/2560/2560 | ok |
| mimo-9b | -ngl 99 · ctx 4096· Q4_K - Medium · slots 1 · build b10931-3057bb66c · pid 2371030 start 2026-10-25T13:38:40-0700 | no (commands_exhausted) | no (commands_exhausted) | no (commands_exhausted) | 0/2/3 | 40/38/37 | 0/0/0 | —/—/— | 2560/2312/2374 | 50.2/44.9/50.7 | 5466/5466/5466 | ok |
| ministral-3b | -ngl 99 · ctx 4096· Q4_K - Medium · slots 1 · build b10931-3057bb66c · pid 2368481 start 2026-10-25T13:35:55-0700 | SOLVED | no (commands_exhausted) | no (commands_exhausted) | 1/1/1 | 0/39/39 | 0/0/0 | —/—/— | 2/2523/2512 | 4.5/22.9/22.9 | 2744/2744/2744 | ok |
| ornith-9b | -ngl 99 · ctx 4096· Q4_K - Medium · slots 1 · build b10931-3057bb66c · pid 2369407 start 2026-10-25T13:36:51-0700 | SOLVED | no (commands_exhausted) | no (gave_up) | 1/0/1 | 0/40/2 | 1/0/0 | —/—/3 | 4/2560/802 | 15.5/58.7/32.2 | 5250/5250/5250 | ok |

<!-- TABLE:zork -->
| entrant | compute path | L1 the_floor | L2 long_crawl | parsed L1/L2 | unparsed L1/L2 | impossible L1/L2 | replay audit | gen tokens L1/L2 | wall s | release |
|---|---|---|---|---|---|---|---|---|---|---|
| bonsai-9b | -ngl 99 · ctx 4096· PQ2_0 - 2.13 bpw (group 128) · slots 1 · build b10777-e3de71522 · pid 2377692 start 2026-10-25T13:47:27-0700 | ESC (escaped) | no (gate_locked) | 3/14 | 0/1 | 0/3 | True/True | 7/44 | 5.4/11.8 | ok |
| mimo-9b | -ngl 99 · ctx 4096· Q4_K - Medium · slots 1 · build b10931-3057bb66c · pid 2377328 start 2026-10-25T13:46:56-0700 | ESC (escaped) | INSTRUMENT-FAILURE (replay) | 6/9 | 0/0 | 10/11 | True/False | 43/55 | 14.7/14.2 | ok |
| ministral-3b | -ngl 99 · ctx 4096· Q4_K - Medium · slots 1 · build b10931-3057bb66c · pid 2376609 start 2026-10-25T13:46:04-0700 | ESC (escaped) | INSTRUMENT-FAILURE (replay) | 3/12 | 0/3 | 2/5 | True/False | 21/242 | 5.3/7.3 | ok |
| ornith-9b | -ngl 99 · ctx 4096· Q4_K - Medium · slots 1 · build b10931-3057bb66c · pid 2376845 start 2026-10-25T13:46:18-0700 | ESC (escaped) | ESC (escaped) | 2/7 | 0/0 | 2/0 | True/True | 11/16 | 17.5/18.5 | ok |

<!-- TABLE:snake -->
| entrant | compute path | seed | apples | deaths | ticks | ended | distinct moves | modal move | state-chain digest | wall s | release |
|---|---|---|---|---|---|---|---|---|---|---|---|
| bonsai-9b | -ngl 99 · ctx 8192· PQ2_0 - 2.13 bpw (group 128) · slots 1 · build b10777-e3de71522 · pid 2391798 start 2026-10-25T14:05:02-0700 | 1 | 0 | 0 | 120 | tick_cap | R | R ×120 | 7f46665eb1a91edf | 49.0 | ok |
| bonsai-9b | -ngl 99 · ctx 8192· PQ2_0 - 2.13 bpw (group 128) · slots 1 · build b10777-e3de71522 · pid 2391798 start 2026-10-25T14:05:02-0700 | 7 | 0 | 0 | 120 | tick_cap | R | R ×120 | 7f46665eb1a91edf | 49.0 | ok |
| mimo-9b | -ngl 99 · ctx 8192· Q4_K - Medium · slots 1 · build b10931-3057bb66c · pid 2385769 start 2026-10-25T13:57:52-0700 | 1 | 0 | 0 | 120 | tick_cap | R,U | R ×81 | 235d7cddceebd6bc | 133.0 | ok |
| mimo-9b | -ngl 99 · ctx 8192· Q4_K - Medium · slots 1 · build b10931-3057bb66c · pid 2385769 start 2026-10-25T13:57:52-0700 | 7 | 0 | 0 | 120 | tick_cap | R,U | R ×81 | 235d7cddceebd6bc | 133.0 | ok |
| ministral-3b | -ngl 99 · ctx 8192· Q4_K - Medium · slots 1 · build b10931-3057bb66c · pid 2379866 start 2026-10-25T13:50:29-0700 | 1 | 0 | 0 | 120 | tick_cap | R | R ×120 | 7f46665eb1a91edf | 16.3 | ok |
| ministral-3b | -ngl 99 · ctx 8192· Q4_K - Medium · slots 1 · build b10931-3057bb66c · pid 2379866 start 2026-10-25T13:50:29-0700 | 7 | 0 | 0 | 120 | tick_cap | R | R ×120 | 7f46665eb1a91edf | 16.3 | ok |
| ornith-9b | -ngl 99 · ctx 8192· Q4_K - Medium · slots 1 · build b10931-3057bb66c · pid 2384124 start 2026-10-25T13:55:57-0700 | 1 | 0 | 0 | 120 | tick_cap | D,R,U | U ×94 | 32d9bf1e3a4be462 | 113.7 | ok |
| ornith-9b | -ngl 99 · ctx 8192· Q4_K - Medium · slots 1 · build b10931-3057bb66c · pid 2384124 start 2026-10-25T13:55:57-0700 | 7 | 0 | 0 | 120 | tick_cap | D,R,U | U ×94 | 32d9bf1e3a4be462 | 113.7 | ok |

<!-- TABLE:labyrinth -->
| entrant | compute path | plies / cap | end state | moved | blocked | not_an_action | give_up | visited positions | visited names | turn cap | tokens | wall s | release |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bonsai-9b | -ngl 99 · ctx 8192· PQ2_0 - 2.13 bpw (group 128) · slots 1 · build b10777-e3de71522 · pid 2395883 start 2026-10-25T14:09:32-0700 | 40/40 | cap | 40 | 0 | 0 | 0 | 2 | 2 | 32 | 120 | 5.2 | ok |
| mimo-9b | -ngl 99 · ctx 8192· Q4_K - Medium · slots 1 · build b10931-3057bb66c · pid 2395745 start 2026-10-25T14:09:21-0700 | 40/40 | cap | 40 | 0 | 0 | 0 | 4 | 4 | 32 | 146 | 6.9 | ok |
| ministral-3b | -ngl 99 · ctx 8192· Q4_K - Medium · slots 1 · build b10931-3057bb66c · pid 2395485 start 2026-10-25T14:09:00-0700 | 40/40 | cap | 1 | 39 | 0 | 0 | 2 | 2 | 32 | 160 | 1.5 | ok |
| ornith-9b | -ngl 99 · ctx 8192· Q4_K - Medium · slots 1 · build b10931-3057bb66c · pid 2395565 start 2026-10-25T14:09:04-0700 | 40/40 | cap | 40 | 0 | 0 | 0 | 2 | 2 | 32 | 120 | 6.7 | ok |

<!-- TABLE:chess -->
| entrant | compute path | termination | premature collapse | miscalibrated persistence | plies in lost positions | plies | cap | prompt digest | wall s | release |
|---|---|---|---|---|---|---|---|---|---|---|
| bonsai-9b | -ngl 99 · ctx 4096· PQ2_0 - 2.13 bpw (group 128) · slots 1 · build b10777-e3de71522 · pid 2400963 start 2026-10-25T14:13:31-0700 | illegal-move | 0 | 0 | 0 | 1 | 30 | 76fa8848e9adf514 | 22.8 | ok |
| mimo-9b | -ngl 99 · ctx 4096· Q4_K - Medium · slots 1 · build b10931-3057bb66c · pid 2400694 start 2026-10-25T14:13:18-0700 | illegal-move | 0 | 0 | 0 | 2 | 30 | 76fa8848e9adf514 | 11.7 | ok |
| ministral-3b | -ngl 99 · ctx 4096· Q4_K - Medium · slots 1 · build b10931-3057bb66c · pid 2398618 start 2026-10-25T14:11:40-0700 | illegal-move | 0 | 0 | 0 | 1 | 30 | 76fa8848e9adf514 | 4.6 | ok |
| ornith-9b | -ngl 99 · ctx 4096· Q4_K - Medium · slots 1 · build b10931-3057bb66c · pid 2398800 start 2026-10-25T14:11:46-0700 | serving-failure | 0 | 0 | 0 | 5 | 30 | 76fa8848e9adf514 | 91.8 | ok |

<!-- TABLE:cpu -->
| preserved artifact (suite/runs/published_cpu/) | sha256 (provenance file) | its own primary fields |
|---|---|---|
| SNAKE_Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0_s1.json | see .provenance.json | ended=tick_cap, moves=['R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R'], not_an_action=0 |
| SNAKE_Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0_s1.json.provenance.json | see .provenance.json |  |
| SNAKE_Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0_s7.json | see .provenance.json | ended=tick_cap, moves=['R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R'], not_an_action=0 |
| SNAKE_Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0_s7.json.provenance.json | see .provenance.json |  |
| SOKOBAN_MiMo-V2.6-Distill-Qwen-9B-Q4_K_M_02_two_boxes.json | see .provenance.json | solved=False, ended=commands_exhausted, moves=1, blocked=0, not_an_action=39, give_up=0 |
| SOKOBAN_MiMo-V2.6-Distill-Qwen-9B-Q4_K_M_02_two_boxes.json.provenance.json | see .provenance.json |  |
| SOKOBAN_MiMo-V2.6-Distill-Qwen-9B-Q4_K_M_03_the_corner_waiting.json | see .provenance.json | solved=False, ended=commands_exhausted, moves=3, blocked=0, not_an_action=37, give_up=0 |
| SOKOBAN_MiMo-V2.6-Distill-Qwen-9B-Q4_K_M_03_the_corner_waiting.json.provenance.json | see .provenance.json |  |
| SOKOBAN_Ministral-3-3B-Instruct-2512-UD-Q4_K_XL_01_one_push.json | see .provenance.json | solved=True, ended=solved, moves=1, blocked=0, not_an_action=0, give_up=0 |
| SOKOBAN_Ministral-3-3B-Instruct-2512-UD-Q4_K_XL_01_one_push.json.provenance.json | see .provenance.json |  |
| SOKOBAN_Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0_01_one_push.json | see .provenance.json | solved=True, ended=solved, moves=1, blocked=0, not_an_action=0, give_up=0 |
| SOKOBAN_Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0_01_one_push.json.provenance.json | see .provenance.json |  |
| SOKOBAN_Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0_02_two_boxes.json | see .provenance.json | solved=False, ended=gave_up, moves=4, blocked=6, not_an_action=0, give_up=1 |
| SOKOBAN_Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0_02_two_boxes.json.provenance.json | see .provenance.json |  |
| SOKOBAN_Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0_03_the_corner_waiting.json | see .provenance.json | solved=False, ended=gave_up, moves=3, blocked=5, not_an_action=0, give_up=1 |
| SOKOBAN_Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0_03_the_corner_waiting.json.provenance.json | see .provenance.json |  |
| ZORK_Ministral-3-3B-Instruct-2512-UD-Q4_K_XL_zork_01_the_floor.json | see .provenance.json | ended=escaped, finished=True, carried_required_item=True |
| ZORK_Ministral-3-3B-Instruct-2512-UD-Q4_K_XL_zork_01_the_floor.json.provenance.json | see .provenance.json |  |

