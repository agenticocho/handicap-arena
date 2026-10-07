#!/usr/bin/env python3
"""
Regenerates roster.html from results/*.json.

Surface: COMPARE. The unit of content is not a leaderboard row but a CONTROLLED PAIR --
the same GGUF sha256 run under two serving configs, producing two different belts. That is
what the evidence set actually contains, and rendering it as a ranking would hide it.

Every number comes from a result bundle. Nothing is invented. Where a round was cut off,
the card says so, because a truncated round is a MEASUREMENT FAILURE, not a capability
result -- and the first version of this project's diagnostic named the wrong cause.

Templating: PLAIN string with __TOKENS__ replaced at the end, with an assertion per edit.
Do NOT convert to an f-string; the JS is full of ${...} and object literals.
"""
import glob, hashlib, json, os, html, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "roster.html")
CORDS = {"Featherweight": "#3aa6a0", "Lightweight": "#d8a13a",
         "Middleweight": "#a07ad8", "Heavyweight": "#c9503f"}
BELT_ORDER = ["White", "Yellow", "Orange", "Green", "Blue", "Purple", "Brown", "Black"]

TPL = r"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Handicap Arena — Evidence Set</title>
<style>
  :root{
    --bg:#0e0f11; --panel:#15171a; --panel2:#1b1e22; --ink:#e8e6e1; --muted:#8c9099;
    --line:#262a30; --line2:#32373e; --accent:#d8a13a; --cool:#5aa9c9; --warn:#c9704f;
    --mono:ui-monospace,"SF Mono","Cascadia Mono",Menlo,Consolas,monospace;
    --sans:"Inter Tight","Helvetica Neue",Helvetica,Arial,sans-serif;
  }
  *{box-sizing:border-box}
  html,body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);
            font-size:14px;line-height:1.45;-webkit-font-smoothing:antialiased}
  .wrap{max-width:1180px;margin:0 auto;padding:26px 22px 80px}
  header.top{display:grid;grid-template-columns:1fr auto;gap:18px;align-items:end;
             border-bottom:1px solid var(--line2);padding-bottom:14px;margin-bottom:6px}
  h1{font-size:19px;font-weight:600;letter-spacing:-.01em;margin:0 0 3px}
  .sub{color:var(--muted);font-size:12.5px;max-width:78ch}
  .stamp{font-family:var(--mono);font-size:11px;color:var(--muted);text-align:right;white-space:nowrap}
  .notice{border:1px solid var(--line2);border-left:3px solid var(--accent);border-radius:3px;
          background:var(--panel);padding:11px 14px;margin:18px 0 22px;font-size:12.5px;color:var(--muted)}
  .notice b{color:var(--ink)}
  h2{font-size:12px;text-transform:uppercase;letter-spacing:.09em;color:var(--muted);
     font-weight:600;margin:26px 0 10px}
  .pair{background:var(--panel);border:1px solid var(--line);border-radius:3px;margin-bottom:14px;overflow:hidden}
  .pair .hd{display:flex;justify-content:space-between;gap:14px;padding:10px 14px;
            background:var(--panel2);border-bottom:1px solid var(--line);align-items:baseline;flex-wrap:wrap}
  .pair .hd .t{font-weight:600;font-size:13px}
  .pair .hd .sha{font-family:var(--mono);font-size:11px;color:var(--muted)}
  .arms{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--line)}
  .arm{background:var(--panel);padding:12px 14px}
  .arm .cfg{font-family:var(--mono);font-size:11px;color:var(--cool);margin-bottom:8px;
            word-break:break-word}
  .arm .lbl{font-size:10.5px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted)}
  .arm .belt{font-size:15px;font-weight:600;margin:2px 0 8px}
  .arm .rec{font-family:var(--mono);font-size:12px}
  .arm .why{color:var(--warn);font-size:11.5px;margin-top:7px}
  .delta{padding:9px 14px;border-top:1px solid var(--line);font-size:12.5px;color:var(--ink);
         background:var(--panel2)}
  .delta b{color:var(--accent)}
  table{width:100%;border-collapse:collapse;font-size:12.5px}
  thead th{text-align:right;font-size:10.5px;text-transform:uppercase;letter-spacing:.06em;
           color:var(--muted);font-weight:600;padding:8px;border-bottom:1px solid var(--line2);white-space:nowrap}
  thead th:first-child{text-align:left}
  tbody td{padding:7px 8px;border-bottom:1px solid var(--line);text-align:right;font-family:var(--mono)}
  tbody td.l{text-align:left;font-family:var(--sans);max-width:280px;overflow:hidden;text-overflow:ellipsis}
  tbody tr:hover td{background:var(--panel2)}
  .beltchip{display:inline-block;padding:1px 7px;border-radius:2px;font-family:var(--mono);
            font-size:11px;border:1px solid var(--line2)}
  .trunc{color:var(--warn)}
  .ok{color:var(--cool)}
  .dim{color:var(--muted)}
  @media (max-width:720px){.arms{grid-template-columns:1fr}tbody td.l{max-width:130px}}
  @media (prefers-reduced-motion:reduce){*{transition:none!important}}
