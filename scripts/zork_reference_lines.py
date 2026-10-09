"""Reference lines on the retention world, measured before freezing the criteria."""
import json
import subprocess
import sys

W = "levels/zork_02_long_crawl.txt"
LINES = [
    ("carries it",        ["north", "take key", "south", "east", "north", "east"]),
    ("forgets the take",  ["north", "south", "east", "north", "east"]),
    ("takes then drops",  ["north", "take key", "drop key", "south", "east", "north", "east"]),
    ("passive",           ["look", "inventory", "look"]),
    ("never moves",       ["look", "look"]),
    ("parses nothing",    ["e2e4", "RESIGN", "take unicorn"]),
    ("wrong way",         ["east", "north", "south", "west"]),
]

print(f"{'line':20s} {'finished':9s} {'ending':16s} {'took_at':8s} {'parsed':7s} "
      f"{'unparsed':9s} {'impossible':11s}")
print("-" * 84)
rows = []
for name, cmds in LINES:
    out = subprocess.run([sys.executable, "zork.py", "--world", W,
                          "--commands", ";".join(cmds), "--json"],
                         capture_output=True, text=True)
    r = json.loads(out.stdout)
    c = r["counts"]
    print(f"{name:20s} {str(r['finished']):9s} {r['ending']:16s} "
          f"{str(r['took_item_at_step']):8s} {c['parsed']:<7} {c['unparsed']:<9} "
          f"{c['recognised-but-impossible']:<11}")
    rows.append({"line": name, "commands": cmds, "finished": r["finished"],
                 "ending": r["ending"], "took_item_at_step": r["took_item_at_step"],
                 "counts": c, "rooms_visited": r["rooms_visited"],
                 "final_inventory": r["final_inventory"]})

print()
fin = [r for r in rows if r["finished"]]
print(f"lines that finish            : {len(fin)} / {len(rows)}")
print(f"lines ending gate_locked     : {sum(1 for r in rows if r['ending'] == 'gate_locked')}")
print(f"lines with zero unparsed     : {sum(1 for r in rows if r['counts']['unparsed'] == 0)}")
best = max(r["counts"]["parsed"] for r in rows)
print(f"max parsed count seen        : {best}")
with open("/tmp/zork_refs.json", "w") as f:
    json.dump(rows, f, indent=2)
print("\nwrote /tmp/zork_refs.json")
