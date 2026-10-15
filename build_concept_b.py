#!/usr/bin/env python3
"""Build Concept B (Canvas Pixel) -- 8-bit cabinet rendered on a scaled canvas.

Weight: canvas 2D at 320x240 scaled 2x, bitmap text via fillText (system font at pixel
sizes, no external font), WebAudio three-channel cues, CSS CRT scanlines/vignette.
"""
import json, os
ARENA = os.path.dirname(os.path.abspath(__file__))
PROBE = os.path.join(ARENA, "probes_RUN_20261010-072252.json")
OUT = os.path.join(ARENA, "arcade_concept_b_canvas.html")
TRACE_FREEZE = "186f561facd44916"

def main():
    d = json.load(open(PROBE))
    c = [x for x in d["cells"] if x.get("entrant")=="Qwen3.5-9B-Q4_K_M" and x.get("level")=="02_two_boxes"][0]
    trace = [{"ply":int(t["ply"]),"token":t["token"],"action":t["action"],"outcome":t["outcome"],"board":t["board"]} for t in c["trace"]]
    data = {"entrant":c["entrant"],"level":c["level"],"moves":int(c["moves"]),"attempted":int(c["attempted"]),"blocked":int(c["blocked"]),"not_an_action":int(c["not_an_action"]),"give_up":int(c["give_up"]),"ended":c["ended"],"distinctBoards":len(set(t["board"] for t in c["trace"])),"trace":trace,"freeze":TRACE_FREEZE}
    data_json = json.dumps(data, separators=(",",":"))
    template = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>CONCEPT B · CANVAS PIXEL CABINET</title>