</style>
</head><body><div class="wrap">

<header class="top">
  <div>
    <h1>Handicap Arena &mdash; Evidence Set</h1>
    <div class="sub">Every result bundle in <code>results/</code>, rendered from its own recorded
      config. The unit of comparison is the <b>controlled pair</b>: one GGUF, two serving
      configurations, two different belts.</div>
  </div>
  <div class="stamp">harness __HARNESS__ v__VER__<br>built __BUILT__<br>__NB__ bundles &middot; __NE__ entries</div>
</header>

<div class="notice">
  <b>This is not a leaderboard.</b> It is the raw evidence set, and it is small: __NE__ graded
  entries from __NB__ bundles. Two things it will never do &mdash; rank a
  <span class="trunc">truncated</span> round as if it were a capability result, and present a
  self-reported run as CERTIFIED. A model that is cut off has not failed; it has been measured
  wrongly, and the bundle says which of the two limits bit.
</div>

<h2>Controlled pairs &mdash; identical weights, different serving</h2>
<div id="pairs"></div>

<h2>All entries</h2>
<table>
  <thead><tr>
    <th>model</th><th>div</th><th>gb</th><th>belt</th><th>stripes</th>
    <th>R1</th><th>R2</th><th>R3</th><th>agg</th><th>lat s</th><th>place</th><th>vram free</th><th>ctx</th><th>mt</th><th>cert</th>
  </tr></thead>
  <tbody id="tb"></tbody>
</table>

<h2>What this set cannot tell you</h2>
<div class="notice">
  <b>How to read the round columns.</b> <code>3/3</code> is wins over trials.
  <span class="trunc">3/3&middot;cap3</span> means all three trials stopped on the
  <b>token cap</b> rather than finishing &mdash; a different failure from answering wrongly, and
  the distinction matters when choosing a model to put in service. A rambler and a wrong-answerer
  are not the same thing.<br><br>
  <b>Four bundles is not a field.</b> These measure serving-configuration effects on three rounds;
  they do not establish which local model is best at anything. The divisions are
  <b>measured VRAM</b> and move with whatever else held the GPU at weigh-in time (see
  FINDINGS/002) &mdash; a footprint here is a property of the machine as much as the model.
  <b>CERTIFIED</b> requires the arena to re-run the entry itself; everything here is
  <b>OPEN (self-reported)</b>.<br><br>
  <b>Do not compare the latency column across rows.</b> Placement is <code>auto-fit</code> for
  nearly every entry, which means each model got whatever VRAM the production stack left free at
  its turn &mdash; 6,453 of 8,192 MiB were held by resident servers during this run. Accuracy
  scores are unaffected (the 900&thinsp;s generation timeout never binds, and truncation is a
  token cap, not a time cap), but <b>latency is the base unit of the biathlon score</b>, so no
  biathlon total from this field may be quoted. A valid latency comparison needs a separate
  all-CPU division (<code>--ngl 0</code>) &mdash; see FINDINGS/004. A fixed <code>ngl</code> is not
  a valid substitute: it counts <i>layers</i>, not bytes.
</div>

<script>
const ENTRIES = __ENTRIES__;
const PAIRS   = __PAIRS__;
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const belt = b => '<span class="beltchip">' + esc(b) + '</span>';

