#!/usr/bin/env bash
# PREFLIGHT for the arena run. It WAITS for conditions under which the box is not at risk, then runs.
#
# WHY THIS EXISTS. The 16:55:16 freeze left NO OOM record, NO GPU/driver error and NO kernel trace --
# the journal simply stops. That is the signature of memory pressure that slows the machine to a halt
# rather than one that trips a limit: with 60 GiB RAM plus 8 G of swap the kernel can push ~68 GiB, and
# it thrashes long before oomd acts. The unit's own properties now bound swap; this waits for a window
# where the box is quiet to begin with.
#
# WHAT IT DETECTS, AND WHAT IT CANNOT. There is no xprintidle on this box, so it CANNOT tell whether a
# human is typing. It detects the two things that actually make the run dangerous: the machine being
# under load, and memory being tight. It does not claim to detect "the user is at the keyboard", and it
# does not need to -- a browser tab is not what freezes a box; a 35B model and a 64K-context server are.
set -u

LOAD_OK=1.5          # 1-minute load average must be below this
MEM_OK_GB=30         # available memory must be at least this
STABLE_SECS=300      # the pressures must hold this long before we start
MAX_WAIT_SECS=21600  # give up after 6 h and leave it for a human

say() { printf '%s  %s\n' "$(date '+%H:%M:%S')" "$*"; }

memory_avail_gb() { awk '/MemAvailable/ {printf "%d", $2/1048576}' /proc/meminfo; }
load1() { awk '{print $1}' /proc/loadavg; }

say "preflight: waiting for load1 < $LOAD_OK, MemAvailable >= ${MEM_OK_GB}G, stable for ${STABLE_SECS}s"
say "preflight: this does NOT detect a person at the keyboard (no xprintidle); it detects a BUSY BOX."

waited=0; stable=0
until [ "$waited" -ge "$MAX_WAIT_SECS" ]; do
    l=$(load1); m=$(memory_avail_gb)
    if awk -v a="$l" -v b="$LOAD_OK" 'BEGIN{exit !(a < b)}' && [ "$m" -ge "$MEM_OK_GB" ]; then
        stable=$((stable + 30))
        say "preflight: quiet (load1=$l, avail=${m}G) -- ${stable}s of ${STABLE_SECS}s"
    else
        [ "$stable" -gt 0 ] && say "preflight: conditions broke (load1=$l, avail=${m}G) -- timer reset"
        stable=0
    fi
    [ "$stable" -ge "$STABLE_SECS" ] && { say "preflight: GO"; exec /usr/bin/python3 \
        /home/chilly1/workspace/ocho_arena/run_card.py --card v5; }
    sleep 30; waited=$((waited + 30))
done

say "preflight: waited ${MAX_WAIT_SECS}s without a safe window. NOT starting. A human should look."
exit 3
