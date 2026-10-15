#!/usr/bin/env python3
"""Build Concept A (Minimal / Terminal) -- one of the labelled Arcade concept variants.

Weight target: smallest possible. DOM + text only, no canvas, no audio, no CSS effects beyond
a single scanline rule. Entry is a high-score table; selection is direct; no avatar.
"""
import json, os
ARENA = os.path.dirname(os.path.abspath(__file__))
PROBE = os.path.join(ARENA, "probes_RUN_20261010-072252.json")
OUT = os.path.join(ARENA, "arcade_concept_a_minimal.html")
TRACE_FREEZE = "186f561facd44916"
PILOT_FREEZE = "7134c3e8"

def main():
    d = json.load(open(PROBE))
    c = [x for x in d["cells"] if x.get("entrant")=="Qwen3.5-9B-Q4_K_M" and x.get("level")=="02_two_boxes"][0]
    assert not c["solved"] and len(c["trace"])==40
    trace = [{"ply":int(t["ply"]),"token":t["token"],"action":t["action"],"outcome":t["outcome"],"board":t["board"]} for t in c["trace"]]
    data = {"entrant":c["entrant"],"level":c["level"],"solved":False,"moves":int(c["moves"]),"attempted":int(c["attempted"]),"blocked":int(c["blocked"]),"not_an_action":int(c["not_an_action"]),"give_up":int(c["give_up"]),"ended":c["ended"],"distinctBoards":len(set(t["board"] for t in c["trace"])),"finalBoard":c["final_board"],"freeze":TRACE_FREEZE,"pilotFreeze":PILOT_FREEZE,"trace":trace}
    data_json = json.dumps(data, separators=(",",":"))
    template = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CONCEPT A · THE ARCADE AS TEXT</title>