document.getElementById('pairs').innerHTML = PAIRS.map(p => {
  const arms = p.arms.map(a => `
    <div class="arm">
      <div class="cfg">${esc(a.cfg)}</div>
      <div class="lbl">belt</div>
      <div class="belt">${belt(a.belt)} &nbsp;<span class="dim">${a.stripes}/${a.trials} stripes</span></div>
      <div class="rec">${esc(a.model)} &middot; ${a.footprint} GB &middot; ${esc(a.div)}</div>
      ${a.why ? `<div class="why">&#9888; ${esc(a.why)}</div>` : ''}
    </div>`).join('');
  return `
  <div class="pair">
    <div class="hd"><div class="t">${esc(p.title)}</div>
      <div class="sha">gguf sha256 ${esc(p.sha)} &middot; ${p.arms.length} arms</div></div>
    <div class="arms">${arms}</div>
    <div class="delta">${p.delta}</div>
  </div>`;
}).join('') || '<div class="notice">No controlled pairs in this set yet.</div>';

document.getElementById('tb').innerHTML = ENTRIES.map(e => `
  <tr>
    <td class="l">${esc(e.model)}</td>
    <td class="dim">${esc(e.div)}</td>
    <td>${e.footprint}</td>
    <td>${belt(e.belt)}</td>
    <td>${e.stripes}/${e.trials}</td>
    <td class="${e.r1trunc ? 'trunc' : ''}">${e.r1}</td>
    <td class="${e.r2trunc ? 'trunc' : ''}">${e.r2}</td>
    <td class="${e.r3trunc ? 'trunc' : ''}">${e.r3}</td>
    <td>${e.agg}</td>
    <td class="dim">${e.lat}</td>
    <td class="trunc">${esc(e.placement)}</td>
    <td class="${e.partial ? 'trunc' : 'dim'}">${e.gpu_free == null ? '—' : e.gpu_free + ' GB'}${
        e.partial === true ? ' &darr;partial' : (e.partial === false ? ' full' : '')}</td>
    <td class="dim">${e.ctx}</td>
    <td class="dim">${e.mt}</td>
    <td class="dim">${esc(e.cert)}</td>
  </tr>`).join('');
</script>
</div></body></html>
"""


def load_bundles():
    entries, harness, ver = [], "?", "?"
    for path in sorted(glob.glob(os.path.join(HERE, "results", "*.json"))):
        try:
            d = json.load(open(path))
        except Exception as e:
            print(f"  SKIP {os.path.basename(path)}: {e}")
            continue
        harness = d.get("harness", harness)
        ver = d.get("version", ver)
        for r in (d.get("results") or []):
            r["_file"] = os.path.basename(path)
            r["_mtime"] = os.path.getmtime(path)
            entries.append(r)

    # DEDUPE. An entry is identified by (sha256, ctx, max_tokens, n_gpu_layers) -- the tuple
    # that determines the measurement. Two bundles measuring the same thing are ONE entry.
    #
    # This exists because run_card.py's skip was FILENAME-based and therefore missed the
    # hand-named bundles: it re-ran Qwen3.5-2B and produced a second bundle under the full
    # stem. Rendering the same measurement twice would make the board look fuller than it is.
    best = {}
    for r in entries:
        cfg = r.get("config") or {}
        key = (r.get("sha256"), cfg.get("ctx"), cfg.get("max_tokens"), cfg.get("n_gpu_layers"))
        prev = best.get(key)
        if prev is None or r["_mtime"] > prev["_mtime"]:
            best[key] = r
    collapsed = len(entries) - len(best)
    if collapsed:
        print(f"  dedupe: collapsed {collapsed} duplicate measurement(s) — same sha256+config")
    return list(best.values()), harness, ver


def label_for(r):
    cfg = r.get("config") or {}
    flags = cfg.get("server_flags") or []
    serving = "GRAMMAR" if "--grammar-file" in flags else "neutral"
    return f"{os.path.basename(r.get('gguf','?')).replace('.gguf','')} | ctx{cfg.get('ctx')} mt{cfg.get('max_tokens')}"


def build(entries, harness, ver):
    def g(r, k, dflt=0):
        return (r.get("rounds") or {}).get(k, {}).get("score", dflt)

    def rec(r, k):
        rd = (r.get("rounds") or {}).get(k, {})
        fr = rd.get("finish_reasons") or {}
        cap = fr.get("length", 0)          # trials that hit the TOKEN cap
        s = f"{rd.get('wins',0)}/{rd.get('trials',0)}"
        # 'hit the token cap' and 'answered wrongly' are different failures. For someone
        # choosing a model to put in service, a rambler and a wrong-answerer are not the same
        # thing, and the bundle already records which is which.
        return s + ("·cap" + str(cap) if cap else "")

    rows = []
    for r in entries:
        cfg = r.get("config") or {}
        rd = r.get("rounds") or {}
        gr = r.get("grade") or {}
        agg = r.get("aggregate")
        rows.append({
            "model": label_for(r),
            "div": r.get("division", "?"),
            "footprint": round(r.get("footprint_gb") or 0, 2),
            "belt": gr.get("belt", "?"),
            "stripes": gr.get("stripes", 0),
            "trials": gr.get("trials", 0),
            "r1": rec(r, "R1_fencing"), "r2": rec(r, "R2_chess"), "r3": rec(r, "R3_pitstop"),
            "r1trunc": bool(rd.get("R1_fencing", {}).get("truncated")),
            "r2trunc": bool(rd.get("R2_chess", {}).get("truncated")),
            "r3trunc": bool(rd.get("R3_pitstop", {}).get("truncated")),
            "agg": "—" if agg is None else f"{agg:.2f}",
            "lat": round(r.get("mean_latency") or 0, 1),
            "ctx": cfg.get("ctx"), "mt": cfg.get("max_tokens"),
            # Placement belongs on the board. FINDINGS/004: latency is the base unit of the
            # biathlon score, so a latency figure is only meaningful alongside the placement it
            # was measured at -- and placement here is set by the production stack, not the
            # entrant.
            "placement": ("auto-fit" if cfg.get("n_gpu_layers") is None
                          else f"ngl {cfg.get('n_gpu_layers')}"),
            # These live in the nested weigh_in block (FINDINGS/002's fix), and the pre-fix
            # bundles simply do not have it -- shown as '—' rather than guessed.
            "gpu_free": (r.get("weigh_in") or {}).get("gpu_free_gb_at_weigh_in"),
            "partial": (r.get("weigh_in") or {}).get("partial_offload"),
            "cert": "OPEN" if "OPEN" in str(r.get("certification", "")) else str(r.get("certification", "?")),
        })

    # ---- controlled pairs: same gguf sha256, more than one distinct config ----
    from collections import defaultdict
    by_sha = defaultdict(list)
    for r in entries:
        by_sha[r.get("sha256")].append(r)
    pairs = []
    for sha, group in by_sha.items():
        if len(group) < 2 or not sha:
            continue
        arms = []
        for r in group:
            cfg = r.get("config") or {}
            rd = r.get("rounds") or {}
            gr = r.get("grade") or {}
            worst_why = next((v.get("why") for v in rd.values()
                              if v.get("truncated") and v.get("why")), None)
            # NEVER render an absolute local path into a public artifact. The repo is public;
            # the grammar's basename is the information, the directory tree is not.
            flags = cfg.get("server_flags") or []
            gbnf = next((os.path.basename(f) for f in flags if f.endswith(".gbnf")), None)
            arms.append({
                "cfg": f"ctx {cfg.get('ctx')} · mt {cfg.get('max_tokens')} · "
                       + (f"GRAMMAR {gbnf}" if "--grammar-file" in flags else "neutral"),
                "model": os.path.basename(r.get("gguf", "?")).replace(".gguf", ""),
                "belt": gr.get("belt", "?"), "stripes": gr.get("stripes", 0),
                "trials": gr.get("trials", 0),
                "footprint": round(r.get("footprint_gb") or 0, 2),
                "div": r.get("division", "?"),
                "why": worst_why,
            })
        arms.sort(key=lambda a: BELT_ORDER.index(a["belt"]) if a["belt"] in BELT_ORDER else 99)
        lo, hi = arms[0], arms[-1]
        if lo["belt"] != hi["belt"]:
            delta = (f"The <b>same weights</b> produce a different belt: "
                     f"{html.escape(lo['belt'])} ({lo['stripes']}/{lo['trials']}) versus "
                     f"{html.escape(hi['belt'])} ({hi['stripes']}/{hi['trials']}). "
                     f"The weights did not change &mdash; the serving configuration did.")
        else:
            delta = "Same belt in both configurations; the serving change did not move the grade."
        pairs.append({"title": "Controlled pair", "sha": (sha or "")[:16], "arms": arms,
                      "delta": delta})
    pairs.sort(key=lambda p: p["sha"])

    doc = TPL
    import json as _json
    edits = [
        ("__HARNESS__", html.escape(str(harness))),
        ("__VER__", html.escape(str(ver))),
        ("__BUILT__", dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")),
        ("__NB__", str(len({r["_file"] for r in entries}))),
        ("__NE__", str(len(rows))),
        ("__ENTRIES__", _json.dumps(rows)),
        ("__PAIRS__", _json.dumps(pairs)),
    ]
    for tok, val in edits:
        assert tok in doc, f"TOKEN MISSING FROM TEMPLATE: {tok}"
        doc = doc.replace(tok, val)
    return doc, rows, pairs


if __name__ == "__main__":
    entries, harness, ver = load_bundles()
    doc, rows, pairs = build(entries, harness, ver)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(doc)
    print(f"entries: {len(rows)}   controlled pairs: {len(pairs)}")
    print(f"written: {OUT} ({os.path.getsize(OUT):,} bytes)")
    leftover = [t for t in ("__ENTRIES__", "__PAIRS__", "__NB__", "__NE__",
                            "__HARNESS__", "__VER__", "__BUILT__") if t in doc]
    print(f"unreplaced tokens: {leftover or 'none'}")
    for p in pairs:
        print(f"  pair {p['sha']}: " + " | ".join(f"{a['belt']} {a['stripes']}/{a['trials']}"
                                                 for a in p["arms"]))
