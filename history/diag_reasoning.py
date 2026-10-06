#!/usr/bin/env python3
"""Diagnose the reasoning-field problem on llama-swap: where does the ANSWER actually go?"""
import json, urllib.request, re

BASE = "http://127.0.0.1:8080/v1/chat/completions"
T1 = """Return ONLY a JSON object matching this JSON Schema. No prose, no code fences.

Schema: {"type":"object","required":["station"],"properties":{"station":{"type":"string"}}}

Content requirements:
- station: "RENO-04"

After the JSON, add a short friendly sentence explaining your choice."""


def probe(alias, max_tokens):
    body = json.dumps({"model": alias, "messages": [{"role": "user", "content": T1}],
                       "temperature": 0.0, "max_tokens": max_tokens}).encode()
    req = urllib.request.Request(BASE, data=body, headers={"Content-Type": "application/json"})
    try:
        r = json.load(urllib.request.urlopen(req, timeout=300))
    except Exception as e:
        return {"err": f"{type(e).__name__}: {str(e)[:80]}"}
    ch = r["choices"][0]; m = ch.get("message", {})
    return dict(finish=ch.get("finish_reason"),
                content=m.get("content") or "",
                reasoning=m.get("reasoning_content") or "",
                ctok=(r.get("usage") or {}).get("completion_tokens"))


for alias in ("ocho-planner", "ocho-planner-4b"):
    for mt in (1200, 4000):
        d = probe(alias, mt)
        print(f"\n{'='*100}\n{alias}  max_tokens={mt}")
        if "err" in d:
            print("  ERR", d["err"]); continue
        print(f"  finish_reason      : {d['finish']}")
        print(f"  completion_tokens  : {d['ctok']}")
        print(f"  content  len       : {len(d['content'])}")
        print(f"  reasoning len      : {len(d['reasoning'])}")
        print(f"  content  repr      : {d['content'][:200]!r}")
        print(f"  reasoning TAIL     : {d['reasoning'][-300:]!r}")
        # does EITHER field contain a parseable JSON object?
        for field in ("content", "reasoning"):
            mm = re.search(r"\{.*\}", d[field], re.S)
            if mm:
                try:
                    json.loads(mm.group(0)); print(f"  --> parseable JSON found in {field}")
                except Exception:
                    print(f"  --> JSON-LIKE but unparseable in {field}: {mm.group(0)[:120]!r}")
        print(f"  contains 'RENO-04' : content={('RENO-04' in d['content'])} "
              f"reasoning={('RENO-04' in d['reasoning'])}")
        print(f"  contains '<｜end▁of▁thinking｜>': {(' response' in d['reasoning'] or ' response' in d['content'])}")

print(f"\n{'='*100}")
print("server reasoning config / props:")
for ep in ("/props", "/v1/props"):
    try:
        r = urllib.request.urlopen(f"http://127.0.0.1:8080{ep}", timeout=20)
        j = json.load(r)
        keys = [k for k in j if "reason" in k.lower() or "template" in k.lower() or "chat" in k.lower()]
        print(f"  {ep}: keys of interest -> {keys}")
        for k in keys:
            print(f"     {k} = {str(j[k])[:200]}")
    except Exception as e:
        print(f"  {ep}: {type(e).__name__}")