<style>
  html,body{margin:0;height:100%;background:#020203;color:#d6d6e0;font-family:ui-monospace,Menlo,monospace}
  .wrap{display:flex;flex-direction:column;align-items:center;padding:10px;gap:8px}
  canvas{image-rendering:pixelated;border:2px solid #333;box-shadow:0 0 0 2px #000,6px 6px 0 #000}
  .row{display:flex;gap:6px;flex-wrap:wrap;justify-content:center;max-width:640px}
  button{background:#000;border:1px solid #444;color:#d6d6e0;font:inherit;font-size:11px;padding:4px 8px;cursor:pointer}
  button:hover{border-color:#ffb02e;color:#ffb02e}
  .info{font-size:10px;color:#7a7a8c;max-width:640px;line-height:1.4}
  .info b{color:#d6d6e0}
  footer{font-size:9px;color:#5a5a6a;max-width:640px;border-top:1px solid #2a2a33;padding-top:4px}
</style>
</head>
<body>
<div class="wrap">
  <div style="font-size:12px;letter-spacing:.12em;color:#ffb02e">THE ARCADE · CONCEPT B · CANVAS 320x240 @2x · CRT PASS · AUDIO</div>
  <canvas id="screen" width="320" height="240"></canvas>
  <div class="row">
    <button id="back">STEP BACK</button>
    <button id="play">PLAY</button>
    <button id="step">STEP</button>
    <button id="reset">RESET</button>
  </div>
  <div class="info" id="info"></div>
  <footer>WEIGHT: canvas 2D pixel compositing (CPU only), WebAudio oscillators, CSS scanlines + vignette.
  Data embedded verbatim. Freeze differs from pilot run of record (7134c3e8); never pooled.
  Unsolved, not a failure, not a zero. Catalogued cabinets not run do not appear.</footer>
</div>
<script>
const DATA=__DATA__;
const trace=DATA.trace;
const cvs=document.getElementById('screen'), ctx=cvs.getContext('2d');
const SCALE=2;
ctx.imageSmoothingEnabled=false;
const PAL={bg:'#020203', wall:'#3a3a4a', floor:'#0a0a12', player:'#30d158', box:'#ffb02e', target:'#2a2a3a', boxT:'#ff3b30', playerT:'#5ac8fa', text:'#d6d6e0', dim:'#7a7a8c', red:'#ff3b30', amber:'#ffb02e', green:'#30d158'};
function pxText(str,x,y,color,size){ ctx.fillStyle=color; ctx.font='bold '+size+'px ui-monospace,monospace'; ctx.fillText(str,x,y); }
function drawBoard(b,ox,oy){
  const lines=b.split('\n'); const tw=8,th=10;
  for(let r=0;r<lines.length;r++) for(let cc=0;cc<lines[r].length;cc++){
    const ch=lines[r][cc];
    let color=PAL.floor;
    if(ch==='#') color=PAL.wall;
    if(ch==='.') color=PAL.target;
    if(ch==='$') color=PAL.box;
    if(ch==='*') color=PAL.boxT;
    if(ch==='@') color=PAL.player;
    if(ch==='+') color=PAL.playerT;
    ctx.fillStyle=color; ctx.fillRect(ox+cc*tw, oy+r*th, tw, th);
    if(ch==='@'||ch==='+'||ch==='$'||ch==='*'){
      ctx.fillStyle='#000'; ctx.fillRect(ox+cc*tw+2, oy+r*th+2, tw-4, th-4);
      ctx.fillStyle=color; ctx.fillRect(ox+cc*tw+3, oy+r*th+3, tw-6, th-6);
    }
  }
}
const AUDIO=(function(){let ctx=null;function ensure(){if(!ctx)try{ctx=new (window.AudioContext||window.webkitAudioContext)()}catch(e){}return ctx;}
function tone(f,d,t,g){const c=ensure();if(!c)return;const o=c.createOscillator(),g2=c.createGain();o.type=t;o.frequency.value=f;g2.gain.value=g;o.connect(g2);g2.connect(c.destination);o.start();g2.gain.exponentialRampToValueAtTime(0.001,c.currentTime+d);o.stop(c.currentTime+d);}
function noise(d,g){const c=ensure();if(!c)return;const buf=c.createBuffer(1,c.sampleRate*d,c.sampleRate);const dd=buf.getChannelData(0);for(let i=0;i<dd.length;i++)dd[i]=(Math.random()*2-1)*0.4;const s=c.createBufferSource();s.buffer=buf;const g2=c.createGain();g2.gain.value=g;s.connect(g2);g2.connect(c.destination);s.start();g2.gain.exponentialRampToValueAtTime(0.001,c.currentTime+d);s.stop(c.currentTime+d);}
return {blip(){tone(880,0.05,'square',0.07);},clack(){tone(220,0.06,'square',0.09);},push(){tone(330,0.09,'triangle',0.10);},buzz(){noise(0.18,0.10);}};}());
let idx=-1, playing=false, timer=null;
function outcomeLabel(o){return o==='pushed'?'PUSHED':o==='moved'?'MOVED':o==='blocked'?'BLOCKED':String(o).toUpperCase();}
function render(){
  if(idx<0) idx=0;
  const t=trace[idx];
  ctx.fillStyle=PAL.bg; ctx.fillRect(0,0,320,240);
  pxText('SOKOBAN / CONCEPT B CANVAS',6,12,PAL.amber,9);
  pxText('ENTRANT '+DATA.entrant,6,24,PAL.text,8);
  pxText('LEVEL '+DATA.level+'   FREEZE '+DATA.freeze.slice(0,8).toUpperCase(),6,34,PAL.amber,8);
  pxText('PLY '+(idx+1)+'/'+trace.length+'   '+outcomeLabel(t.outcome),6,44,PAL.text,8);
  drawBoard(t.board, 6, 52);
  const by=52+ (t.board.split('\n').length*10)+6;
  pxText('MOVES '+DATA.moves+'  ATTEMPTED '+DATA.attempted+'  BLOCKED '+DATA.blocked,6,by,PAL.text,8);
  pxText('STATUS: UNSOLVED (not a failure, not a zero)',6,by+11,PAL.red,8);
  // move stream tail
  let sy=by+24; pxText('MOVE STREAM',6,sy,PAL.dim,8); sy+=10;
  const start=Math.max(0,idx-6);
  for(let i=start;i<=Math.min(trace.length-1,start+8);i++){
    const tt=trace[i]; let color=PAL.dim;
    if(i===idx) color=PAL.amber;
    else if(tt.outcome==='blocked') color=PAL.red;
    else if(tt.outcome==='pushed') color=PAL.green;
    pxText(String(tt.ply).padStart(2,'0')+' '+(tt.action||'-')+' '+outcomeLabel(tt.outcome),6,sy,color,8); sy+=9;
  }
}
function goto(i){ if(i<0)i=0; if(i>=trace.length)i=trace.length-1; idx=i; render(); }
function playStep(){ if(idx>=trace.length-1){playing=false;clearInterval(timer);timer=null;document.getElementById('play').textContent='PLAY';return;} goto(idx+1); const t=trace[idx]; if(t.outcome==='blocked')AUDIO.buzz(); else if(t.outcome==='pushed')AUDIO.push(); else if(t.outcome==='moved')AUDIO.clack(); }
document.getElementById('play').onclick=()=>{playing=!playing;document.getElementById('play').textContent=playing?'PAUSE':'PLAY'; if(playing)timer=setInterval(playStep,300);else{clearInterval(timer);timer=null;}};
document.getElementById('step').onclick=()=>{if(timer){clearInterval(timer);timer=null;playing=false;document.getElementById('play').textContent='PLAY';}playStep();};
document.getElementById('back').onclick=()=>{if(idx>0)goto(idx-1);};
document.getElementById('reset').onclick=()=>{if(timer){clearInterval(timer);timer=null;playing=false;document.getElementById('play').textContent='PLAY';}goto(0);};
document.addEventListener('keydown',e=>{if(e.key===' ') {e.preventDefault();document.getElementById('play').click();} if(e.key==='ArrowRight')document.getElementById('step').click(); if(e.key==='ArrowLeft')document.getElementById('back').click();});
document.getElementById('info').innerHTML='ENTRANT <b>'+DATA.entrant+'</b> · LEVEL <b>'+DATA.level+'</b> · '
  +'PLIES <b>'+trace.length+'</b> · DISTINCT BOARDS <b>'+DATA.distinctBoards+'</b> · '
  +'MOVES <b>'+DATA.moves+'</b> / ATTEMPTED <b>'+DATA.attempted+'</b> (blocked '+DATA.blocked+', not_an_action '
  +DATA.not_an_action+', give_up '+DATA.give_up+', ended '+DATA.ended+'). '
  +'Freeze '+DATA.freeze+' differs from pilot run of record (7134c3e8). '
  +'Catalogued cabinets not run do not appear.';
goto(0);
</script>
</body>
</html>
'''
    html = template.replace("__DATA__", data_json)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print("wrote", OUT, "bytes", os.path.getsize(OUT))

if __name__ == "__main__":
    main()