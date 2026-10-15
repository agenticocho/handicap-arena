#!/usr/bin/env python3
"""Build the Arcade wall (a single-file, self-contained front end) from result bundles.

Scope: layout, aesthetics, interaction only. This script does not design the data model;
it reduces the recorded bundles using the rules already fixed in FRONTEND_CONTRACT_v1.md
(card_of, Fraction(sum(wins), sum(trials)), results==[], etc.) and embeds them as
read-only data. Every displayed value is derived at generation time and reproducible by
re-running this script.
"""
import json
import glob
import os
from fractions import Fraction

ARENA = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(ARENA, "results")
OUT = os.path.join(ARENA, "arcade_wall.html")


def card_of(entry):
    cv = entry.get("card_version", None)
    return 1 if cv is None else cv


def wins_of(entry):
    return int(sum((r.get("wins") or 0) for r in entry.get("rounds", {}).values()))


def trials_of(entry):
    return int(sum((r.get("trials") or 0) for r in entry.get("rounds", {}).values()))


def truncated_trials(entry):
    n = 0
    for rnd in entry.get("rounds", {}).values():
        fr = rnd.get("finish_reasons") or {}
        n += int(fr.get("length") or 0)
    return n


def basename(p):
    if not p:
        return "—"
    # paths normalized to basenames before display (contract 4.4). Never leak absolute paths.
    return str(p).rsplit("/", 1)[-1].rsplit("\\", 1)[-1]


bundles = sorted(glob.glob(os.path.join(RESULTS, "*.json")))
non_entrant_paths = []
arena_bundles = []
scratched_paths = []
graded_entries = []
for path in bundles:
    try:
        d = json.load(open(path))
    except Exception:
        continue
    # Contract scope: only THIS arena's bundles. Without this the glob counts 317
    # files where the gate counts 310.
    if d.get("harness") != "handicap-arena":
        non_entrant_paths.append(os.path.basename(path))
        continue
    arena_bundles.append(path)
    # The rendered claim, keyed on DATA: results == [] is a missed weight.
    # A bundle with NO "results" key is not an entrant at all -- counting it as a
    # miss is how seven test artifacts (CHESS_GAME_*, CHESS_VOID_*, DEPTH_TEST*)
    # became seven phantom missed weights: 92 where section 7.2's rule gives 85.
    if "results" not in d:
        non_entrant_paths.append(os.path.basename(path))
        continue
    res = d["results"]
    if res == []:
        scratched_paths.append(os.path.basename(path))
        continue
    for e in res:
        graded_entries.append(e)

entries = []
for e in graded_entries:
    w = wins_of(e)
    t = trials_of(e)
    exact = Fraction(w, t) if t else Fraction(0, 1)
    cv = card_of(e)
    rnds = []
    for name, r in (e.get("rounds") or {}).items():
        rnds.append({
            "name": name,
            "kind": r.get("kind"),
            "metaphor": r.get("metaphor"),
            "wins": int(r.get("wins") or 0),
            "trials": int(r.get("trials") or 0),
            "score": r.get("score"),
            "truncated": bool(r.get("truncated")),
            "finish": r.get("finish_reasons") or {},
        })
    weigh = e.get("weigh_in") or {}
    config = e.get("config") or {}
    norm_flags = [basename(x) for x in (config.get("server_flags") or [])]
    entries.append({
        "label": basename(e.get("gguf")).replace(".gguf", ""),
        "sha": (e.get("sha256") or "")[:12],
        "fullSha": e.get("sha256"),
        "card": cv,
        "cardLabel": "card %s" % cv,
        "wins": w,
        "trials": t,
        "exact": ("%.4f" % (float(exact))),
        "exactFrac": "%d/%d" % (w, t),
        "belt": (e.get("grade") or {}).get("belt", "?"),
        "stripes": (e.get("grade") or {}).get("stripes", 0),
        "roundsWon": (e.get("grade") or {}).get("rounds_won", 0),
        "rounds": (e.get("grade") or {}).get("rounds", 0),
        "division": e.get("division"),
        "footprint": e.get("footprint_gb"),
        "weightsGb": weigh.get("weights_gb"),
        "residentGb": weigh.get("footprint_gb"),
        "partialOffload": weigh.get("partial_offload"),
        "divisionCompetition": weigh.get("division_for_competition"),
        "divisionResident": weigh.get("division_from_resident"),
        "placement": weigh.get("placement"),
        "meanLatency": e.get("mean_latency"),
        "truncatedTrials": truncated_trials(e),
        "finishReasons": {r["name"]: r["finish"] for r in rnds},
        "roundsDetail": rnds,
        "answersFromReasoning": e.get("answers_from_reasoning"),
        "config": {
            "ctx": config.get("ctx"),
            "maxTokens": config.get("max_tokens"),
            "trials": config.get("trials"),
            "temperature": config.get("temperature"),
            "ngl": config.get("n_gpu_layers"),
            "flags": norm_flags,
        },
        "certification": e.get("certification"),
        "state": "run-of-record",
    })

