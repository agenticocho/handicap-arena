# FINDING 008 — the greedy parser understated 9 items, and the correction flips criterion 2

Criterion 2 of CARD_v3.md needs >=4 entrants below 0.34. On the RECORDED scores there were 6
(PASS). On the CORRECTED scores there are 3 (FAIL). The bar is unmoved; the input was corrected.

Cause: `_first_json` parses with a greedy `\{.*\}` -- first brace to last -- so a model that
reasons first and emits JSON second is scored `unparseable`. With the raw output now stored in
the bundle, every failing item was re-parsed with a strict extractor and re-scored with the
arena's own scorer. 15 items were scored unparseable; 14 raws contain an object; 9 score higher.

THE THREE THAT CROSSED, which is the whole flip:

```
  stablelm-2-zephyr-1.6b      0.3333 -> 0.5000   crossed above
  LFM2.5-1.2B-Thinking-BF16   0.0000 -> 0.5833   crossed above   <- 0.0 was ENTIRELY the parser
  Qwen3.5-2B-UD-Q4_K_XL       0.3333 -> 0.6667   crossed above
  LFM2-350M-Math-Q4_K_M       0.0000 -> 0.2917   stayed below
  LFM2-350M-Extract-Q4_K_M    0.3333 -> 0.3333   stayed below
  granite-3.3-2b-instruct     0.1667 -> 0.1667   stayed below
```

Note the shape of the understatement: on two entries the parser accounted for the ENTIRE score
(0.0000 recorded). This was not a rounding correction. An entry scored 0.0 that is actually 0.58
was reported as a model that could not answer at all.

TWO entries were also recorded as `TRUNCATED at max_tokens (3000)` while their stored raw contains
a COMPLETE JSON object -- so the truncation verdict was wrong for the same reason: the object was
there and the extractor could not reach it.

## The full row-by-row table (the audit trail; compare against any independent re-score)

```
38 entries with R1_fencing

entry                                           n  recorded  corrected  below0.34
granite-3.3-2b-instruct-critical-thinking.Q5_K  6    0.1667     0.1667  <-- R <-- C
LFM2-350M-Math-Q4_K_M_cardv3_autofit_neutral_c  6    0.0000     0.2917  <-- R <-- C
LFM2-350M-Extract-Q4_K_M_cardv3_autofit_neutra  6    0.3333     0.3333  <-- R <-- C
LFM2-1.2B-Extract-Q4_K_M_cardv3_autofit_neutra  6    0.5000     0.5000        
stablelm-2-zephyr-1_6b-Q4_K_M_cardv3_autofit_n  6    0.3333     0.5000  <-- R 
LFM2.5-1.2B-Thinking-BF16_cardv3_autofit_neutr  6    0.0000     0.5833  <-- R 
Cloudflare_clef-Q4_K_M_cardv3_autofit_neutral_  6    0.6667     0.6667        
Cyber-Ornith-1.5-9B-OBLITERATED-Q4_K_M_cardv3_  6    0.6667     0.6667        
LFM2.5-1.2B-Instruct-Q6_K_cardv3_autofit_neutr  6    0.6667     0.6667        
LFM2.5-VL-1.6B-Q4_0_cardv3_autofit_neutral_ctx  6    0.6667     0.6667        
LFM2.5-VL-1.6B-Q8_0_cardv3_autofit_neutral_ctx  6    0.6667     0.6667        
LFM2.5-VL-1.6B-UD-Q8_K_XL_cardv3_autofit_neutr  6    0.6667     0.6667        
Llama-3.2-3B-Instruct-Q4_K_M_cardv3_autofit_ne  6    0.6667     0.6667        
Qwen3-VL-2B-Instruct-1M-UD-Q4_K_XL_cardv3_auto  6    0.6667     0.6667        
Qwen3.5-2B-UD-Q4_K_XL_cardv3_autofit_neutral_c  6    0.3333     0.6667  <-- R 
apertus-8b-financial-reasoner-v1.Q4_K_M_cardv3  6    0.6667     0.6667        
BTL-4-IQ2_XXS_cardv3_autofit_neutral_ctx8192_m  6    0.8333     0.8333        
Cyber-Tiel-Coder-35B-A3B-MTP-UD-Q4_K_XL_cardv3  6    0.8333     0.8333        
Meta-Llama-3.1-8B-Instruct-Q4_K_M_cardv3_autof  6    0.8333     0.8333        
Ministral-3-3B-Instruct-2512-UD-Q4_K_XL_cardv3  6    0.8333     0.8333        
OrcaSAQ-2-27B-Uncensored_cardv3_autofit_neutra  6    0.8333     0.8333        
Phi-3.5-mini-instruct-Q4_K_M_cardv3_autofit_ne  6    0.8333     0.8333        
Qwen3-1.7B-Q8_0_cardv3_autofit_neutral_ctx8192  6    0.8333     0.8333        
Qwen3.5-4B-UD-Q4_K_XL_cardv3_autofit_neutral_c  6    0.8333     0.8333        
Qwen3.5-9B-UD-Q4_K_XL_cardv3_autofit_neutral_c  6    0.8333     0.8333        
SmolLM3-3B-128K-UD-Q4_K_XL_cardv3_autofit_neut  6    0.8333     0.8333        
Fastino-Nemotron-Finance-IQ4_NL-stream_cardv3_  6    1.0000     1.0000        
MiMo-V2.6-Distill-Qwen-9B-Q4_K_M_cardv3_autofi  6    1.0000     1.0000        
Ornith-1.5-35B-A3B-Abliterated-TIEL_Calibrated  6    1.0000     1.0000        
Ornith-1.5-9B-Q4_K_M_cardv3_autofit_neutral_ct  6    1.0000     1.0000        
Qwen3.5-9B-Q4_K_M_cardv3_autofit_neutral_ctx81  6    1.0000     1.0000        
Qwythos-9B-Claude-Mythos-5-1M-MTP-Q4_K_M_cardv  6    1.0000     1.0000        
Spark-X2.5-4B-Q4_K_M_cardv3_autofit_neutral_ct  6    1.0000     1.0000        
Spark-X2.5-4B-Q5_K_S_cardv3_autofit_neutral_ct  6    1.0000     1.0000        
Tiel-Coder-35B-A3B-MTP-UD-Q4_K_XL_cardv3_autof  6    1.0000     1.0000        
Tiel-Coder-35B-A3B-UD-Q4_K_XL_cardv3_autofit_n  6    1.0000     1.0000        
Tiel-Inspired-Coder-9B-UD-Q4_K_M_cardv3_autofi  6    1.0000     1.0000        
Triumvirate-Qwopus-MiMo-Ornith-9B-Coder.i1-Q4_  6    1.0000     1.0000        

recorded below 0.34 : 6
corrected below 0.34: 3   <- criterion 2 needs >= 4
entries sitting exactly ON the bound: 0 []
```

## Method

Recomputed from the bundles by a second, from-scratch script (own strict extractor, own loop, no
import of evaluate_v3.py) and cross-checked against evaluate_v3.py. Both give 6 -> 3. No entry
sits exactly on the 0.34 bound, so the comparison is not boundary-sensitive.

The parser is NOT fixed in v3 -- a scoring-method change belongs to its own version with its own
pre-frozen bar. v4 carries the fix and fresh criteria.
