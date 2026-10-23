"""Recover the press sets from the raw text in results.jsonl, so the 'distinct press sets'
question can be answered from the record rather than declared unanswerable.

The stored row keeps n_presses but not the cells; it does keep `raw`, so re-parsing it with
the probe's own parser reproduces the cells. The parser's echo guard needs the prompt, which
is rebuilt from boards.json exactly as the run did.
"""
import collections
import importlib.util
import json

F = '/home/chilly1/.hermes/profiles/chilly/cache/scratch/lightsout_probe.py'
spec = importlib.util.spec_from_file_location('probe', F)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

boards = {b['name']: b for b in json.load(open('/home/chilly1/.hermes/profiles/chilly/cache/scratch/boards.json'))}
PATH = '/home/chilly1/.hermes/profiles/chilly/cache/scratch/results.jsonl'

rows = []
with open(PATH) as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get('model') == 'prism-bonsai-9b':
            rows.append(r)

sets = collections.Counter()
recovered = 0
no_parse = 0
for r in rows:
    raw = r.get('raw') or ''
    b = boards.get(r.get('board'))
    if not b or not raw:
        no_parse += 1
        continue
    try:
        presses, claim, path = m.parse(raw, m.PROMPT.format(board=m.render(b['state'])))
    except Exception:
        no_parse += 1
        continue
    if presses:
        key = tuple(sorted(presses))
        sets[key] += 1
        recovered += 1
    else:
        no_parse += 1

print('  rows                      %d' % len(rows))
print('  rows yielding a press set %d' % recovered)
print('  rows yielding none        %d' % no_parse)
print('  DISTINCT PRESS SETS       %d' % len(sets))
for s, n in sets.most_common(20):
    print('    x%d  %s' % (n, ','.join(str(x) for x in sorted(s))))
contain_a1 = sum(1 for s in sets if 'A1' in s)
print('  sets containing A1        %d of %d' % (contain_a1, len(sets)))
