import json, sys
R = '/home/chilly1/workspace/ocho_arena'
d = json.load(open(f'{R}/suite/runs/AGGREGATE.json'))
E = ['ministral-3b', 'ornith-9b', 'mimo-9b', 'bonsai-9b']
tp = {e: json.load(open(f'{R}/suite/runs/throughput_{e}.json')) for e in E}
print("MASTERMIND")
for e, v in d['mastermind'].items():
    s = v['stats']
    print(f"| `{e}` | GPU -ngl 99 | {s['wins']}/16 | {s['answered']} | {s['consistency_pct']}% | {s['distinct_guesses']} | `{s['modal_guess']}` x{s['modal_count']} | {s['no_answer']} | {v['vram']['max_pid']} | {s['rowset_sha256'][:12]} |")
print("\nLIGHTSOUT")
for e, v in d['lightsout'].items():
    s = v['stats']
    print(f"| `{e}` | {s['correct']}/16 | {s['distinct_answers']} | {s['answer_block']} | {s['verdicts']} | {s['tokens_median']} | {s['secs_total']} | {s['out_of_range_boards']} | {v['vram']['max_pid']} |")
print("\nTHROUGHPUT")
for e in E:
    t = tp[e]; c = t['call']; cp = t['compute_path']
    gap = round(100 * (c['server_predicted_tok_per_s'] - c['client_tok_per_s']) / c['server_predicted_tok_per_s'], 1)
    print(f"| `{e}` | {cp['props_model_ftype']} | {c['client_tok_per_s']} | {c['server_predicted_tok_per_s']:.2f} | {gap}% | {c['server_prompt_tok_per_s']:.1f} | {t['vram_pid_mib']} | {cp['serving_process']['start_time']} |")
print("\nIDENTITY")
for e in E:
    cp = tp[e]['compute_path']; sp = cp['serving_process']
    print(e, '| pid', sp['pid'], '|', sp['start_time'], '| bin', sp['binary_size'], sp['binary_mtime'], '| w', sp['weights_size'], sp['weights_mtime'])
print("\nRELEASE")
for cab in ('mastermind', 'lightsout'):
    for e, v in d[cab].items():
        r = v['release']
        print(cab, e, r['port_closed'], r['vram_mib_after'], r['vram_baseline_mib'], r['vram_delta_mib'], r['pid_vram_after'], r['resident_health_after'])
cpu = json.load(open(f'{R}/suite/runs/CPUNGL0_lightsout_bonsai-9b_20261025-131236.meta.json'))
print("\nCPU CONTROL bonsai lightsout ngl", cpu['compute_path']['ngl_flag'], cpu['compute_path']['serving_process']['start_time'])
import collections
rows = [json.loads(l) for l in open(f'{R}/suite/runs/CPUNGL0_lightsout_bonsai-9b_20261025-131236.jsonl')]
ver = collections.Counter(r['verdict'] for r in rows)
raws = collections.Counter((r['raw'] or '').strip() for r in rows)
print('  verdicts', dict(ver), 'distinct', len(raws), 'secs', round(sum(r['secs'] for r in rows), 1),
      'tokens total', sum(r['completion_tokens'] or 0 for r in rows))
print('  top:', [(a.replace(chr(10), ' / ')[:50], n) for a, n in raws.most_common(3)])
print("\nCABINET PROC IDENTITY")
for cab in ('mastermind', 'lightsout'):
    for e, v in d[cab].items():
        m = json.load(open(v['out'].replace('.jsonl', '.meta.json').replace('.json', '.meta.json')))
        sp = m['compute_path']['serving_process']
        print(cab, e, 'pid', sp['pid'], sp['start_time'], 'build', m['compute_path']['build_line'],
              'peak_pid_mib', v['vram']['max_pid'], 'peak_total', v['vram']['max_total'])

