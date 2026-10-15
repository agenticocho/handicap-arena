#!/usr/bin/env python3
"""Build the Zork cabinet trace screen from the simulator and a real level.

One representation per cabinet (breadth first): a text-record trace viewer for the
Long Crawl, ESCAPED and GATE_LOCKED on the same level. No levels were added and
no invented data: both runs are produced by zork.play() on the committed level.
"""
import hashlib, json, os, sys

ARENA = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ARENA)
import zork

LEVEL = os.path.join(ARENA, "levels", "zork_02_long_crawl.txt")
OUT = os.path.join(ARENA, "zork_trace.html")

world_text = open(LEVEL, encoding="utf-8").read()

runs = {
    "escaped": zork.play(world_text, ["north", "take key", "south", "east", "north", "east"]),
    "locked": zork.play(world_text, ["north", "south", "east", "north", "east"]),
}

# make run ids explicit
runs["escaped"]["label"] = "ESCAPED (carried the required item)"
runs["locked"]["label"] = "GATE LOCKED (forgot the required item)"

level_digest = hashlib.sha256(world_text.encode("utf-8")).hexdigest()[:12]
sim_digest = hashlib.sha256(open(os.path.join(ARENA, "zork.py"), "rb").read()).hexdigest()[:12]

for r in runs.values():
    r["level_digest"] = level_digest
    r["simulator_digest"] = sim_digest

data_json = json.dumps(runs, separators=(",", ":"))

template = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>THE ARCADE · ZORK · TRACE (MODERN 8-BIT)</title>
<style>
  *{box-sizing:border-box}
  html,body{margin:0;min-height:100%;background:radial-gradient(circle at 50% -10%,#1a1a2e 0%,#05050a 62%);color:#e7eaf2;font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
  .room{min-height:100vh;display:flex;align-items:center;justify-content:center;padding:24px 16px}
  .cabinet{width:min(1180px,100%);display:grid;grid-template-columns:minmax(0,1fr) minmax(0,360px);gap:18px;align-items:start}
  @media (max-width:980px){.cabinet{grid-template-columns:1fr}}
  .frame{background:linear-gradient(180deg,#1c1c26,#0a0a12);border:2px solid #2a2a38;border-radius:18px;padding:18px;box-shadow:0 26px 70px rgba(0,0,0,.8),inset 0 1px 0 rgba(255,255,255,.05)}
  .marquee{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:10px 14px;border-radius:10px;background:linear-gradient(180deg,#0b2b24,#04120f);border:2px solid #4ee08a;box-shadow:inset 0 -2px 0 rgba(0,0,0,.6),0 0 18px rgba(78,224,138,.18);font-size:12px;letter-spacing:.14em;color:#4ee08a;margin-bottom:14px}
  .marquee b{font-size:13px}
  .leds{display:flex;gap:6px}
  .led{width:8px;height:8px;border-radius:50%;background:#4ee08a;box-shadow:0 0 9px #4ee08a;animation:blink 1.35s infinite}
  .led:nth-child(2){animation-delay:.25s} .led:nth-child(3){animation-delay:.5s}
  @keyframes blink{0%,100%{opacity:1} 50%{opacity:.35}}
  .monitor{background:#03060a;border-radius:14px;overflow:hidden;padding:14px;box-shadow:inset 0 0 50px #000,0 0 0 2px #1a1a24;min-height:360px}
  .tabs{display:flex;gap:8px;margin-bottom:10px}
  .tab{flex:1;padding:8px;border-radius:8px;border:1px solid #2a2a38;background:#0a0a14;color:#7b8194;cursor:pointer;font:inherit;font-size:11px;letter-spacing:.1em}
  .tab.on{border-color:#4ee08a;color:#4ee08a;background:#061a12}
  .line{padding:4px 0;border-bottom:1px dashed #1a2420;font-size:12px;display:grid;grid-template-columns:34px 120px 70px 90px 1fr;gap:8px;align-items:baseline}
  .line.hdr{color:#7b8194;font-size:10px;letter-spacing:.14em}
  .outcome.moved{color:#7b8194}
  .outcome.took{color:#4ee08a}
  .outcome.escaped{color:#30d158;font-weight:700}
  .outcome.gate_locked{color:#ff5a5a;font-weight:700}
  .outcome.unparsed{color:#ffb02e}
  .side{display:grid;gap:12px}
  .card{background:rgba(255,255,255,.035);border:1px solid #2a2a38;border-radius:12px;padding:12px 14px}
  .card h3{margin:0 0 8px;font-size:10px;letter-spacing:.18em;color:#7b8194}
  .stats{display:grid;grid-template-columns:1fr 1fr;gap:6px}
  .stat{padding:8px;border-radius:8px;background:rgba(0,0,0,.35);border:1px solid #202030}
  .stat .k{font-size:9px;letter-spacing:.16em;color:#7b8194} .stat .v{font-size:15px;font-weight:700;color:#4ee08a;margin-top:2px;font-size:13px}
  .room-path{font-size:11px;color:#9aa;word-break:break-word}
  .footer{grid-column:1/-1;font-size:10px;color:#7b8194;line-height:1.55;border-top:1px solid #232333;padding-top:10px}
  .footer b{color:#e7eaf2}
</style>
</head>
<body>
<div class="room">
  <div class="cabinet">
    <div class="frame">
      <div class="marquee">
        <span><b>THE ARCADE</b> · ZORK · TRACE (MODERN 8-BIT)</span>
        <div class="leds"><div class="led"></div><div class="led"></div><div class="led"></div></div>
      </div>
      <div class="monitor">
        <div class="tabs">
          <button class="tab on" data-run="escaped">ESCAPED</button>
          <button class="tab" data-run="locked">GATE LOCKED</button>
        </div>
        <div id="stream"></div>
      </div>
    </div>
    <div class="side">
      <div class="card">
        <h3>CABINET PLATE</h3>
        <div class="stats" id="plate"></div>
        <div style="margin-top:10px;font-size:11px" id="statusLine"></div>
      </div>
      <div class="card">
        <h3>ROOMS (first visit)</h3>
        <div class="room-path" id="rooms"></div>
      </div>
      <div class="card">
        <h3>COUNTS (never merged)</h3>
        <div id="counts"></div>
      </div>
    </div>
    <div class="footer">
      <b>PROVENANCE.</b> Both runs are produced by <b>zork.py</b> (simulator digest <span style="color:#4ee08a" id="sd"></span>)
      on <b>levels/zork_02_long_crawl.txt</b> (digest <span style="color:#4ee08a" id="ld"></span>). The record is the sufficient
      statistic; the trace below carries command, verb, object, outcome, room and inventory so a later reader
      can replay the crawl byte-for-byte. <b>escaped</b> carries the required item; <b>gate_locked</b> arrives at
      the gate without it. Catalogued cabinets nobody has run do not appear. This is a reference run, not a
      model entrant's.
    </div>
  </div>
</div>
<script>
const RUNS = __DATA__;
let current = "escaped";
function esc(s){return String(s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}
function render(){
  const r = RUNS[current];
  const stream = document.getElementById('stream');
  let h = '<div class="line hdr"><span>STEP</span><span>COMMAND</span><span>VERB</span><span>OUTCOME</span><span>ROOM · INVENTORY</span></div>';
  for(const t of r.trace){
    const inv = (t.inventory||[]).join(", ") || "(empty)";
    h += '<div class="line"><span>'+String(t.step).padStart(2,'0')+'</span><span>'+esc(t.command)+'</span><span>'+esc(t.verb||"-")+'</span><span class="outcome '+t.outcome+'">'+esc(t.outcome).toUpperCase()+'</span><span>'+esc(t.room)+' · '+esc(inv)+'</span></div>';
  }
  stream.innerHTML = h;
  const plate = document.getElementById('plate');
  plate.innerHTML =
    '<div class="stat"><div class="k">ENDING</div><div class="v">'+esc(r.ending).toUpperCase()+'</div></div>'+
    '<div class="stat"><div class="k">CARRIED ITEM</div><div class="v">'+(r.carried_required_item?"YES":"NO")+'</div></div>'+
    '<div class="stat"><div class="k">REQUIRED</div><div class="v" style="font-size:12px">'+esc(r.required_item)+'</div></div>'+
    '<div class="stat"><div class="k">TOOK AT STEP</div><div class="v">'+(r.took_item_at_step==null?"NONE":r.took_item_at_step)+'</div></div>'+
    '<div class="stat"><div class="k">COMMANDS</div><div class="v">'+r.commands+' / '+r.commands_consumed+'</div></div>'+
    '<div class="stat"><div class="k">FINAL ROOM</div><div class="v" style="font-size:12px">'+esc(r.final_room)+'</div></div>';
  document.getElementById('statusLine').textContent = r.label + " — " + r.ending;
  document.getElementById('rooms').textContent = (r.rooms_visited||[]).join(" -> ");
  const c = r.counts||{};
  document.getElementById('counts').innerHTML =
    '<div style="font-size:11px">parsed: '+ (c.parsed||0) +'</div>'+
    '<div style="font-size:11px">unparsed: '+ (c.unparsed||0) +'</div>'+
    '<div style="font-size:11px">recognised-but-impossible: '+ (c["recognised-but-impossible"]||0) +'</div>';
  document.getElementById('sd').textContent = r.simulator_digest;
  document.getElementById('ld').textContent = r.level_digest;
}
document.querySelectorAll('.tab').forEach(b=>{
  b.onclick=()=>{ document.querySelectorAll('.tab').forEach(x=>x.classList.remove('on')); b.classList.add('on'); current=b.dataset.run; render(); };
});
render();
</script>
</body>
</html>
'''

html = template.replace("__DATA__", data_json)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("wrote", OUT, "bytes", os.path.getsize(OUT))