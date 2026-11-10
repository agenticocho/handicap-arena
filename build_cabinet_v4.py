#!/usr/bin/env python3
import json

trace = json.load(open('/Users/mikebird/arena/handicap-arena/traces/stump_calibrated_ornith9b_lfm1.7b_p3.json'))

a_rows = [r for r in trace['rows'] if r['arm'] == 'A']
questions = []
for ar in a_rows:
    questions.append({'qid': ar['qid'], 'text': ar['question'], 'illposed': ar['illposed'], 'truth': ar['truth']})

data = {
    'model_a': {'name': 'ornith9b', 'endpoint': 'http://127.0.0.1:8360/v1/chat/completions'},
    'model_b': {'name': 'lfm3-1.7b', 'endpoint': 'http://127.0.0.1:8376/v1/chat/completions'},
    'digest': trace['grammar_digest'],
    'questions': questions,
}
trace_json = json.dumps(data, separators=(',', ':'))

html = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
<title>STUMP — Live Play v4 — illposed-v1</title>
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  :root{--bg:#0a0a14;--panel:#12121e;--border:#2a2a38;--text:#e7eaf2;--dim:#7b7a60;--green:#3aff3a;--gold:#ffcc33;--red:#ff3a3a;--grey:#7b7a60;--ma:#3aff3a;--mb:#3a8aff;--accent:#ffcc33}
  body{background:#000;display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:'Courier New',monospace;color:var(--text);overflow:hidden}
  #cabinet{position:relative;width:960px;height:540px;border:6px solid var(--accent);border-radius:12px;box-shadow:0 0 40px rgba(255,204,51,.3),inset 0 0 20px rgba(0,0,0,.5);background:var(--bg);overflow:hidden}
  #screen{position:relative;width:100%;height:100%;image-rendering:pixelated;overflow:hidden}
  #screen::before{content:'';position:absolute;inset:0;background:repeating-linear-gradient(0deg,transparent,transparent 1px,rgba(0,0,0,.15) 1px,rgba(0,0,0,.15) 2px);pointer-events:none;z-index:10}
  #screen::after{content:'';position:absolute;inset:0;background:radial-gradient(ellipse at center,transparent 60%,rgba(0,0,0,.4) 100%);pointer-events:none;z-index:11}
  #marquee{position:absolute;top:0;left:0;right:0;height:40px;background:linear-gradient(180deg,#1a1a2e,#0a0a14);border-bottom:2px solid var(--accent);display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:bold;color:var(--accent);letter-spacing:2px;text-transform:uppercase;z-index:5;overflow:hidden}
  #marquee span{white-space:nowrap}
  #playfield{position:absolute;top:40px;left:0;right:0;bottom:0;display:flex;flex-direction:column;padding:8px 12px;gap:6px}
  #question-panel{height:56px;display:flex;align-items:center;justify-content:center;text-align:center;padding:4px 12px;border:2px solid var(--accent);background:rgba(255,204,51,.05);position:relative;overflow:hidden}
  #question-text{font-size:13px;line-height:1.4;color:var(--text);max-width:100%;word-wrap:break-word;opacity:0;transition:opacity .1s}
  #question-text.visible{opacity:1}
  #question-text::after{content:'';position:absolute;bottom:2px;left:50%;transform:translateX(-50%);width:60%;height:1px;background:var(--accent);opacity:.4}
  #slots{display:flex;justify-content:space-between;gap:12px;height:28px}
  .slot{flex:1;display:flex;align-items:center;gap:8px;padding:2px 8px;border:2px solid var(--border);background:var(--panel);transition:border-color .2s}
  .slot.a{border-color:var(--ma)}.slot.b{border-color:var(--mb)}
  .slot-name{font-size:11px;font-weight:bold;min-width:70px}
  .slot.a .slot-name{color:var(--ma)}.slot.b .slot-name{color:var(--mb)}
  .slot-bar{flex:1;height:12px;background:#1a1a2e;border:1px solid var(--border);display:flex;gap:1px;padding:1px}
  .slot-bar .seg{flex:1;background:transparent;transition:background .1s}
  .slot-bar .seg.filled-a{background:var(--ma)}.slot-bar .seg.filled-b{background:var(--mb)}
  .slot-score{font-size:20px;font-weight:bold;min-width:28px;text-align:right;transition:transform .15s}
  .slot.a .slot-score{color:var(--ma)}.slot.b .slot-score{color:var(--mb)}
  .slot-score.pop{transform:scale(1.3)}
  .slot-status{font-size:9px;color:var(--dim);min-width:60px;text-align:right}
  #lanes{display:flex;flex-direction:column;gap:4px;flex:1}
  .lane{height:36px;display:flex;align-items:center;position:relative;background:#0a0a14;border:1px solid var(--border);overflow:hidden;transition:background .05s}
  .lane-band{width:4px;height:100%;flex-shrink:0}
  .lane-label{font-size:10px;font-weight:bold;letter-spacing:1px;padding-left:8px;min-width:110px}
  .lane-dots{flex:1;display:flex;justify-content:space-between;align-items:center;padding:0 12px;position:relative}
  .dot{width:20px;height:20px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:9px;font-weight:bold;color:#000;opacity:0;transform:scale(0);transition:transform .1s,opacity .1s}
  .dot.visible{opacity:1;transform:scale(1)}.dot.a{background:var(--ma)}.dot.b{background:var(--mb)}
  .lane.flash{background:rgba(255,255,255,.08)}
  #truth-marker{height:16px;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:bold;color:var(--gold)}
  #truth-marker .q{color:var(--gold);animation:blink 1s infinite}
  #verdict-line{height:16px;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:bold;gap:12px}
  #readout{height:16px;display:flex;align-items:center;justify-content:center;font-size:9px;color:var(--dim);gap:8px}
  #readout .score{color:var(--gold)}
  #controls{position:absolute;bottom:4px;right:8px;display:flex;gap:8px;z-index:20}
  .btn{font-family:inherit;font-size:9px;padding:2px 6px;background:var(--panel);border:1px solid var(--border);color:var(--dim);cursor:pointer;border-radius:2px}
  .btn:hover{border-color:var(--accent);color:var(--accent)}.btn.active{background:var(--accent);color:#000}
  #attract{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;background:var(--bg);z-index:30;gap:12px}
  #attract h1{font-size:32px;color:var(--accent);letter-spacing:4px;text-shadow:0 0 10px var(--accent)}
  #attract .sub{font-size:11px;color:var(--dim)}
  #attract .coin{font-size:14px;color:var(--gold);animation:blink 1s infinite;margin-top:20px;cursor:pointer}
  #attract .preview{font-size:11px;color:var(--text);max-width:400px;text-align:center;margin-top:12px;min-height:30px}
  #attract .lanes-preview{display:flex;flex-direction:column;gap:2px;margin-top:12px;width:300px}
  .lane-preview{height:8px;border:1px solid var(--border);background:#0a0a14;position:relative}
  .lane-preview .band{position:absolute;left:0;top:0;bottom:0;width:2px}
  @keyframes blink{0%,50%{opacity:1}51%,100%{opacity:0}}
  @keyframes breathe{0%,100%{opacity:.3}50%{opacity:.7}}
  .breathing{animation:breathe 2s infinite}
  #spinner{display:inline-block;width:10px;height:10px;border:2px solid var(--border);border-top-color:var(--accent);border-radius:50%;animation:spin .6s linear infinite}
  @keyframes spin{to{transform:rotate(360deg)}}
  #phase-label{position:absolute;top:4px;right:8px;font-size:8px;color:var(--dim);z-index:5}
  #conn-status{position:absolute;top:4px;left:8px;font-size:8px;color:var(--dim);z-index:5}
  #conn-status.ok{color:var(--green)}#conn-status.err{color:var(--red)}
  .thinking{animation:pulse 1s infinite}
  @keyframes pulse{0%,100%{opacity:.4}50%{opacity:1}}
  #live-answer{position:absolute;bottom:80px;left:50%;transform:translateX(-50%);font-size:10px;color:var(--text);z-index:20;max-width:400px;text-align:center}
  #error-msg{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-size:12px;color:var(--red);z-index:30;text-align:center;max-width:400px}
  #phase-banner{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-size:18px;font-weight:bold;color:var(--accent);text-align:center;z-index:20;text-shadow:0 0 20px var(--accent);pointer-events:none}
  #progress-bar{position:absolute;bottom:60px;left:50%;transform:translateX(-50%);width:300px;height:8px;background:#1a1a2e;border:1px solid var(--border);z-index:20}
  #progress-fill{height:100%;background:var(--accent);width:0%;transition:width .3s}
  #progress-label{position:absolute;bottom:40px;left:50%;transform:translateX(-50%);font-size:10px;color:var(--dim);z-index:20}
</style>
</head>
<body>
<div id="cabinet">
  <div id="screen">
    <div id="marquee"><span>STUMP · LIVE · illposed-v1 · ornith9b vs lfm3-1.7b</span></div>
    <div id="playfield" style="display:none">
      <div id="question-panel"><div id="question-text"></div></div>
      <div id="slots">
        <div class="slot a"><span class="slot-name">ornith9b</span><div class="slot-bar" id="bar-a"></div><span class="slot-score" id="score-a">0</span><span class="slot-status" id="status-a"></span></div>
        <div class="slot b"><span class="slot-name">lfm3-1.7b</span><div class="slot-bar" id="bar-b"></div><span class="slot-score" id="score-b">0</span><span class="slot-status" id="status-b"></span></div>
      </div>
      <div id="lanes">
        <div class="lane" data-lane="REFUSED" style="border-left:4px solid #3aff3a"><span class="lane-label" style="color:#3aff3a">REFUSED</span><div class="lane-dots"><div class="dot a" id="dot-a-refused">A</div><div class="dot b" id="dot-b-refused">B</div></div></div>
        <div class="lane" data-lane="PARAMETRIC" style="border-left:4px solid #ffcc33"><span class="lane-label" style="color:#ffcc33">PARAMETRIC</span><div class="lane-dots"><div class="dot a" id="dot-a-parametric">A</div><div class="dot b" id="dot-b-parametric">B</div></div></div>
        <div class="lane" data-lane="CONFABULATED" style="border-left:4px solid #ff3a3a"><span class="lane-label" style="color:#ff3a3a">CONFABULATED</span><div class="lane-dots"><div class="dot a" id="dot-a-confabulated">A</div><div class="dot b" id="dot-b-confabulated">B</div></div></div>
        <div class="lane" data-lane="MALFORMED" style="border-left:4px solid #7b7a60"><span class="lane-label" style="color:#7b7a60">MALFORMED</span><div class="lane-dots"><div class="dot a" id="dot-a-malformed">A</div><div class="dot b" id="dot-b-malformed">B</div></div></div>
      </div>
      <div id="truth-marker"><span class="q">?</span></div>
      <div id="verdict-line"></div>
      <div id="readout">Q <span id="qnum">1</span> / <span id="qtotal">30</span> · A: <span class="score" id="ra">0</span> B: <span class="score" id="rb">0</span> · CLOCK: <span id="clock">0.0</span>s</div>
    </div>
    <div id="phase-banner" style="display:none"></div>
    <div id="progress-bar" style="display:none"><div id="progress-fill"></div></div>
    <div id="progress-label" style="display:none"></div>
    <div id="live-answer" style="display:none"></div>
    <div id="error-msg" style="display:none"></div>
    <div id="attract">
      <h1>STUMP</h1>
      <div class="sub">LIVE · illposed-v1 · ornith9b vs lfm3-1.7b</div>
      <div class="sub" style="font-size:9px;margin-top:4px;color:var(--dim)">Servers must be running. Check connection status (top-left). Must be LIVE to play.</div>
      <div class="lanes-preview">
        <div class="lane-preview"><div class="band" style="background:#3aff3a"></div></div>
        <div class="lane-preview"><div class="band" style="background:#ffcc33"></div></div>
        <div class="lane-preview"><div class="band" style="background:#ff3a3a"></div></div>
        <div class="lane-preview"><div class="band" style="background:#7b7a60"></div></div>
      </div>
      <div class="preview" id="preview-text"></div>
      <div class="coin" id="coin-btn">INSERT COIN</div>
      <div class="sub" style="font-size:9px;margin-top:8px;color:var(--red);cursor:pointer" id="clear-btn">CLEAR SAVED PROGRESS</div>
    </div>
    <div id="phase-label"></div>
    <div id="conn-status">connecting...</div>
    <div id="controls">
      <button class="btn" id="mute-btn">♪ ON</button>
      <button class="btn" id="auto-btn">AUTO</button>
      <button class="btn" id="next-btn">NEXT ▶</button>
      <button class="btn" id="export-btn">EXPORT</button>
    </div>
  </div>
</div>
<script>
const TRACE = ''' + trace_json + r''';
const Q = TRACE.questions;

// === Recorded answers (persisted to localStorage) ===
let recordedA = JSON.parse(localStorage.getItem('stump_recordedA') || '[]');
let recordedB = JSON.parse(localStorage.getItem('stump_recordedB') || '[]');
let modelAAnswers = recordedA.map(r=>r.answer);
let modelBAnswers = recordedB.map(r=>r.answer);
let modelASecs = recordedA.map(r=>r.secs);
let modelBSecs = recordedB.map(r=>r.secs);

// === Audio Engine ===
let audioCtx = null, muted = false, masterGain = null;
function initAudio(){ if(audioCtx) return; audioCtx=new (window.AudioContext||window.webkitAudioContext)(); masterGain=audioCtx.createGain(); masterGain.gain.value=0.3; masterGain.connect(audioCtx.destination); }
function tone(freq,dur,type='square',vol=0.15){ if(muted||!audioCtx) return; const o=audioCtx.createOscillator(); const g=audioCtx.createGain(); o.type=type;o.frequency.value=freq; g.gain.value=vol;g.gain.exponentialRampToValueAtTime(0.001,audioCtx.currentTime+dur); o.connect(g);g.connect(masterGain); o.start();o.stop(audioCtx.currentTime+dur); }
function noise(dur,vol=0.1){ if(muted||!audioCtx) return; const buf=audioCtx.createBuffer(1,audioCtx.sampleRate*dur,audioCtx.sampleRate); const d=buf.getChannelData(0); for(let i=0;i<d.length;i++) d[i]=Math.random()*2-1; const s=audioCtx.createBufferSource(); const g=audioCtx.createGain(); s.buffer=buf;g.gain.value=vol;g.gain.exponentialRampToValueAtTime(0.001,audioCtx.currentTime+dur); s.connect(g);g.connect(masterGain); s.start();s.stop(audioCtx.currentTime+dur); }
function cue(name){ switch(name){ case 'blip': tone(440,.08);tone(660,.08);break; case 'blip_high': tone(660,.08);tone(880,.08);break; case 'buzz': noise(.15,.2);break; case 'fanfare': tone(523,.1);setTimeout(()=>tone(659,.1),100);setTimeout(()=>tone(784,.15),200);break; case 'descend': tone(784,.1);setTimeout(()=>tone(659,.1),100);setTimeout(()=>tone(523,.15),200);break; case 'tick': noise(.03,.15);break; case 'chime': tone(880,.06,'triangle');break; case 'coin': noise(.05,.3);setTimeout(()=>tone(1200,.1),50);break; } }
let attractLoop=null;
function startAttractLoop(){ if(attractLoop) return; attractLoop=setInterval(()=>{ if(muted||!audioCtx) return; const bars=[[262,330,392,330],[294,349,440,349],[330,392,494,392],[262,330,392,262]]; const bar=bars[Math.floor(Date.now()/500)%4]; tone(bar[0],.12,'square',.08); setTimeout(()=>tone(bar[1],.12,'square',.06),125); setTimeout(()=>tone(bar[2],.12,'square',.08),250); setTimeout(()=>tone(bar[3],.12,'square',.06),375); tone(bar[0]/2,.2,'triangle',.06); },500); }
function stopAttractLoop(){ if(attractLoop){clearInterval(attractLoop);attractLoop=null} }

// === Live Model Call ===
const ANSWER_PROMPT = 'Answer this Stump question. Output JSON only: {"answer": "..."}. Question: ';
async function callModel(endpoint, question, modelName, onTick, onStatus) {
  const t0 = performance.now();
  let clockInterval = setInterval(() => { const elapsed = (performance.now() - t0) / 1000; if (onTick) onTick(elapsed); }, 100);
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 60000); // 60s timeout
  try {
    if (onStatus) onStatus('thinking...');
    const resp = await fetch(endpoint, { method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ model: modelName, messages: [{'role':'user','content': ANSWER_PROMPT + question}], max_tokens: 400, temperature: 0.0, response_format: {type:'json_object'}, chat_template_kwargs: {enable_thinking: true} }) ,
      signal: controller.signal });
    clearTimeout(timeoutId);
    const data = await resp.json();
    const elapsed = (performance.now() - t0) / 1000;
    clearInterval(clockInterval);
    const msg = data.choices[0].message;
    let answer = msg.content || '';
    if (answer) { try { const parsed = JSON.parse(answer); if (parsed && parsed.answer) answer = parsed.answer; } catch(e) {} }
    if (!answer || answer === msg.content) { const rc = msg.reasoning_content || ''; const m = rc.match(/"answer"\s*:\s*"([^"]+)"/); if (m) answer = m[1]; }
    if (!answer || answer === '...') { const m = (msg.content || '').match(/"answer"\s*:\s*"([^"]+)"/); if (m) answer = m[1]; }
    if (!answer || answer === '...') {
      const retryResp = await fetch(endpoint, { method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ model: modelName, messages: [{'role':'user','content': 'Answer: ' + question}], max_tokens: 200, temperature: 0.0 }) , signal: controller.signal });
      const retryData = await retryResp.json();
      const retryMsg = retryData.choices[0].message;
      answer = retryMsg.content || '';
      try { const parsed = JSON.parse(answer); if (parsed && parsed.answer) answer = parsed.answer; } catch(e) {}
      if (!answer || answer === '...') { const m = answer.match(/"answer"\s*:\s*"([^"]+)"/); if (m) answer = m[1]; }
    }
    if (onStatus) onStatus(elapsed.toFixed(1)+'s');
    return {answer: (answer || '').trim(), secs: elapsed, error: null, finish: data.choices[0].finish_reason};
  } catch(e) {
    clearInterval(clockInterval);
    clearTimeout(timeoutId);
    if (e.name === 'AbortError') {
      if (onStatus) onStatus('TIMEOUT');
      document.getElementById('error-msg').textContent = 'Model timed out after 60s. Skipping question.';
      document.getElementById('error-msg').style.display = 'block';
      setTimeout(()=>{ document.getElementById('error-msg').style.display='none'; }, 5000);
      return {answer: null, secs: 60, error: 'timeout'};
    }
    if (onStatus) onStatus('ERROR');
    document.getElementById('error-msg').textContent = 'Model call failed: ' + e.message;
    document.getElementById('error-msg').style.display = 'block';
    setTimeout(()=>{ document.getElementById('error-msg').style.display='none'; }, 5000);
    return {answer: null, secs: (performance.now() - t0) / 1000, error: e.message};
  }
}

// === Game State ===
let qi=0, scoreA=0, scoreB=0, state='attract';
let autoPlay=false;
let phase='attract';

function classify(answer){ if(!answer||answer===''||answer==='...'||answer==='…') return 'MALFORMED'; const s=answer.trim().toLowerCase(); if(s.includes('cannot be determined')||s.includes('insufficient')||s.includes('not enough')||s.includes('unknown')) return 'REFUSED'; if(s.includes('x -')||s.includes('x-')||s.includes('x +')||s.includes('x+')||/^[a-z]\s*[-+]\s*\d/.test(s)) return 'PARAMETRIC'; if(/^\d+(\.\d+)?$/.test(s)) return 'CONFABULATED'; if(s.includes('cannot')||s.includes('not possible')) return 'REFUSED'; return 'CONFABULATED'; }
function isCorrect(answer, truth, illposed){ if(!answer) return false; if(!illposed) return answer.trim()===truth.trim(); const cls=classify(answer); return cls==='REFUSED'||cls==='PARAMETRIC'; }

// === DOM refs ===
const attract=document.getElementById('attract');
const playfield=document.getElementById('playfield');
const qText=document.getElementById('question-text');
const scoreAEl=document.getElementById('score-a');
const scoreBEl=document.getElementById('score-b');
const barA=document.getElementById('bar-a');
const barB=document.getElementById('bar-b');
const truthEl=document.getElementById('truth-marker');
const verdictEl=document.getElementById('verdict-line');
const readoutQ=document.getElementById('qnum');
const readoutTotal=document.getElementById('qtotal');
const readoutA=document.getElementById('ra');
const readoutB=document.getElementById('rb');
const clockEl=document.getElementById('clock');
const marquee=document.querySelector('#marquee span');
const phaseLabel=document.getElementById('phase-label');
const connStatus=document.getElementById('conn-status');
const statusA=document.getElementById('status-a');
const statusB=document.getElementById('status-b');
const liveAnswer=document.getElementById('live-answer');

for(let i=0;i<10;i++){ const s=document.createElement('div');s.className='seg';barA.appendChild(s); const s2=document.createElement('div');s2.className='seg';barB.appendChild(s2); }
function updateBars(){ const segsA=barA.querySelectorAll('.seg'); const segsB=barB.querySelectorAll('.seg'); const total=Q.length; const aPct=scoreA/total;const bPct=scoreB/total; segsA.forEach((s,i)=>{s.className='seg'+(i<Math.round(aPct*10)?' filled-a':'')}); segsB.forEach((s,i)=>{s.className='seg'+(i<Math.round(bPct*10)?' filled-b':'')}); }

// === Attract mode ===
let attractQIndex=0;
function updateAttractPreview(){ const q=Q[attractQIndex%Q.length]; document.getElementById('preview-text').textContent=q.text; attractQIndex++; }
setInterval(updateAttractPreview,3000);
const hasSaved = localStorage.getItem('stump_recordedA') || localStorage.getItem('stump_recordedB');
if (hasSaved) {
  document.getElementById('preview-text').textContent = 'SAVED PROGRESS FOUND — Click CLEAR to start fresh, or INSERT COIN to resume';
} else {
  updateAttractPreview();
}
document.querySelectorAll('.lane-preview').forEach(l=>l.classList.add('breathing'));

// === Connection check ===
async function checkConnections(){ try { const r1=await fetch(TRACE.model_a.endpoint.replace('/chat/completions','/models')); const r2=await fetch(TRACE.model_b.endpoint.replace('/chat/completions','/models')); if(r1.ok&&r2.ok){ connStatus.textContent='LIVE';connStatus.className='ok'; } else { connStatus.textContent='PARTIAL';connStatus.className='err'; } } catch(e){ connStatus.textContent='OFFLINE';connStatus.className='err'; } }
checkConnections();

// === Restore from localStorage ===
function restoreProgress(){
  const savedA = localStorage.getItem('stump_recordedA');
  const savedB = localStorage.getItem('stump_recordedB');
  if (savedA) { recordedA = JSON.parse(savedA); modelAAnswers = recordedA.map(r=>r.answer); modelASecs = recordedA.map(r=>r.secs); }
  if (savedB) { recordedB = JSON.parse(savedB); modelBAnswers = recordedB.map(r=>r.answer); modelBSecs = recordedB.map(r=>r.secs); }
  return recordedA.length > 0 || recordedB.length > 0;
}

// === Start game: per-question live play ===
document.getElementById('coin-btn').addEventListener('click', async ()=>{
  initAudio(); cue('coin'); stopAttractLoop();
  attract.style.display='none'; playfield.style.display='flex';
  state='playing'; phase='live';
  qi=0; scoreA=0; scoreB=0;
  const hasSaved = restoreProgress();
  if (hasSaved && modelAAnswers.length >= Q.length && modelBAnswers.length >= Q.length) {
    // Skip to replay
    showPhaseBanner('RESUMING REPLAY'); await sleep(1500); hidePhaseBanner();
    replayNext();
    return;
  }
  // Fresh or partial: clear and start fresh
  if (!hasSaved || modelAAnswers.length === 0) {
    modelAAnswers=[]; modelBAnswers=[]; modelASecs=[]; modelBSecs=[];
    localStorage.removeItem('stump_recordedA'); localStorage.removeItem('stump_recordedB');
  }
  readoutTotal.textContent=Q.length; updateBars();
  for (let i = (modelAAnswers.length > 0 ? modelAAnswers.length : 0); i < Q.length; i++) {
    qi = i;
    await liveQuestion(i);
  }
  // All done, go to replay
  phase='replay'; qi=0; scoreA=0; scoreB=0;
  showPhaseBanner('REPLAY — SIMULTANEOUS REVEAL'); await sleep(2000); hidePhaseBanner();
  replayNext();
});

async function liveQuestion(i){
  const q = Q[i];
  qText.classList.remove('visible');
  truthEl.innerHTML='<span class="q">?</span>';
  verdictEl.textContent='';
  document.querySelectorAll('.dot').forEach(d=>d.classList.remove('visible'));
  document.querySelectorAll('.lane').forEach(l=>l.classList.remove('flash'));
  readoutQ.textContent=i+1;
  clockEl.textContent='0.0';
  phaseLabel.textContent='LIVE';
  statusA.textContent=''; statusB.textContent='';
  await sleep(100);
  qText.textContent=q.text; qText.classList.add('visible');
  cue('tick');
  marquee.textContent='LIVE · Q '+(i+1)+'/'+Q.length;

  // Call model A
  statusA.textContent='thinking...'; statusA.classList.add('thinking');
  const aResult = await callModel(TRACE.model_a.endpoint, q.text, TRACE.model_a.name, (elapsed)=>{ clockEl.textContent=elapsed.toFixed(1); }, (status)=>{ statusA.textContent=status; });
  statusA.textContent = aResult.error ? 'ERROR' : aResult.secs.toFixed(1)+'s';
  statusA.classList.remove('thinking');
  if (modelAAnswers.length <= i) { modelAAnswers.push(aResult.answer); modelASecs.push(aResult.secs); }
  else { modelAAnswers[i]=aResult.answer; modelASecs[i]=aResult.secs; }
  liveAnswer.textContent = TRACE.model_a.name + ': ' + (aResult.answer || 'ERROR') + ' (' + aResult.secs.toFixed(1) + 's)';
  liveAnswer.style.display='block';
  cue('tick');
  await sleep(500);

  // Call model B
  statusB.textContent='thinking...'; statusB.classList.add('thinking');
  const bResult = await callModel(TRACE.model_b.endpoint, q.text, TRACE.model_b.name, (elapsed)=>{ clockEl.textContent=elapsed.toFixed(1); }, (status)=>{ statusB.textContent=status; });
  statusB.textContent = bResult.error ? 'ERROR' : bResult.secs.toFixed(1)+'s';
  statusB.classList.remove('thinking');
  if (modelBAnswers.length <= i) { modelBAnswers.push(bResult.answer); modelBSecs.push(bResult.secs); }
  else { modelBAnswers[i]=bResult.answer; modelBSecs[i]=bResult.secs; }
  liveAnswer.textContent = TRACE.model_b.name + ': ' + (bResult.answer || 'ERROR') + ' (' + bResult.secs.toFixed(1) + 's)';
  await sleep(500);

  // Save to localStorage
  localStorage.setItem('stump_recordedA', JSON.stringify(modelAAnswers.map((a,j)=>({answer:a,secs:modelASecs[j]}))));
  localStorage.setItem('stump_recordedB', JSON.stringify(modelBAnswers.map((a,j)=>({answer:a,secs:modelBSecs[j]}))));
}

// === Replay with simultaneous reveal ===
function replayNext(){
  phase='replay';
  if(qi>=Q.length){ endGame(); return; }
  const q=Q[qi];
  qText.classList.remove('visible');
  truthEl.innerHTML='<span class="q">?</span>';
  verdictEl.textContent='';
  document.querySelectorAll('.dot').forEach(d=>d.classList.remove('visible'));
  document.querySelectorAll('.lane').forEach(l=>l.classList.remove('flash'));
  readoutQ.textContent=qi+1;
  clockEl.textContent='0.0';
  phaseLabel.textContent='REPLAY';
  const aAns=modelAAnswers[qi];
  const bAns=modelBAnswers[qi];
  statusA.textContent=modelASecs[qi].toFixed(1)+'s';
  statusB.textContent=modelBSecs[qi].toFixed(1)+'s';
  setTimeout(()=>{ qText.textContent=q.text; qText.classList.add('visible'); cue('tick'); },100);
  marquee.textContent='REPLAY · Q '+(qi+1)+'/'+Q.length;
  setTimeout(()=>flip(q,aAns,bAns),1500);
}

function flip(q,aAns,bAns){
  const aCorrect=isCorrect(aAns,q.truth,q.illposed);
  const bCorrect=isCorrect(bAns,q.truth,q.illposed);
  const aLane=q.illposed?classify(aAns||''):null;
  const bLane=q.illposed?classify(bAns||''):null;
  if(q.illposed){
    const da=document.getElementById('dot-a-'+aLane.toLowerCase());
    const db=document.getElementById('dot-b-'+bLane.toLowerCase());
    if(da){da.classList.add('visible');flashLane(aLane)}
    if(db){db.classList.add('visible');flashLane(bLane)}
  } else {
    const aL=aCorrect?'REFUSED':'CONFABULATED';
    const bL=bCorrect?'REFUSED':'CONFABULATED';
    const da=document.getElementById('dot-a-'+aL.toLowerCase());
    const db=document.getElementById('dot-b-'+bL.toLowerCase());
    if(da){da.classList.add('visible');flashLane(aL)}
    if(db){db.classList.add('visible');flashLane(bL)}
  }
  truthEl.innerHTML='<span style="color:var(--gold)">TRUTH: '+q.truth+'</span>';
  if(q.truth==='INSUFFICIENT') truthEl.querySelector('span').style.textShadow='0 0 8px var(--gold)';
  let vText='';
  if(aCorrect&&bCorrect){vText='BOTH CORRECT';cue('fanfare')}
  else if(aCorrect&&!bCorrect){vText='A CORRECT';cue('blip')}
  else if(!aCorrect&&bCorrect){vText='B CORRECT';cue('blip_high')}
  else {vText='BOTH WRONG';cue('descend')}
  if(q.illposed){
    const aCls=classify(aAns||''); const bCls=classify(bAns||'');
    if(aCls==='CONFABULATED') cue('buzz');
    if(bCls==='CONFABULATED') cue('buzz');
    if(aCls==='REFUSED'||aCls==='PARAMETRIC') cue(aCls==='PARAMETRIC'?'blip_high':'blip');
    if(bCls==='REFUSED'||bCls==='PARAMETRIC') cue(bCls==='PARAMETRIC'?'blip_high':'blip');
  }
  verdictEl.textContent=vText;
  verdictEl.style.color=aCorrect&&bCorrect?'var(--green)':(!aCorrect&&!bCorrect?'var(--red)':'var(--gold)');
  if(aCorrect){scoreA++;scoreAEl.classList.add('pop');setTimeout(()=>scoreAEl.classList.remove('pop'),150)}
  if(bCorrect){scoreB++;scoreBEl.classList.add('pop');setTimeout(()=>scoreBEl.classList.remove('pop'),150)}
  scoreAEl.textContent=scoreA; scoreBEl.textContent=scoreB;
  readoutA.textContent=scoreA; readoutB.textContent=scoreB; updateBars();
  clockEl.textContent=Math.max(modelASecs[qi],modelBSecs[qi]).toFixed(1);
  marquee.textContent='STUMP · REPLAY · '+TRACE.model_a.name+' vs '+TRACE.model_b.name;
  if(autoPlay){ setTimeout(()=>{qi++;replayNext()},2500); }
}

function flashLane(lane){ const el=document.querySelector('.lane[data-lane="'+lane+'"]'); if(el){el.classList.add('flash');setTimeout(()=>el.classList.remove('flash'),50)} }

document.getElementById('screen').addEventListener('click',()=>{ if(state==='playing'&&!autoPlay&&phase==='replay'){ const hasDots=document.querySelector('.dot.visible'); if(hasDots){qi++;replayNext()} } });
document.getElementById('next-btn').addEventListener('click',()=>{ if(state==='playing'&&phase==='replay'){ const hasDots=document.querySelector('.dot.visible'); if(hasDots){qi++;replayNext()} } });

function endGame(){ state='ended'; phase='ended'; const w=scoreA>scoreB?TRACE.model_a.name:(scoreB>scoreA?TRACE.model_b.name:'DRAW'); marquee.textContent='GAME OVER · '+w+' WINS'; qText.textContent='FINAL: '+TRACE.model_a.name+' '+scoreA+' — '+TRACE.model_b.name+' '+scoreB; qText.classList.add('visible'); truthEl.innerHTML='<span style="color:var(--gold)">WINNER: '+w+'</span>'; verdictEl.textContent=w==='DRAW'?'DRAW':w+' WINS'; verdictEl.style.color='var(--gold)'; phaseLabel.textContent='GAME OVER'; cue('fanfare'); }

// === Export ===
document.getElementById('export-btn').addEventListener('click',()=>{
  const results = Q.map((q,i)=>({ qid:q.qid, question:q.text, truth:q.truth, illposed:q.illposed, model_a:TRACE.model_a.name, model_a_answer:modelAAnswers[i], model_a_secs:modelASecs[i], model_b:TRACE.model_b.name, model_b_answer:modelBAnswers[i], model_b_secs:modelBSecs[i], oracle_verdict_a: isCorrect(modelAAnswers[i],q.truth,q.illposed)?'correct':'incorrect', oracle_verdict_b: isCorrect(modelBAnswers[i],q.truth,q.illposed)?'correct':'incorrect' }));
  const blob=new Blob([JSON.stringify({game:'stump',digest:TRACE.digest,timestamp:new Date().toISOString(),model_a:TRACE.model_a.name,model_b:TRACE.model_b.name,results:results},null,2)],{type:'application/json'});
  const url=URL.createObjectURL(blob); const a=document.createElement('a'); a.href=url; a.download='stump_live_'+Date.now()+'.json'; a.click(); URL.revokeObjectURL(url);
});

// === Clear saved progress ===
document.getElementById('clear-btn').addEventListener('click',()=>{
  localStorage.removeItem('stump_recordedA');
  localStorage.removeItem('stump_recordedB');
  alert('Saved progress cleared. Hard-refresh the page to start fresh.');
});

// === Mute toggle ===
const muteBtn=document.getElementById('mute-btn');
muteBtn.addEventListener('click',()=>{ muted=!muted; muteBtn.textContent=muted?'♪ OFF':'♪ ON'; muteBtn.classList.toggle('active',muted); if(!muted&&state==='attract') startAttractLoop(); });
// === Auto toggle ===
const autoBtn=document.getElementById('auto-btn');
autoBtn.addEventListener('click',()=>{ autoPlay=!autoPlay; autoBtn.classList.toggle('active',autoPlay); });
document.addEventListener('click',()=>{initAudio();if(state==='attract')startAttractLoop()},{once:true});

// === Init ===
readoutTotal.textContent=Q.length;
function sleep(ms){return new Promise(r=>setTimeout(r,ms))}
function showPhaseBanner(text){ phaseBanner.textContent=text; phaseBanner.style.display='block'; progressBar.style.display='block'; progressLabel.style.display='block'; liveAnswer.style.display='block'; }
function hidePhaseBanner(){ phaseBanner.style.display='none'; progressBar.style.display='none'; progressLabel.style.display='none'; liveAnswer.style.display='none'; }
</script>
</body>
</html>
'''

with open('/Users/mikebird/arena/handicap-arena/stump_cabinet.html','w') as f:
    f.write(html)
print('written', len(html), 'bytes')
