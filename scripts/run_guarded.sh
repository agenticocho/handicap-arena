#!/usr/bin/env bash
# RUN EVERYTHING UNDER A UNIT. Chilly's rule, and this is the mechanism that makes it a rule rather than
# a resolution to remember.
#
# WHY IT EXISTS. Every chess run on 2026-10-09 was a bare `python3 ...` and therefore escaped the memory
# ceiling entirely -- the guard was on arena-v5.service and nowhere else. A guard that only covers the
# workload that happened to be unitised is not a guard; it is a guard for one workload.
#
# AND THE NUMBERS ARE THE ARENA'S OWN, NOT A PRECAUTION. They were briefly set BELOW the arena's own
# values, which killed legitimate work for a benefit nobody had demonstrated: memory pressure has never
# been implicated in any freeze on this box (two were GPU GSP firmware, one was kernel memory corruption,
# and none had an OOM record or a bound that engaged). The arena's own numbers are the ones that were
# derived; a precaution below them was a cost with no evidence behind it.
#
# THE SWAP BOUND STAYS. That one came from a measured inference rather than a precaution.
#
# USAGE
#   scripts/run_guarded.sh <unit-name> <workdir> <command...>
#   scripts/run_guarded.sh cost-probe-widened /home/chilly1/workspace/ocho_arena \
#       /usr/bin/python3 cost_probe.py --wide
#
# A BARE RUN IS NEVER THE ANSWER. If one is ever the only way to reproduce something, say so and re-check
# the guard -- do not let it be absent quietly, because a guard with an unrecorded exception is the
# empty-room defect aimed at the guard itself.
set -euo pipefail

UNIT="${1:?unit name required}"
WORKDIR="${2:?workdir required}"
shift 2

MEM_HIGH="${OCHO_MEM_HIGH:-24G}"
MEM_MAX="${OCHO_MEM_MAX:-32G}"
MEM_SWAP="${OCHO_MEM_SWAP:-1G}"
LOG="${OCHO_LOG:-$WORKDIR/logs/${UNIT}.out}"

mkdir -p "$(dirname "$LOG")"

echo "unit      $UNIT"
echo "workdir   $WORKDIR"
echo "ceiling   MemoryHigh=$MEM_HIGH  MemoryMax=$MEM_MAX  MemorySwapMax=$MEM_SWAP"
echo "log       $LOG"
echo "command   $*"
echo

exec systemd-run --user --unit="$UNIT" --collect \
    --property=MemoryHigh="$MEM_HIGH" \
    --property=MemoryMax="$MEM_MAX" \
    --property=MemorySwapMax="$MEM_SWAP" \
    --property=ManagedOOMPreference=none \
    --property=WorkingDirectory="$WORKDIR" \
    --property=StandardOutput="append:$LOG" \
    --property=StandardError="append:$LOG" \
    "$@"
