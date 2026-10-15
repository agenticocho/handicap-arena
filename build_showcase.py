#!/usr/bin/env python3
"""Build a SHOWCASE-grade Sokoban cabinet (artistic exploration, non-spec visual layer)."""
import hashlib, json, os

ARENA = os.path.dirname(os.path.abspath(__file__))
PROBE = os.path.join(ARENA, "probes_RUN_20261010-072252.json")
OUT = os.path.join(ARENA, "arcade_showcase.html")
# The CURRENT instrument on disk -- what the page labels "current pin", NOT the pilot's digest.
# Derived, not typed: if sokoban.py advances, this moves with it and the assertion below refuses the
# build rather than letting the plate mislabel the instrument silently.
# Declared value: CABINET_DECLARATION_sokoban.md -- "On disk sokoban.py is 00996929972b9483; the pilots
# RECORD 7134c3e8fc59fe02 (= commit f0eba6e) and the 2026-10-10 population RECORDS 186f561f."
# The pilot's digest (7134c3e8) is a historical fact and is cited as a literal in the footer; it must
# NEVER be advanced to match a re-frozen file.
PILOT_PIN = hashlib.sha256(open(os.path.join(ARENA, "sokoban.py"), "rb").read()).hexdigest()[:8]
assert PILOT_PIN == "00996929", f"current instrument drifted from its declaration: {PILOT_PIN!r}"

def main():
    d = json.load(open(PROBE))
    c = [x for x in d["cells"] if x.get("entrant") == "Qwen3.5-9B-Q4_K_M" and x.get("level") == "02_two_boxes"][0]
    assert not c["solved"] and len(c["trace"]) == 40 and c["final_board"] == c["final_screen"]
    digest = d.get("simulator_digest")
    assert isinstance(digest, str) and digest.startswith("186f561f")
    trace = [{"ply": int(t["ply"]), "token": t["token"], "action": t["action"],
              "outcome": t["outcome"], "board": t["board"]} for t in c["trace"]]
    data = {"entrant": c["entrant"], "level": c["level"], "moves": int(c["moves"]),
            "attempted": int(c["attempted"]), "blocked": int(c["blocked"]),
            "distinctBoards": len(set(t["board"] for t in c["trace"])),
            "ended": c["ended"], "freeze": digest, "pin": PILOT_PIN, "trace": trace}
    data_json = json.dumps(data, separators=(",", ":"))

    template = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>THE ARCADE · SHOWCASE CABINET</title>