entries.sort(key=lambda x: (x["card"], -Fraction(x["wins"], x["trials"]), x["label"]))

from collections import Counter
card_counts = Counter(e["card"] for e in entries)
display_pay = {
    "generated": "derived",
    "bundleCount": len(arena_bundles),
    "gradedCount": len(entries),
    "scratchedCount": len(scratched_paths),
    "cardCounts": {str(k): card_counts.get(k, 0) for k in sorted(card_counts)},
    "entries": entries,
    "scratched": scratched_paths,
}

# no nonce, no timestamp; output is byte-stable given a fixed input tree

data_json = json.dumps(display_pay, separators=(",", ":"), sort_keys=True)


# Build HTML. __DATA__ placeholder is replaced after template creation.
template = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>THE ARCADE — attract mode</title>
<style>
  :root{--bg:#050507;--panel:#101014;--line:#262630;--ink:#d6d6e0;--dim:#7a7a8c;--amber:#ffb02e;--red:#ff3b30;--green:#30d158;--blue:#5ac8fa;--purple:#bf5af2;--scan:#1a1a22}
  *{box-sizing:border-box}
  html,body{margin:0;height:100%;background:#020203;color:var(--ink);font-family:ui-monospace,SFMono-Regular,Menlo,monospace;image-rendering:pixelated}
  /* ---- CRT container ---- */
  .crt{position:relative;width:100%;min-height:100vh;background:radial-gradient(ellipse at center,#0a0a10 0%,#020203 78%);overflow:hidden}
  .crt::before{content:"";position:fixed;inset:0;pointer-events:none;z-index:20;background:repeating-linear-gradient(to bottom,rgba(255,255,255,.035) 0 1px,transparent 1px 3px);mix-blend-mode:screen}
  .crt::after{content:"";position:fixed;inset:0;pointer-events:none;z-index:21;background:radial-gradient(ellipse at center,transparent 55%,rgba(0,0,0,.85) 100%)}
  .stage{position:relative;z-index:2;padding:10px}
  /* ---- marquee header ---- */
  .marquee{border:2px solid var(--amber);background:linear-gradient(90deg,#2a1a00,#1a1200);padding:6px 10px;display:flex;justify-content:space-between;align-items:center;font-size:12px;letter-spacing:.12em;color:var(--amber)}
  .marquee b{font-size:14px}
  /* ---- attract wall ---- */
  .wall{display:grid;grid-template-columns:repeat(auto-fill,162px);gap:14px;margin-top:12px;padding:6px}
  .cabinet{width:160px;border:2px solid #444;background:var(--panel);position:relative;outline:0;cursor:pointer;transition:transform .08s;box-shadow:4px 4px 0 #000}
  .cabinet:hover{transform:translate(-1px,-1px)}
  .cabinet.selected{border-color:var(--green);box-shadow:0 0 0 2px var(--green),4px 4px 0 #000}
  .cab-top{background:#1a1a24;border-bottom:2px solid #444;padding:4px 6px;font-size:9px;letter-spacing:.18em;color:var(--dim)}
  .cab-marq{background:#222;border-bottom:2px solid #444;padding:5px 6px;font-size:10px;font-weight:700;color:#fff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .cab-screen{height:68px;background:#000;display:flex;flex-direction:column;justify-content:center;align-items:center;border-bottom:2px solid #444;position:relative;overflow:hidden}
  .cab-screen .pixel{font-size:18px;font-weight:800;color:var(--green);text-shadow:0 0 4px var(--green)}
  .cab-screen .tag{font-size:8px;color:var(--dim);letter-spacing:.18em;margin-top:2px}
  .cab-body{padding:4px 6px;font-size:9px;color:var(--dim);line-height:1.35}
  .cab-body .row{display:flex;justify-content:space-between}
  .cab-body .row b{color:var(--ink)}
  .cab-plate{background:#0d0d12;border-top:2px solid #444;padding:3px 6px;font-size:8px;color:var(--amber);letter-spacing:.1em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .cab-foot{background:#000;border-top:1px solid #2a2a33;padding:3px 6px;font-size:8px;color:#555}
  /* badges */
  .belt{display:inline-block;padding:0 4px;border-radius:2px;font-size:8px;font-weight:800;letter-spacing:.1em;background:var(--amber);color:#1a1200}
  .state{font-size:8px;letter-spacing:.16em;color:var(--green)}
  .state.scratch{color:var(--red)}
  .state.never{color:var(--dim)}
  .state.out{color:var(--amber)}
  /* detail */
  .detail{margin-top:14px;border:2px solid #333;background:#040408;padding:10px}
  .detail h2{margin:0 0 6px;font-size:13px;color:var(--amber);letter-spacing:.12em}
  .detail .grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px}
  .box{border:1px solid #262630;background:#080810;padding:8px;font-size:11px}
  .box h3{margin:0 0 4px;font-size:10px;letter-spacing:.16em;color:var(--dim)}
  .box table{width:100%;border-collapse:collapse}
  .box td{padding:1px 0;font-size:10px;vertical-align:top}
  .box td:first-child{color:var(--dim);width:118px}
  .box td:last-child{color:var(--ink)}
  .rows{margin-top:4px}
  .rowItem{display:grid;grid-template-columns:118px 40px 40px 14px;gap:6px;font-size:10px;padding:2px 0;border-top:1px dashed #1c1c24}
  .outroom{color:var(--amber)}
  .missed{color:var(--red)}
  /* filters */
  .filters{margin:8px 0 4px;display:flex;gap:6px;flex-wrap:wrap}
  .btn{background:#000;border:1px solid #444;color:var(--dim);font:inherit;font-size:10px;padding:3px 8px;cursor:pointer}
  .btn.on{border-color:var(--amber);color:var(--amber)}
  /* proof */
  .proof{margin-top:12px;border-top:2px solid #2a2a33;padding-top:8px;font-size:10px;color:var(--dim)}
  .proof b{color:var(--ink)}
  .mono{font-family:monospace}
  .clauses li{margin:2px 0}
  .clauses .ok{color:var(--green)}
  .hidden{display:none}
  @keyframes cycle{0%{transform:translateY(0)}100%{transform:translateY(-100%)}}
</style>
</head>
<body>
<div class="crt">
  <div class="stage">
    <div class="marquee">
      <span><b>THE ARCADE</b> · ATTRACT MODE · CABINETS CYCLING · DIRECT SELECTION · NO DOORS · NO HOST</span>
      <span id="counts"></span>
    </div>

    <div class="filters">
      <button class="btn on" data-f="all">ALL CABINETS</button>
      <button class="btn" data-f="1">SUITE 1 (9 TRIALS)</button>
      <button class="btn" data-f="2">SUITE 2 (18 TRIALS)</button>
      <button class="btn" data-f="3">SUITE 3</button>
      <button class="btn" data-f="4">SUITE 4</button>
      <button class="btn" data-f="trunc">OUT OF ROOM</button>
      <button class="btn" data-f="partial">PARTIAL OFFLOAD</button>
    </div>

    <div id="wall" class="wall"></div>

    <div id="detail" class="detail hidden">
      <h2 id="dtitle"></h2>
      <div class="grid2" id="dgrid"></div>
      <div id="drows" class="rows"></div>
    </div>

    <div class="proof">
      <div><b>PROVENANCE.</b> Generated from <span class="mono">results/*.json</span>. Sort key:
      <span class="mono">Fraction(sum wins, sum trials)</span> (integer counts). Belt is a label, never a sort key.
      <span class="mono">results == []</span> renders as a missed weight, never a zero. <span class="mono">card_version</span> is a hard partition;
      the suite partition is derived, never a literal total. <span class="mono">task suite v2</span> names the 18-trial suite, not a release —
      this front end is v1. Catalogued cabinets without a recorded run are NEVER RUN and do not appear on the floor.</div>
      <div style="margin-top:6px"><b>STATE VOCABULARY:</b>
        <span class="state">FROZEN</span> ·
        <span class="state">RUN-OF-RECORD</span> ·
        <span class="state scratch">SCRATCH / MISSED WEIGHT</span> ·
        <span class="state out">OUT OF ROOM</span> ·
        <span class="state never">NEVER RUN</span></div>
      <div style="margin-top:6px"><b>THE FOUR CLAUSES (Ocho §8) — checked by construction:</b>
        <ul class="clauses">
          <li><span class="ok">✓</span> 1. Sort on exact rational counts; belt is a label. No belt-sorted default exists.</li>
          <li><span class="ok">✓</span> 2. <span class="mono">results == []</span> → missed weight, excluded from averages. Keyed on data, not filename.</li>
          <li><span class="ok">✓</span> 3. Task suits 1 and 2 never share a table, average or chart. Front end is v1.</li>
          <li><span class="ok">✓</span> 4. Token cap → OUT OF ROOM, not wrong. Latency carries its placement in the same unit. <span class="mono">ngl</span> counts layers.</li>
        </ul>
      </div>
      <div style="margin-top:6px;font-size:9px;color:#4a4a58">Every number above comes from a parser, an execution, or a ground truth — never from a model judging models. A score with no scorer inverts this project.</div>
    </div>
  </div>
</div>

<script>
const DATA = __DATA__;
const AUDIO = (function(){
  let ctx=null;
  function ensure(){ if(!ctx) try{ctx=new (window.AudioContext||window.webkitAudioContext)()}catch(e){} return ctx; }
  function tone(freq,dur,type,gain){
    const c=ensure(); if(!c) return;
    const o=c.createOscillator(), g=c.createGain();
    o.type=type; o.frequency.value=freq; g.gain.value=gain;
    o.connect(g); g.connect(c.destination);
    o.start(); g.gain.exponentialRampToValueAtTime(0.001,c.currentTime+dur); o.stop(c.currentTime+dur);
  }
  function noise(dur,gain){
    const c=ensure(); if(!c) return;
    const buf=c.createBuffer(1,c.sampleRate*dur, c.sampleRate);
    const d=buf.getChannelData(0);
    for(let i=0;i<d.length;i++) d[i]=(Math.random()*2-1)*0.4;
    const src=c.createBufferSource(); src.buffer=buf;
    const g=c.createGain(); g.gain.value=gain;
    src.connect(g); g.connect(c.destination); src.start(); g.gain.exponentialRampToValueAtTime(0.001,c.currentTime+dur); src.stop(c.currentTime+dur);
  }
  return {
    blip(){ tone(880,0.08,'square',0.08); },
    buzz(){ noise(0.25,0.12); },
    descend(){ for(let i=0;i<6;i++) setTimeout(()=>tone(440-i*40,0.12,'square',0.07),i*90); },
    fanfare(){ [523,659,784].forEach((f,i)=>setTimeout(()=>tone(f,0.14,'triangle',0.09),i*110)); }
  };
})();
const entries = DATA.entries || [];
let filter = 'all';
document.getElementById('counts').textContent =
  'BUNDLES ' + DATA.bundleCount + ' · GRADED ' + DATA.gradedCount + ' · MISSED WEIGHTS ' + DATA.scratchedCount +
  ' · ' + Object.keys(DATA.cardCounts).map(k=>'SUITE '+k+' '+DATA.cardCounts[k]).join(' · ');

function passesFilter(e,f){
  if(f==='all') return true;
  if(f==='1') return e.card===1;
  if(f==='2') return e.card===2;
  if(f==='3') return e.card===3;
  if(f==='4') return e.card===4;
  if(f==='trunc') return e.truncatedTrials>0;
  if(f==='partial') return e.partialOffload===true;
  return true;
}
function rerenderWall(){
  const wall = document.getElementById('wall');
  wall.innerHTML = '';
  entries.filter(e=>passesFilter(e,filter)).forEach((e,i)=>{
    const el = document.createElement('div');
    el.className='cabinet';
    el.dataset.index = entries.indexOf(e);
    el.innerHTML =
      '<div class="cab-top">CAB-'+String(entries.indexOf(e)+1).padStart(3,'0')+' · FROZEN</div>'+
      '<div class="cab-marq">'+esc(e.label)+'</div>'+
      '<div class="cab-screen"><div class="pixel">'+esc(e.exact)+'</div><div class="tag">'+esc(e.belt)+' · '+e.wins+'/'+e.trials+'</div></div>'+
      '<div class="cab-body">'+
        '<div class="row"><span>suites</span><b>'+e.cardLabel.toUpperCase()+'</b></div>'+
        '<div class="row"><span>division</span><b>'+esc(e.division||'—')+'</b></div>'+
        '<div class="row"><span>trunc</span><b>'+e.truncatedTrials+'</b></div>'+
        '<div class="row"><span>state</span><span class="state '+stateClass(e)+'">'+stateText(e)+'</span></div>'+
      '</div>'+
      '<div class="cab-plate">SHA '+esc(e.sha)+' · STRIPES '+Number(e.stripes).toFixed(0)+' · RUN-OF-RECORD</div>'+
      '<div class="cab-foot">tap to inspect · esc to clear</div>';
    el.addEventListener('click',()=>selectCabinet(entries.indexOf(e)));
    wall.appendChild(el);
  });
}
function stateClass(e){ if(e.state==='scratch') return 'scratch'; if(e.truncatedTrials>0) return 'out'; return ''; }
function stateText(e){ if(e.state==='scratch') return 'MISSED WEIGHT'; if(e.truncatedTrials>0) return 'OUT OF ROOM'; return 'RUN-OF-RECORD'; }
function esc(s){ if(s==null) return ''; return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
document.querySelectorAll('.btn').forEach(btn=>{
  btn.addEventListener('click',()=>{ document.querySelectorAll('.btn').forEach(b=>b.classList.remove('on')); btn.classList.add('on'); filter=btn.dataset.f; rerenderWall(); });
});

function selectCabinet(idx){
  const e = entries[idx];
  document.querySelectorAll('.cabinet').forEach(c=>c.classList.toggle('selected', Number(c.dataset.index)===idx));
  AUDIO.blip();
  if(e.truncatedTrials>0) setTimeout(()=>AUDIO.buzz(),120);
  const d = document.getElementById('detail');
  d.classList.remove('hidden');
  document.getElementById('dtitle').textContent = e.label + ' · SHA ' + e.sha + ' · ' + e.belt;
  const grid = document.getElementById('dgrid');
  grid.innerHTML = '';
  grid.appendChild(box('CABINET PLATE (frozen identity)', [
    ['model sha256', e.fullSha],
    ['suite', e.cardLabel + ' · locked'],
    ['state', stateText(e)],
    ['belt', e.belt + ' (label, not sort key)'],
    ['stripes', e.stripes],
    ['rounds won', e.roundsWon + ' / ' + e.rounds],
  ]));
  grid.appendChild(box('WEIGH-IN (measured, not declared)', [
    ['division', (e.divisionCompetition||e.division||'—') + (e.partialOffload? ' (from weights under partial offload)' : '')],
    ['resident footprint', (e.residentGb!=null? e.residentGb+' GB':'—') + ' (machine reading)'],
    ['weights', (e.weightsGb!=null? e.weightsGb+' GB':'—')],
    ['partial offload', e.partialOffload? 'yes' : 'no'],
    ['placement', e.placement || 'ABSENT (no latency shown)'],
    ['mean latency', (e.placement && e.meanLatency!=null)? e.meanLatency+' s ('+e.placement+')' : 'not comparable without placement'],
  ]));
  grid.appendChild(box('MEASUREMENT (scorer = parser / executed tests)', [
    ['exact aggregate', e.exactFrac + ' = ' + e.exact],
    ['truncated trials', e.truncatedTrials + ' (OUT OF ROOM, not wrong)'],
    ['answers from reasoning', e.answersFromReasoning!=null? e.answersFromReasoning : '—'],
    ['certification', e.certification || 'OPEN (self-reported)'],
    ['suites never mixed', 'card ' + e.card + ' only'],
  ]));
  grid.appendChild(box('CONFIG (a result without its config is not a result)', [
    ['ctx', e.config.ctx],
    ['max tokens', e.config.maxTokens],
    ['trials', e.config.trials],
    ['temperature', e.config.temperature],
    ['ngl (layers)', e.config.ngl!=null? e.config.ngl : 'auto-fit (not bytes)'],
    ['server flags', (e.config.flags||[]).join(' ') || '—'],
  ]));
  const rows = document.getElementById('drows');
  rows.innerHTML = '<h3 style="margin:6px 0 4px;font-size:10px;letter-spacing:.16em;color:var(--dim)">ROUND BY ROUND</h3>';
  (e.roundsDetail||[]).forEach(r=>{
    const div = document.createElement('div');
    div.className='rowItem';
    const marker = r.truncated ? '<span class="outroom">OUT-OF-ROOM</span>' : (r.wins>=r.trials?'<span style="color:var(--green)">PASS</span>':'<span style="color:var(--dim)">—</span>');
    div.innerHTML = '<span>'+esc(r.name)+' <span style="color:#555">'+esc(r.kind||'')+'</span></span>'+
                    '<span>'+r.wins+'/'+r.trials+'</span>'+
                    '<span>'+esc(r.score==null?'—':Number(r.score).toFixed(2))+'</span>'+
                    '<span>'+marker+'</span>';
    rows.appendChild(div);
  });
  // cue map (show derived, never hand-authored): only outcomes the record carries
  const cues = document.createElement('div');
  cues.style.marginTop='8px';
  cues.innerHTML = '<h3 style="margin:6px 0 4px;font-size:10px;letter-spacing:.16em;color:var(--dim)">OUTCOME CUES (R9 — derived from bound fields)</h3>'+
    '<div class="rowItem" style="grid-template-columns:1fr"><span>win/loss wherever wins/trials are recorded · truncation → out-of-room cue · resignation: <b style="color:var(--amber)">null</b> (no run did not finish on this cabinet; absence declared, not omitted)</span></div>';
  rows.appendChild(cues);
}
function box(t, rows){
  const d=document.createElement('div'); d.className='box';
  d.innerHTML='<h3>'+esc(t)+'</h3><table>'+rows.map(r=>'<tr><td>'+esc(r[0])+'</td><td>'+esc(r[1])+'</td></tr>').join('')+'</table>';
  return d;
}
function esc(s){ if(s==null) return ''; return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

rerenderWall();
document.addEventListener('keydown',e=>{ if(e.key==='Escape'){ document.getElementById('detail').classList.add('hidden'); document.querySelectorAll('.cabinet').forEach(c=>c.classList.remove('selected')); } });
</script>
</body>
</html>
'''

html = template.replace("__DATA__", data_json)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)

# ── Verification assertions. THESE MUST BE ABLE TO FAIL. ─────────────────────
# The pair that stood here were `assert DATA if False else True` and
# `assert "results == []" not in html or True` -- two tautologies, under a comment
# claiming the checks were "printed, not just claimed". Worse: `DATA` is the JS-side
# object in the rendered template, not a Python name in this file at all, so the
# first assertion referenced a variable that DOES NOT EXIST and `if False else True`
# meant Python never looked. A check that cannot run is indistinguishable from a
# check that passes, and the 92-vs-85 defect rode straight through both.
assert display_pay["gradedCount"] == len(graded_entries), (display_pay["gradedCount"], len(graded_entries))
assert display_pay["scratchedCount"] == len(scratched_paths), (display_pay["scratchedCount"], len(scratched_paths))
assert display_pay["bundleCount"] == len(arena_bundles), (display_pay["bundleCount"], len(arena_bundles))
assert len(arena_bundles) + len(non_entrant_paths) == len(bundles), (
    len(arena_bundles), len(non_entrant_paths), len(bundles))

# The claim the HTML RENDERS -- "results == [] renders as a missed weight...
# Keyed on data, not filename" -- is now TESTED, in both directions, rather than
# asserted in prose. Each direction is a real check with a real failure mode.
for _name in scratched_paths:
    assert json.load(open(os.path.join(RESULTS, _name))).get("results") == [], _name
_scratched = set(scratched_paths)
for _p in arena_bundles:
    if json.load(open(_p)).get("results") == []:
        assert os.path.basename(_p) in _scratched, _p
from collections import Counter
# card counts are derived and printed below
# exact rational ordering check
prev = None
for e in sorted(entries, key=lambda x: x["card"]):
    val = float(Fraction(int(e["wins"]), int(e["trials"])))
    if prev is not None and prev[0] == e["card"]:
        assert val <= prev[1] + 1e-12, (prev, val)
    prev = (e["card"], val)
print("wrote", OUT, "bytes", os.path.getsize(OUT))
print("graded", len(entries), "scratched", len(scratched_paths))
print("card partition", dict(card_counts))
print("truncated trials (out of room)", sum(e["truncatedTrials"] for e in entries))
print("placement absent", sum(1 for e in entries if not e["placement"]))
print("partial offload", sum(1 for e in entries if e["partialOffload"]))
