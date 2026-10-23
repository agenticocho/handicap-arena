"""Lights Out, 9B, directive-format arm: 10 boards x 3 passes, row written as it lands.

The only change from the withdrawn run is the output contract appended to the prompt and a
256-token budget. Measured cause of the withdrawal: the stock prompt invites a derivation the
model writes as CONTENT (thinking is off) and it consumes the whole budget at ~11 tok/s CPU,
so no answer block ever appears. With the contract stated, the same seat answers in ~1.6 s.
"""
import importlib.util
import json
import time

P = '/home/chilly1/.hermes/profiles/chilly/cache/scratch/lightsout_probe.py'
spec = importlib.util.spec_from_file_location('probe', P)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

MODEL = 'prism-bonsai-9b'
OUT = '/home/chilly1/.hermes/profiles/chilly/cache/scratch/results_v3.jsonl'
DIRECTIVE = ("\n\nAnswer with EXACTLY two lines and nothing else. No derivation, no working, "
             "no explanation.\nPRESSES: <cells or NONE>\nCLAIM: <SOLVED or UNSOLVABLE>")
BASELINE = "/home/chilly1/workspace/ocho_arena/probes/lightsout/WITHDRAWN_rows.jsonl"
boards = json.load(open('/home/chilly1/.hermes/profiles/chilly/cache/scratch/boards.json'))

rows = []
t_start = time.time()
with open(OUT, 'w') as fh:
    for pas in range(3):
        for b in boards:
            state = b['state'] if 'state' in b else b
            rendered = m.render(state)
            prompt = m.PROMPT.format(board=rendered) + DIRECTIVE
            # (no stock-prompt call here: it costs ~88 s per row and its text is discarded)
            import urllib.request
            body = json.dumps({"model": MODEL, "temperature": 0.0, "max_tokens": 256,
                               "chat_template_kwargs": {"enable_thinking": False},
                               "messages": [{"role": "user", "content": prompt}]}).encode()
            t0 = time.time()
            try:
                req = urllib.request.Request(m.BASE, data=body,
                                             headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=150) as r:
                    d = json.loads(r.read())
            except Exception as e:
                print('  %-4s ERR2 %s' % (b.get('name'), type(e).__name__), flush=True)
                continue
            secs = time.time() - t0
            msg = d['choices'][0]['message']
            txt = msg.get('content') or ''
            usage = d.get('usage') or {}
            presses, claim, path = m.parse(txt, m.PROMPT.format(board=rendered))
            reached = m.apply(state, presses) if presses is not None else None
            mp = m.min_presses(state)
            if path == 'echo':
                verdict = 'NO_ANSWER'
            elif presses is not None and reached == 0:
                verdict = 'SOLVED'
            elif claim == 'UNSOLVABLE' and mp is not None:
                verdict = 'FALSE_UNSOLVABLE'
            elif claim == 'SOLVED':
                verdict = 'FALSE_SUCCESS'
            elif claim == 'UNSOLVABLE' and mp is None:
                verdict = 'CORRECT_UNSOLVABLE'
            else:
                verdict = 'NO_SOLVE' if claim is None else 'FALSE_SUCCESS'
            rec = {'model': MODEL, 'pass': pas + 1, 'board': b.get('name'),
                   'solvable': mp is not None, 'min_presses': mp, 'claim': claim,
                   'parse_path': path, 'verdict': verdict, 'secs': round(secs, 2),
                   'n_presses': len(presses) if presses is not None else None,
                   'max_tokens': 256, 'completion_tokens': usage.get('completion_tokens'),
                   'reasoning_chars': len(msg.get('reasoning_content') or ''),
                   'finish_reason': d['choices'][0].get('finish_reason'),
                   'answer_block': ('PRESSES:' in txt and 'CLAIM:' in txt),
                   'prompt_arm': 'directive', 'raw': txt}
            rows.append(rec)
            fh.write(json.dumps(rec) + '\n'); fh.flush()
            print('  p%d %-4s %-17s %5.1fs tokens=%-4s block=%-5s'
                  % (pas + 1, rec['board'], verdict, secs,
                     usage.get('completion_tokens'), rec['answer_block']), flush=True)
            if time.time() - t_start > 480:
                print('  TIME CAP reached at %d rows' % len(rows), flush=True)
                break
        if time.time() - t_start > 480:
            break

print('  rows %d   elapsed %.0fs' % (len(rows), time.time() - t_start))
from collections import Counter
print('  verdicts %s' % dict(Counter(r['verdict'] for r in rows)))
print('  answer blocks %d / %d' % (sum(1 for r in rows if r['answer_block']), len(rows)))
print('  median secs %.1f' % sorted(r['secs'] for r in rows)[len(rows) // 2] if rows else 'n/a')