<style>
  html,body{margin:0;min-height:100%;background:#000;color:#33ff66;font-family:ui-monospace,Menlo,monospace;font-size:13px}
  body{padding:12px;max-width:880px;margin:0 auto}
  h1{font-size:14px;letter-spacing:.12em;margin:0 0 8px;border-bottom:1px solid #1a5533;padding-bottom:4px}
  pre{margin:0;white-space:pre;line-height:1.2}
  .board{color:#33ff66;font-weight:700}
  .row{display:flex;gap:8px;flex-wrap:wrap;margin:6px 0;font-size:12px}
  .red{color:#ff5555} .amber{color:#ffb02e} .dim{color:#4a7a5a}
  button{background:#000;border:1px solid #1a5533;color:#33ff66;font:inherit;font-size:12px;padding:3px 8px;cursor:pointer}
  button:hover{border-color:#33ff66}
  .stream{max-height:120px;overflow:auto;border-top:1px solid #1a5533;margin-top:6px;font-size:11px}
  .cur{background:#0a2214}
  .blocked .out{color:#ff5555} .pushed .out{color:#ffb02e}
  footer{margin-top:10px;border-top:1px solid #1a5533;padding-top:6px;font-size:10px;color:#4a7a5a;line-height:1.5}
</style>
</head>
<body>
<h1>THE ARCADE · CONCEPT A · TEXT ONLY · NO AUDIO · NO CANVAS · [WEIGHT: see footer]</h1>
<div class="row">
  <span>ENTRANT: <b id="ent"></b></span>
  <span>LEVEL: <b id="lvl"></b></span>
  <span>PLIES: <b id="nply"></b></span>
  <span>BOARDS: <b id="nb"></b></span>
  <span class="red">STATUS: UNSOLVED</span>
  <span class="amber">FREEZE: <span id="freeze"></span></span>
</div>
<pre id="board" class="board"></pre>
<div class="row">
  <button id="back">BACK</button>
  <button id="play">PLAY</button>
  <button id="step">STEP</button>
  <button id="reset">RESET</button>
  <span id="ply" class="dim"></span>
  <span id="outcome"></span>
</div>
<div class="stream" id="stream"></div>
<div class="row dim" id="counts"></div>
<footer>
WEIGHT (measured): single HTML file, DOM + text only. No canvas, no audio context, no images,
no external resources, no JS frameworks. Scanlines omitted to keep bytes minimal; the CRT is
implied by the phosphor palette. Larger variants will cost more; nothing here is paid for that
is not on the screen. Data embedded verbatim from probes_RUN_20261010-072252.json;
freeze <span class="amber" id="ffreeze"></span> differs from the pilot run of record
(7134c3e8) and is never pooled. Unsolved is reported as unsolved -- 12 successful moves in
40 attempts, commands_exhausted -- not a failure and not a zero. Catalogued cabinets nobody
has run do not appear here.
</footer>
<script>
const DATA = __DATA__;
const trace = DATA.trace;
let idx=-1, playing=false, timer=null;
function renderBoard(b){ document.getElementById('board').textContent = b; }
function outcomeLabel(o){ return o==='pushed'?'PUSHED':o==='moved'?'MOVED':o==='blocked'?'BLOCKED':String(o).toUpperCase(); }
function goto(i){
  if(i<0)i=0; if(i>=trace.length)i=trace.length-1; idx=i;
  const t=trace[idx];
  renderBoard(t.board);
  document.getElementById('ply').textContent='PLY '+(idx+1)+'/'+trace.length;
  document.getElementById('outcome').textContent=outcomeLabel(t.outcome);
  document.getElementById('outcome').className=t.outcome;
  let h='';
  for(let i=0;i<trace.length;i++){const t=trace[i]; h+='<div class="moveRow'+(i===idx?' cur':'')+' '+t.outcome+'"><span>'+String(t.ply).padStart(2,'0')+'</span> <span>'+ (t.action||'-') +'</span> <span class="out">'+outcomeLabel(t.outcome)+'</span></div>';}
  document.getElementById('stream').innerHTML=h;
  const cur=document.querySelector('.cur'); if(cur) cur.scrollIntoView({block:'nearest'});
}
function playStep(){
  if(idx>=trace.length-1){playing=false;clearInterval(timer);timer=null;document.getElementById('play').textContent='PLAY';return;}
  goto(idx+1);
}
document.getElementById('play').onclick=()=>{ playing=!playing; document.getElementById('play').textContent=playing?'PAUSE':'PLAY'; if(playing) timer=setInterval(playStep,260); else {clearInterval(timer);timer=null;} };
document.getElementById('step').onclick=()=>{ if(timer){clearInterval(timer);timer=null;playing=false;document.getElementById('play').textContent='PLAY';} playStep(); };
document.getElementById('back').onclick=()=>{ if(idx>0)goto(idx-1); };
document.getElementById('reset').onclick=()=>{ if(timer){clearInterval(timer);timer=null;playing=false;document.getElementById('play').textContent='PLAY';} goto(0); };
document.addEventListener('keydown',e=>{ if(e.key===' ') {e.preventDefault();document.getElementById('play').click();} if(e.key==='ArrowRight')document.getElementById('step').click(); if(e.key==='ArrowLeft')document.getElementById('back').click(); });
document.getElementById('ent').textContent=DATA.entrant;
document.getElementById('lvl').textContent=DATA.level;
document.getElementById('nply').textContent=trace.length;
document.getElementById('nb').textContent=DATA.distinctBoards;
document.getElementById('freeze').textContent=DATA.freeze.slice(0,8).toUpperCase();
document.getElementById('ffreeze').textContent=DATA.freeze;
document.getElementById('counts').textContent='MOVES '+DATA.moves+' / ATTEMPTED '+DATA.attempted+' (blocked '+DATA.blocked+', not_an_action '+DATA.not_an_action+', give_up '+DATA.give_up+', ended '+DATA.ended+')';
goto(0);
</script>
</body>
</html>
'''
    html = template.replace("__DATA__", data_json)
    with open(OUT, "w", encoding="utf-8") as f: f.write(html)
    print("wrote", OUT, "bytes", os.path.getsize(OUT))

if __name__ == "__main__":
    main()