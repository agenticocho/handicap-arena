# Chess instrument report — 2026-10-26

Commit: ddcc1938c186482904fe54545d62f32811f77287.

Controls (all four, run in the same process that produced each row; written output at
`/home/chilly1/workspace/cabinet_results/main/CHESS_CONTROLS_<entrant>.json`):
- control_1_accept_legal_e2e4: PASS (e2e4 resolves to e2e4 on the initial FEN; in the engine's 20-move list).
- control_2_reject_illegal_e4d5: PASS (e4d5 rejected on the initial FEN).
- control_3_count_agrees_with_engine: PASS (reported count equals engine list length for the initial FEN,
  the post-1.e4-e5 FEN, and the black-to-move initial FEN).
- control_4_label_earned: PASS (illegal-move is emitted only after controls 1-3 pass in-process, with a
  recomputed legal list that must equal the one used).

29-vs-20 measurement: `legal_moves(initial)` = 20; after 1.e4 e5 the position has 29 legal moves
(`rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2`); `e4d5` is not in that 29-move
list, so the 29 count is correct for ply 2 and is not a mismatched position. The original 29-vs-20
alarm came from reading the ply-2 row as if its FEN were the initial position.

New rows (staged INSTRUMENT, compute path --ngl 99 --ctx 8192 --cache-type-k/v q8_0 --parallel 1,
private ports, one entrant at a time, global GPU lease released and verified): ministral-3b
illegal-move (ply 0, first line e3); bonsai-9b illegal-move (ply 1, repeated e2e4 as Black);
mimo-9b serving-failure (deliberating, content empty at the 2048-token cap); ornith-9b
serving-failure (deliberating). Old sitting-2 rows are left untouched beside them.

What the cabinet still cannot separate: a model that is still deliberating at the token cap from a
model that committed no move (both surface as serving-failure with no move_uci); and an
illegal-move verdict from a scored capability, because illegal-move is not in CARD_chess.md's frozen
taxonomy. The instrument also cannot recover a move from `reasoning_content` without inventing a
decision, so those rows carry no move.