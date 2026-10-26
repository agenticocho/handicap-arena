#!/usr/bin/env python3
"""Labyrinth controls: scripted walker + wall-pusher. CPU only."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import labyrinth_run as L

def main():
    ok, row = L.control_test()
    print(json.dumps({"controls": row, "pass": ok}, indent=2))
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())