<style>
  *{box-sizing:border-box}
  html,body{margin:0;min-height:100%;background:#02020a;color:#e9ecf5;font-family:ui-monospace,Menlo,monospace}
  .room{min-height:100vh;display:flex;align-items:center;justify-content:center;padding:30px 18px 50px;
    background:radial-gradient(circle at 25% 15%,rgba(90,140,255,.22),transparent 38%),
               radial-gradient(circle at 78% 82%,rgba(255,120,70,.18),transparent 40%),
               linear-gradient(180deg,#05050f 0%,#010107 100%);perspective:1400px}
  .floor{position:fixed;left:0;right:0;bottom:0;height:140px;background:linear-gradient(180deg,transparent,rgba(255,176,46,.08));pointer-events:none;filter:blur(10px)}
  .cabinet{position:relative;width:min(1180px,100%);display:grid;grid-template-columns:minmax(0,680px) minmax(0,1fr);gap:22px;align-items:start;transform-style:preserve-3d;transition:transform .15s ease}
  @media (max-width:980px){.cabinet{grid-template-columns:1fr}}
  .frame{position:relative;background:linear-gradient(180deg,#1a1a26,#07070f);border:2px solid #26263a;border-radius:20px;padding:20px;
    box-shadow:0 40px 90px rgba(0,0,0,.85), inset 0 1px 0 rgba(255,255,255,.06), 0 0 0 1px rgba(255,176,46,.08)}
  .marquee{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:12px 16px;border-radius:12px;
    background:linear-gradient(180deg,#3a1808,#140900);border:2px solid #ffb02e;color:#ffb02e;letter-spacing:.16em;font-size:12px;
    box-shadow:inset 0 -3px 0 rgba(0,0,0,.6), 0 0 26px rgba(255,176,46,.22);margin-bottom:16px;overflow:hidden}
  .marquee b{font-size:14px;text-shadow:0 0 10px rgba(255,176,46,.6)}
  .leds{display:flex;gap:6px}
  .led{width:9px;height:9px;border-radius:50%;background:#ffb02e;box-shadow:0 0 12px #ffb02e;animation:blink 1.25s infinite}
  .led:nth-child(2){animation-delay:.22s} .led:nth-child(3){animation-delay:.44s}
  @keyframes blink{0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.25;transform:scale(.8)}}
  .monitor{position:relative;background:#000;border-radius:16px;overflow:hidden;padding:12px;
    box-shadow:inset 0 0 60px #000, 0 0 0 2px #141420, 0 0 40px rgba(80,120,255,.15)}
  canvas{display:block;margin:0 auto;image-rendering:pixelated;image-rendering:crisp-edges;width:720px;height:540px;background:#000}
  .monitor::after{content:"";position:absolute;inset:12px;pointer-events:none;
    background:repeating-linear-gradient(0deg,rgba(255,255,255,.06) 0 1px,transparent 1px 3px),
               radial-gradient(circle at 50% 50%,transparent 46%,rgba(0,0,0,.78) 100%);mix-blend-mode:screen}
  .monitor::before{content:"";position:absolute;inset:0;border-radius:16px;pointer-events:none;box-shadow:inset 0 0 36px rgba(120,150,255,.16)}
  @media (max-width:760px){canvas{width:360px;height:270px}}
  .side{display:grid;gap:16px}
  .card{background:linear-gradient(180deg,rgba(255,255,255,.05),rgba(255,255,255,.015));border:1px solid #2a2a3e;border-radius:14px;padding:16px;
    box-shadow:0 14px 34px rgba(0,0,0,.35)}
  .card h3{margin:0 0 10px;font-size:10px;letter-spacing:.2em;color:#7f859c}
  .row{display:grid;grid-template-columns:30px 48px 1fr;gap:10px;padding:4px 0;border-top:1px dashed #242438;font-size:11px;align-items:center}
  .row.cur{background:rgba(255,176,46,.12);color:#fff}
  .row .tag.blocked{color:#ffb02e} .row .tag.moved{color:#7f859c} .row .tag.pushed{color:#30d158}
  .stream{max-height:290px;overflow:auto;scrollbar-width:thin}
  .stats{display:grid;grid-template-columns:1fr 1fr;gap:8px}
  .stat{padding:10px;border-radius:10px;background:rgba(0,0,0,.4);border:1px solid #22223a}
  .stat .k{font-size:9px;letter-spacing:.18em;color:#7f859c} .stat .v{font-size:17px;font-weight:800;color:#ffb02e;margin-top:3px}
  .controls{display:flex;gap:10px;flex-wrap:wrap}
  button{background:linear-gradient(180deg,#202030,#0e0e18);border:1px solid #44445a;color:#e9ecf5;font:inherit;font-size:11px;letter-spacing:.12em;padding:8px 12px;border-radius:10px;cursor:pointer;
    box-shadow:0 3px 0 #04040a, 0 0 0 1px rgba(255,255,255,.03) inset}
  button:hover{border-color:#ffb02e;color:#ffb02e;box-shadow:0 3px 0 #04040a,0 0 14px rgba(255,176,46,.18)}
  button:active{transform:translateY(2px);box-shadow:0 1px 0 #04040a}
  .btnPrimary{border-color:#ffb02e;color:#ffb02e}
  .progress{height:12px;background:#0e0e16;border:1px solid #2a2a40;border-radius:8px;overflow:hidden;margin-top:8px;position:relative}
  .progress i{position:absolute;top:0;bottom:0;width:4px;margin:0;background:#ffb02e;border-radius:2px;transform:translateX(-50%);left:0}
  .unsolved{color:#ff5a5a;font-weight:800}
  .freeze{color:#ffb02e}
  .footer{grid-column:1/-1;font-size:10px;color:#7f859c;line-height:1.6;border-top:1px solid #232338;padding-top:12px}
  .footer b{color:#e9ecf5}
  .title{font-size:11px;color:#7f859c;margin:0 0 6px;letter-spacing:.18em}
</style>
</head>
<body>
<div class="floor"></div>
<div class="room">
  <div class="cabinet" id="cab">
    <div class="frame">
      <div class="marquee">
        <span><b>THE ARCADE</b> · SHOWCASE CABINET · ALL RIGHTS TO THE RECORD</span>
        <div class="leds"><div class="led"></div><div class="led"></div><div class="led"></div></div>
      </div>
      <div class="monitor">
        <canvas id="screen" width="320" height="240"></canvas>
      </div>
      <div class="controls" style="margin-top:14px">
        <button id="back">STEP BACK</button>
        <button id="play" class="btnPrimary">PLAY</button>
        <button id="step">STEP</button>
        <button id="reset">RESET</button>
      </div>
      <div class="progress" style="margin-top:10px"><i id="bar"></i></div>
    </div>
    <div class="side">
      <div class="card">
        <div class="title">MOVE STREAM</div>
        <div id="stream" class="stream"></div>
      </div>
      <div class="card">
        <div class="title">CABINET PLATE</div>
        <div class="stats">
          <div class="stat"><div class="k">ENTRANT</div><div class="v" style="font-size:13px">QWEN3.5-9B-Q4_K_M</div></div>
          <div class="stat"><div class="k">LEVEL</div><div class="v" style="font-size:13px">02_TWO_BOXES</div></div>
          <div class="stat"><div class="k">MOVES</div><div class="v" id="mk">—</div></div>
          <div class="stat"><div class="k">ATTEMPTS</div><div class="v" id="ak">—</div></div>
          <div class="stat"><div class="k">BLOCKED</div><div class="v" id="bk">—</div></div>
          <div class="stat"><div class="k">DISTINCT BOARDS</div><div class="v" id="dk">—</div></div>
        </div>
        <div style="margin-top:12px;font-size:11px">
          run freeze <span class="freeze" id="freeze"></span> · current pin <span class="freeze" id="pin"></span> (different measurement, never pooled) · ended <b id="ended"></b><br>
          solved <span class="unsolved">NO — UNSOLVED, NOT A FAILURE, NOT A ZERO</span>
        </div>
      </div>
    </div>
    <div class="footer">
      <b>PROVENANCE.</b> Boards, plies, tokens, actions, outcomes and counts are taken verbatim from
      <span>probes_RUN_20261010-072252.json</span> — entrant <b id="fent"></b>, level <b id="flvl"></b>,
      freeze <span class="freeze" id="ffreeze"></span> (simulator digest). The freeze differs from the pilot run of record
      (<b>7134c3e8</b>); the two are different measurements and are never pooled. The board on screen is the recorded
      <b>final_screen / final_board</b> string, ASCII and byte-identical, not reconstructed. Catalogued cabinets nobody
      has run do not appear. <i>Artistic showcase layer: gradients/particles/glow are presentation, not measurement.</i>
    </div>
  </div>
</div>
<script>
const DATA = __DATA__;
const trace = DATA.trace;
const canvas = document.getElementById('screen');
const ctx = canvas.getContext('2d');
ctx.imageSmoothingEnabled = false;

const TILE = 24, HUD = 40;
const P = {
  bg:'#06070b', floor:'#0f131c', floorAlt:'#141a26', wall:'#2f3546', wallHi:'#5a607a', wallSh:'#161925',
  target:'#2a3042', targetHi:'#4a526a', crate:'#d98b2b', crateHi:'#ffd08a', crateSh:'#7a4f16', crateBand:'#a86a18',
  goal:'#37c96b', goalHi:'#b7ffd0', player:'#4ee08a', playerHi:'#d2ffea', visor:'#0a2a18', visorHi:'#4ea0ff',
  text:'#e9ecf5', dim:'#7f859c', amber:'#ffb02e', red:'#ff5a5a', green:'#30d158'
};
let particles = [];
let idx = 0, currentBoard = trace[0].board, anim = null, rafId = null;
const outcomeLabel = o => o==='pushed'?'PUSHED':o==='moved'?'MOVED':o==='blocked'?'BLOCKED':String(o).toUpperCase();

function layout(board){const lines=board.split('\n');const cols=Math.max(...lines.map(l=>l.length));const rows=lines.length;const w=cols*TILE,h=rows*TILE;return {lines,cols,rows,ox:Math.floor((320-w)/2),oy:HUD+Math.floor((240-HUD-h)/2)}}
function entities(board){const lines=board.split('\n');const player=[],crates=[];for(let r=0;r<lines.length;r++)for(let c=0;c<(lines[r]||'').length;c++){const ch=lines[r][c];if(ch==='@'||ch==='+')player.push({r,c});if(ch==='$'||ch==='*')crates.push({r,c,goal:ch==='*'});}return{lines,player:player[0]||null,crates}}

function crateMoves(fromBoard,toBoard){
  const fe=entities(fromBoard), te=entities(toBoard);
  const fromCrates=fe.crates.map(x=>({...x})), toCrates=te.crates.map(x=>({...x}));
  const used=new Array(toCrates.length).fill(false);
  const moves=[];
  for(const fc of fromCrates){
    let found=-1; for(let i=0;i<toCrates.length;i++){if(!used[i]&&toCrates[i].r===fc.r&&toCrates[i].c===fc.c){found=i;break;}}
    if(found>=0) used[found]=true;
    else { let best=-1,bestd=999; for(let i=0;i<toCrates.length;i++){if(used[i])continue;const d=Math.abs(toCrates[i].r-fc.r)+Math.abs(toCrates[i].c-fc.c);if(d<bestd){bestd=d;best=i;}} if(best>=0){used[best]=true;if(toCrates[best].r!==fc.r||toCrates[best].c!==fc.c)moves.push({from:fc,to:toCrates[best]});}}
  }
  const playerMove = (fe.player&&te.player)?{from:fe.player,to:te.player}:null;
  const movingTo=new Set(moves.map(m=>m.to.r+','+m.to.c));
  const finalCrates=toCrates.filter(tc=>!movingTo.has(tc.r+','+tc.c));
  return {fe,te,playerMove,moves,finalCrates};
}

const AUDIO=(function(){let ctx=null;function ensure(){if(!ctx)try{ctx=new (window.AudioContext||window.webkitAudioContext)()}catch(e){}return ctx;}
function tone(f,d,type,gain,slide=0){const c=ensure();if(!c)return;const o=c.createOscillator(),g=c.createGain();o.type=type;o.frequency.value=f; if(slide)o.frequency.exponentialRampToValueAtTime(Math.max(40,f+slide),c.currentTime+d); g.gain.value=gain;o.connect(g);g.connect(c.destination);o.start();g.gain.exponentialRampToValueAtTime(0.001,c.currentTime+d);o.stop(c.currentTime+d);}
function noise(d,gain){const c=ensure();if(!c)return;const buf=c.createBuffer(1,c.sampleRate*d,c.sampleRate);const dd=buf.getChannelData(0);for(let i=0;i<dd.length;i++)dd[i]=(Math.random()*2-1)*0.4;const s=c.createBufferSource();s.buffer=buf;const gg=c.createGain();gg.gain.value=gain;s.connect(gg);gg.connect(c.destination);s.start();gg.gain.exponentialRampToValueAtTime(0.001,c.currentTime+d);s.stop(c.currentTime+d);}
return{clack(){tone(240,0.06,'square',0.09,60);},push(){tone(392,0.08,'triangle',0.12,0);tone(523,0.12,'triangle',0.09,0);tone(165,0.16,'square',0.05,0);},buzz(){noise(0.20,0.12);tone(80,0.22,'sawtooth',0.08,-20);}};
})();

function drawBase(board){
  const {lines,ox,oy}=layout(board);
  for(let r=0;r<lines.length;r++)for(let c=0;c<(lines[r]||'').length;c++){
    const ch=(lines[r]||'')[c]||' ';const x=ox+c*TILE,y=oy+r*TILE;
    if(ch==='#'){
      const g=ctx.createLinearGradient(x,y,x,y+TILE);g.addColorStop(0,P.wallHi);g.addColorStop(1,P.wallSh);ctx.fillStyle=g;ctx.fillRect(x,y,TILE,TILE);
      for(let yy=y+6;yy<y+TILE;yy+=6){ctx.fillStyle='rgba(0,0,0,.22)';ctx.fillRect(x,yy,TILE,1);}
      ctx.fillStyle='rgba(255,255,255,.16)';ctx.fillRect(x,y,TILE,2);
    }else{
      const alt=((r+c)%2===0);
      const g=ctx.createLinearGradient(x,y,x,y+TILE);g.addColorStop(0,alt?P.floor:'#0c1018');g.addColorStop(1,P.floorAlt);ctx.fillStyle=g;ctx.fillRect(x,y,TILE,TILE);
      ctx.fillStyle='rgba(255,255,255,.04)';ctx.fillRect(x,y,TILE,1);
      if(ch==='.'||ch==='*'||ch==='+'){
        const cx=x+TILE/2,cy=y+TILE/2;
        const rg=ctx.createRadialGradient(cx,cy,2,cx,cy,9);rg.addColorStop(0,P.targetHi);rg.addColorStop(1,'transparent');
        ctx.fillStyle=rg;ctx.fillRect(x,y,TILE,TILE);
        ctx.fillStyle=P.target;ctx.beginPath();ctx.arc(cx,cy,7,0,Math.PI*2);ctx.fill();
        ctx.fillStyle=P.targetHi;ctx.beginPath();ctx.arc(cx,cy,3,0,Math.PI*2);ctx.fill();
      }
    }
  }
}
function drawCrate(x,y,onGoal){
  const body=onGoal?P.goal:P.crate, hi=onGoal?P.goalHi:P.crateHi;
  ctx.fillStyle='rgba(0,0,0,.34)';ctx.fillRect(x+3,y+4,TILE-6,TILE-6);
  ctx.fillStyle=P.crateSh;ctx.fillRect(x+2,y+2,TILE-6,TILE-6);
  const g=ctx.createLinearGradient(x+3,y+3,x+3,y+TILE-5);g.addColorStop(0,hi);g.addColorStop(1,body);
  ctx.fillStyle=g;ctx.fillRect(x+3,y+3,TILE-8,TILE-8);
  ctx.fillStyle=P.crateBand;ctx.fillRect(x+3,y+TILE/2-2,TILE-8,3);ctx.fillRect(x+TILE/2-2,y+3,3,TILE-8);
  ctx.fillStyle='rgba(255,255,255,.35)';ctx.fillRect(x+3,y+3,TILE-8,2);
}
function drawPlayer(x,y,t){
  const cx=x+TILE/2,cy=y+TILE/2,r=TILE/2-4;
  const g=ctx.createRadialGradient(cx-3,cy-4,r/4,cx,cy,r+2);g.addColorStop(0,P.playerHi);g.addColorStop(1,P.player);
  ctx.fillStyle='rgba(0,0,0,.30)';ctx.beginPath();ctx.ellipse(cx+2,cy+r+2,r*0.9,r/3,0,0,Math.PI*2);ctx.fill();
  ctx.fillStyle=g;ctx.beginPath();ctx.arc(cx,cy,r,0,Math.PI*2);ctx.fill();
  const blink = (Math.sin((t||0)*0.006)>0.92)?0.6:1;
  ctx.fillStyle=P.visor;ctx.fillRect(cx-5,cy-4,10,5);
  ctx.fillStyle=P.visorHi;ctx.globalAlpha=blink;ctx.fillRect(cx-4,cy-3,3,3);ctx.fillRect(cx+1,cy-3,3,3);ctx.globalAlpha=1;
  ctx.fillStyle='rgba(255,255,255,.55)';ctx.fillRect(cx-2,cy-8,4,2);
}
function burst(cx,cy,outcome){
  const n=outcome==='pushed'?14:outcome==='moved'?6:3;
  const color=outcome==='blocked'?'#ffb02e':outcome==='pushed'?'#ffb02e':'#4ee08a';
  for(let i=0;i<n;i++){particles.push({x:cx,y:cy,vx:(Math.random()-0.5)*2.2,vy:(Math.random()-1)*2,life:1,color});}
}
function updateParticles(){for(const p of particles){p.x+=p.vx;p.y+=p.vy;p.vy+=0.07;p.life-=0.028;}particles=particles.filter(p=>p.life>0);}
function drawParticles(){for(const p of particles){ctx.globalAlpha=p.life;ctx.fillStyle=p.color;ctx.fillRect(Math.round(p.x),Math.round(p.y),2,2);}ctx.globalAlpha=1;}

function drawHUD(status){
  ctx.fillStyle=P.bg;ctx.fillRect(0,0,320,HUD);
  const g=ctx.createLinearGradient(0,0,320,0);g.addColorStop(0,'rgba(255,176,46,.12)');g.addColorStop(1,'transparent');ctx.fillStyle=g;ctx.fillRect(0,0,320,HUD);
  ctx.fillStyle=P.dim;ctx.fillRect(0,HUD-1,320,1);
  ctx.fillStyle=P.amber;ctx.font='bold 10px ui-monospace,monospace';ctx.fillText('SHOWCASE CABINET  ·  TRACE',8,13);
  ctx.fillStyle=P.text;ctx.font='8px ui-monospace,monospace';ctx.fillText('ENTRANT '+DATA.entrant+'   LEVEL '+DATA.level,8,23);
  ctx.fillStyle=P.amber;ctx.fillText('RUN FREEZE '+DATA.freeze.slice(0,8).toUpperCase()+'   FULL '+DATA.freeze,8,32);
  ctx.fillStyle=P.dim;ctx.fillText('PLY '+(idx+1)+'/'+trace.length+'   MOVES '+DATA.moves+'   ATTEMPTS '+DATA.attempted+'   BLOCKED '+DATA.blocked+'   '+status,8,41);
}

function easeOutCubic(t){return 1-Math.pow(1-t,3)}
function renderStatic(board,status,now){
  const {ox,oy}=layout(board);
  ctx.fillStyle=P.bg;ctx.fillRect(0,0,320,240);
  drawBase(board);
  const e=entities(board);
  for(const c of e.crates) drawCrate(ox+c.c*TILE,oy+c.r*TILE,c.goal);
  if(e.player) drawPlayer(ox+e.player.c*TILE,oy+e.player.r*TILE,now);
  updateParticles();drawParticles();
  drawHUD(status||outcomeLabel(trace[idx].outcome));
}
function renderAnim(u,now){
  const {info,toBoard}=anim;
  const {ox,oy}=layout(toBoard);
  ctx.fillStyle=P.bg;ctx.fillRect(0,0,320,240);
  drawBase(toBoard);
  for(const c of info.finalCrates) drawCrate(ox+c.c*TILE,oy+c.r*TILE,c.goal);
  for(const m of info.moves){
    const x=ox+(m.from.c+(m.to.c-m.from.c)*u)*TILE;
    const y=oy+(m.from.r+(m.to.r-m.from.r)*u)*TILE;
    drawCrate(x,y,m.to.goal);
    if(Math.abs(u-1)<0.001) burst(x+TILE/2,y+TILE/2,anim.outcome);
  }
  const pm=info.playerMove;
  let px,py;
  if(pm){px=ox+(pm.from.c+(pm.to.c-pm.from.c)*u)*TILE;py=oy+(pm.from.r+(pm.to.r-pm.from.r)*u)*TILE;}
  else if(info.te.player){px=ox+info.te.player.c*TILE;py=oy+info.te.player.r*TILE;}
  // squash on landing
  const squash = (u>0.85)? 1-(u-0.85)/0.15*0.12 : 1;
  ctx.save(); ctx.translate(px+TILE/2,py+TILE/2); ctx.scale(1,squash); ctx.translate(-(px+TILE/2),-(py+TILE/2));
  drawPlayer(px,py,performance.now());
  ctx.restore();
  updateParticles();drawParticles();
  drawHUD('MOVING');
}

function updateSide(){
  const _pct = (trace.length>1) ? (idx/(trace.length-1))*100 : 0;
  document.getElementById('bar').style.left = _pct+'%';
  document.getElementById('mk').textContent=DATA.moves;
  document.getElementById('ak').textContent=DATA.attempted;
  document.getElementById('bk').textContent=DATA.blocked;
  document.getElementById('dk').textContent=DATA.distinctBoards;
  document.getElementById('ended').textContent=DATA.ended;
  document.getElementById('freeze').textContent=DATA.freeze.slice(0,8).toUpperCase();
  document.getElementById('pin').textContent=DATA.pin;
  document.getElementById('fent').textContent=DATA.entrant;
  document.getElementById('flvl').textContent=DATA.level;
  document.getElementById('ffreeze').textContent=DATA.freeze;
  const stream=document.getElementById('stream'); let h='';
  for(let i=0;i<trace.length;i++){const t=trace[i];h+='<div class="row'+(i===idx?' cur':'')+'"><span>'+String(t.ply).padStart(2,'0')+'</span><span class="tag '+t.outcome+'">'+t.token+'</span><span>'+outcomeLabel(t.outcome)+'</span></div>';}
  stream.innerHTML=h;
  const cur=stream.querySelector('.cur'); if(cur)cur.scrollIntoView({block:'nearest'});
}

function shake(){const m=document.querySelector('.monitor');m.animate([{transform:'translate(0,0) scale(1)'},{transform:'translate(5px,3px) scale(1.005)'},{transform:'translate(-4px,2px) scale(.998)'},{transform:'translate(3px,-2px)'},{transform:'translate(0,0) scale(1)'}],{duration:200});}

function goto(i){
  if(i<0)i=0; if(i>=trace.length)i=trace.length-1;
  const prevBoard=currentBoard; const newBoard=trace[i].board; const outcome=trace[i].outcome;
  idx=i; currentBoard=newBoard; updateSide();
  if(anim){cancelAnimationFrame(rafId);anim=null;}
  if(i===0 || prevBoard===newBoard){
    if(outcome==='pushed'){burst(...canvasTileCenter(newBoard), 'pushed');}
    else if(outcome!=='blocked'){burst(...canvasTileCenter(newBoard), 'moved');}
    renderStatic(newBoard,outcomeLabel(outcome),performance.now());
    if(outcome==='blocked'){ /* no cue: legal wall-bump, not an illegal move (RENDER_SPEC cue map reserves buzz for illegal) */ }
    else if(outcome==='pushed'){AUDIO.push();} else if(outcome==='moved'){AUDIO.clack();}
    if(!idleRaf) idleRaf=requestAnimationFrame(idleLoop);
  }else{
    if(outcome!=='blocked'){ burst(...canvasTileCenter(newBoard), outcome); }
    const info=crateMoves(prevBoard,newBoard);
    const movedPlayer = info.playerMove && (info.playerMove.from.r!==info.playerMove.to.r||info.playerMove.from.c!==info.playerMove.to.c);
    const movedCrate = info.moves.length>0;
    if(!movedPlayer && !movedCrate){
      // silence for blocked: no burst
      renderStatic(newBoard,outcomeLabel(outcome),performance.now());
      if(outcome==='blocked'){ /* no cue: legal wall-bump, not an illegal move (RENDER_SPEC cue map reserves buzz for illegal) */ }
    }else{
      if(idleRaf){cancelAnimationFrame(idleRaf);idleRaf=null;}
      anim={start:performance.now(),dur:movedCrate?320:210,outcome,info,toBoard:newBoard};
      rafId=requestAnimationFrame(tick);
    }
  }
}
function canvasTileCenter(board){const {ox,oy}=layout(board);const e=entities(board);const p=e.player||{r:1,c:1};return [ox+p.c*TILE+TILE/2, oy+p.r*TILE+TILE/2];}
function tick(now){
  if(idleRaf){cancelAnimationFrame(idleRaf);idleRaf=null;}
  if(!anim)return;
  const t=Math.min(1,(now-anim.start)/anim.dur);
  renderAnim(easeOutCubic(t),now);
  if(t<1) rafId=requestAnimationFrame(tick);
  else {
    const outcome=anim.outcome;
    const info=anim.info;
    for(const m of info.moves){const {ox,oy}=layout(anim.toBoard); burst(ox+m.to.c*TILE+TILE/2, oy+m.to.r*TILE+TILE/2, outcome);}
    burst(...canvasTileCenter(anim.toBoard), outcome);
    anim=null;
    renderStatic(currentBoard,outcomeLabel(outcome),performance.now());
    if(outcome==='blocked'){ /* no cue: legal wall-bump, not an illegal move (RENDER_SPEC cue map reserves buzz for illegal) */ }
    else if(outcome==='pushed'){AUDIO.push();} else if(outcome==='moved'){AUDIO.clack();}
    idleRaf=requestAnimationFrame(idleLoop);
  }
}

// idle blink loop (kept cheap: only redraws, no data change)
let idleRaf=null;
function idleLoop(now){renderStatic(currentBoard,outcomeLabel(trace[idx].outcome),now); idleRaf=requestAnimationFrame(idleLoop);}
// only start idle when not animating; restart after init

let playing=false,timer=null;
function playStep(){if(anim)return;if(idx>=trace.length-1){playing=false;clearInterval(timer);timer=null;document.getElementById('play').textContent='PLAY';return;}goto(idx+1);}
document.getElementById('play').onclick=()=>{playing=!playing;document.getElementById('play').textContent=playing?'PAUSE':'PLAY';if(playing)timer=setInterval(playStep,460);else{clearInterval(timer);timer=null;}};
document.getElementById('step').onclick=()=>{if(timer){clearInterval(timer);timer=null;playing=false;document.getElementById('play').textContent='PLAY';}playStep();};
document.getElementById('back').onclick=()=>{if(idx>0)goto(idx-1);};
document.getElementById('reset').onclick=()=>{if(timer){clearInterval(timer);timer=null;playing=false;document.getElementById('play').textContent='PLAY';}particles=[];goto(0);};
document.addEventListener('keydown',e=>{if(e.key===' '){e.preventDefault();document.getElementById('play').click();} if(e.key==='ArrowRight')document.getElementById('step').click(); if(e.key==='ArrowLeft')document.getElementById('back').click();});

// cabinet tilt
const cab=document.getElementById('cab');
document.addEventListener('mousemove',e=>{const r=cab.getBoundingClientRect();const x=(e.clientX-r.left)/r.width-0.5;const y=(e.clientY-r.top)/r.height-0.5;cab.style.transform='rotateY('+(x*5)+'deg) rotateX('+(-y*3.5)+'deg)';});
document.addEventListener('mouseleave',()=>{cab.style.transform='';});

updateSide();
goto(0);
particles=[];
// start idle blink/pulse (lightweight)
idleRaf=requestAnimationFrame(idleLoop);
// pause idle loop while animating by checking anim in tick entry
</script>
</body>
</html>
'''

    template = template.replace("rafId=requestAnimationFrame(tick);", "rafId=requestAnimationFrame(tick);")
    template = template.replace("idleRaf=requestAnimationFrame(idleLoop);", "idleRaf=requestAnimationFrame(idleLoop);")
    html = template.replace("__DATA__", data_json)
    # calls to renderAnim use global now etc okay.
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print("wrote", OUT, "bytes", os.path.getsize(OUT))

if __name__ == "__main__":
    main()