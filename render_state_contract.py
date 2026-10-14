#!/usr/bin/env python3
"""THE STATE SIDE OF THE BINDING CONTRACT — derived from the bundles, not written by hand.

RENDER_SPEC_8bit.md §3 says a cart declares `bindings`: recorded field -> drawn element, and §8 says
a binding naming a field absent from the event's state schema FAILS. That check needs a state schema
to fail against, and this file is the one the state side can supply.

TWO RULES SHAPE IT, AND BOTH ARE ALREADY PROJECT RULES APPLIED HERE:

  * DERIVE, DON'T CARRY. The schema is computed from the recorded bundles in `results/`. A hand-kept
    field list drifts from what it lists exactly the way a hand-kept count drifts from what it counts
    (GAMES.md's header read "forty-plus across nine" while the body held 55 across 10). So there is
    no field list in this file to go stale.

  * READ THE PRIMITIVE, NEVER THE RENDERING. `aggregate` is stored, and on 52 of 119 graded entries
    it is NOT the value its own `wins`/`trials` give. A cart binding a gauge to `aggregate` draws a
    number the bundle's own primitives do not agree with. So the schema marks stored display values
    UNSAFE and the check refuses a binding that names one where its primitive exists.

WHAT THE CHECK ENFORCES (each rule, and why it is state-side and not taste):

  R1  every `draw:` target is reachable from a `field:`                  -- their §3, mirrored so the
                                                                            whole contract is one program
  R2  every `field:` exists in the DERIVED schema for that event kind     -- a name outside the
                                                                            schema is a fabrication
  R3  no binding names an UNSAFE display value where its primitive exists -- the read rule
  R4  every `from:`/transform comes from the CLOSED transform set         -- a free expression is
                                                                            where an invented number
                                                                            enters
  R5  every `when:` names a recorded field                                -- a condition with no field
                                                                            asserts state nobody recorded
  R6  every binding declares `if_absent`, and it is "blank" or "omit"     -- never a default value:
                                                                            a plausible sprite where
                                                                            there is no field is a
                                                                            fabrication with pixels
  R7  a cart is DATA: the key set is closed                              -- cart code is where an
                                                                            unbound element gets drawn
  R9  every cue names an OUTCOME the record carries, and the vocabulary  -- a motif named after the
      is derived per event, not declared by the cart                         drawing ("score", "miss")
                                                                            is R3 one channel over --
                                                                            the read rule with a sound
                                                                            in place of a number -- and
                                                                            a `resign` cue on an event
                                                                            whose record cannot run out
                                                                            is a claim nobody recorded

  Silence is the default (spec 5), so a cart may declare no cues at all. It may not declare one the
  record cannot take. R9 is the transcript's own addition -- the room is built on win, loss and, IF IT
  HAS ONE, resignation -- turned into the same kind of mechanical check the field bindings already are.

POSITIVE CONTROLS: ten deliberately-bad carts, one per rule and one for the negative direction, so
this cannot become a check that passes by being unable to fail. The last control is the one that
matters most: an HONEST cart must PASS. A rule that rejects the thing it exists to permit is worse
than no rule.

USAGE
    python3 render_state_contract.py                 # derive + self-test; writes RENDER_STATE_SCHEMA.json
    python3 render_state_contract.py <cart.json>...   # additionally check real carts
Exit code is 1 while any violation stands -- an enforcing check that exits 0 while reporting
violations cannot fail, and this project has been bitten by exactly that.
"""
import glob
import hashlib
import json
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)                      # root scripts: already sys.path[0]; scripts/*: required
import cabinet_root as _root


def scope(pattern="*.json"):
    """[(kind, base, [paths])] over the DECLARED domain, entry by entry. No pattern is widened,
    no directory joins by existing."""
    rows = []
    for kind, base in _root.domain():
        rows.append((kind, base, sorted(glob.glob(os.path.join(base, pattern)))))
    return rows


def print_scope(rows, pattern):
    # THE SCOPE IS PRINTED WITH THE COUNT IT CONTRIBUTED: a count without its scope is not a count.
    for kind, base, hits in rows:
        print(f"  scope  {kind:16} {len(hits):4} {pattern}  {base}")

SCHEMA_PATH = os.path.join(HERE, "RENDER_STATE_SCHEMA.json")

# --- what a binding may say -------------------------------------------------------------------

CART_KEYS = {"name", "atlas", "bindings", "cues", "resolution", "kind"}
BINDING_KEYS = {"field", "draw", "of", "from", "to", "range", "when", "if_absent"}
# The draw vocabulary IS §2's five primitives, and nothing else. Two entries were wrong in opposite
# directions, and both were found by comparing this set against the spec rather than by reading it:
#   `sprite_tween` -- NOT a primitive. §2 defines "sprite layer: positioned sprites from the atlas,
#                     WITH A TWEEN", so the tween is a property of the sprite, not a second kind.
#   `state`        -- NOT a primitive. It has no engine behind it, and it is not needed: R5 already
#                     carries `when:`, and a condition is a binding property, not a drawing operation.
#   `audio`        -- WAS MISSING, and it is §2's fifth primitive. This is the one that mattered: the
#                     room's three outcome cues (win / loss / resignation) have no draw target without
#                     it, so the cue map R9 enforces could not be bound to anything.
DRAW_KINDS = {"tile_layer", "sprite", "text_panel", "gauge", "audio"}
IF_ABSENT = {"blank", "omit"}

# The closed transform set. Everything a cart may do to a recorded field before drawing it. A free
# expression is a place a number that is not in the record can be produced, so there is no free
# expression: these five, and anything else fails the cart.
TRANSFORMS = {"slice", "index", "linear_map", "identity", "count_of"}

# Fields that are STORED DERIVED VALUES: a value already computed from primitives elsewhere in the
# same bundle. Binding a gauge to one of these renders a number the primitives do not agree with.
# Each entry names the primitive the cart must bind instead.
UNSAFE_DISPLAY = {
    "entrant.aggregate": "Fraction(sum(wins), sum(trials)) over the rounds of the card_version",
    "round.score": "wins / trials for the round",
    "entrant.grade.stripes": "rounds_won / rounds",
}


def classify(path):
    if path in UNSAFE_DISPLAY:
        return "UNSAFE_DERIVED"
    if path.startswith("entrant.config") or path.startswith("entrant.weigh_in"):
        return "RUN_FACT"          # a fact about HOW it ran; real, bindable, not the measurement
    if path.startswith("entrant."):
        return "ENTRANT"
    return "ROUND"


def walk(o, pfx, out):
    if isinstance(o, dict):
        for k, v in o.items():
            walk(v, pfx + "." + k if pfx else k, out)
    elif isinstance(o, list):
        out[pfx + "[]"] = "list"
    else:
        out[pfx] = type(o).__name__


def derive():
    """The schema, computed from every recorded bundle. Deterministic: sorted, no timestamps."""
    _rows = scope("*.json")
    print_scope(_rows, "*.json")
    bundles = [p for _k, _b, hits in _rows for p in hits]
    kinds = defaultdict(Counter)      # kind -> path -> count of rounds carrying it
    kind_rounds = Counter()           # kind -> rounds seen
    kind_outcomes = defaultdict(set)  # kind -> the outcome vocabulary THE RECORD carries (R9)
    entrant_counts = Counter()
    entrant_types = {}
    n_ent = 0
    n_bundles = 0
    for b in bundles:
        try:
            d = json.load(open(b, encoding="utf-8"))
        except Exception:
            continue
        if d.get("harness") != "handicap-arena":
            continue
        n_bundles += 1
        for e in d.get("results") or []:
            n_ent += 1
            o = {}
            walk({k: v for k, v in e.items() if k != "rounds"}, "entrant", o)
            for k, t in o.items():
                entrant_counts[k] += 1
                entrant_types[k] = t
            for _rk, rd in (e.get("rounds") or {}).items():
                kind = rd.get("kind") or "unknown"
                kind_rounds[kind] += 1
                # R9's vocabulary, DERIVED the same way the field list is: a round is won or lost
                # wherever wins/trials are recorded, and a resignation exists only where the record
                # carries a run that did not finish -- `truncated` on the round or on an item, or a
                # `finish_reasons` key other than the machine's own `stop`. Nothing is asserted: if a
                # future kind carries no such state, `resign` simply is not in its vocabulary.
                if "wins" in rd and "trials" in rd:
                    kind_outcomes[kind].update({"win", "loss"})
                fr = rd.get("finish_reasons")
                if isinstance(fr, dict):
                    kind_outcomes[kind].update(fr.keys())
                if rd.get("truncated"):
                    kind_outcomes[kind].add("resign")
                for _iid, it in (rd.get("items") or {}).items():
                    if isinstance(it, dict) and it.get("truncated"):
                        kind_outcomes[kind].add("resign")
                        break
                o = {}
                walk(rd, "round", o)
                for k, t in o.items():
                    kinds[kind][k] += 1
                    entrant_types.setdefault("__t_" + kind + "__" + k, t)
    return {
        "derived_from": {
            "bundles": n_bundles,
            "entrant_entries": n_ent,
            "results_dir": "results/",
        },
        "note": ("Derived from the recorded bundles. There is no field list in the derivation script "
                 "to go stale; re-run it and the schema moves with the record."),
        "entrant": {
            "present_on": n_ent,
            "fields": {p: {"type": entrant_types[p], "present": entrant_counts[p],
                           "class": classify(p)}
                       for p in sorted(entrant_counts)},
        },
        "round": {
            kind: {
                "observed_rounds": kind_rounds[kind],
                "outcomes": sorted(kind_outcomes[kind]),
                "fields": {p: {"type": entrant_types["__t_" + kind + "__" + p],
                               "present": c, "class": classify(p)}
                           for p, c in sorted(kinds[kind].items())},
            }
            for kind in sorted(kinds)
        },
    }


# --- the check ---------------------------------------------------------------------------------

def _schema_paths(schema, kind):
    paths = dict(schema["entrant"]["fields"])
    round_fields = schema["round"].get(kind, {}).get("fields", {})
    paths.update(round_fields)
    return paths


def check_cart(cart, schema, kind_hint=None):
    """-> list of failure strings. The cart is DATA; every rule here is mechanical."""
    fails = []
    if not isinstance(cart, dict):
        return ["cart is not an object -- a cart is data, not a program"]
    extra = set(cart) - CART_KEYS
    if extra:
        fails.append("R7 cart declares keys outside the closed set: %s" % sorted(extra))
    if "bindings" not in cart:
        return fails + ["cart declares no `bindings`"]
    if not isinstance(cart["bindings"], list):
        return fails + ["`bindings` is not a list"]
    if not cart["bindings"]:
        return fails + ["`bindings` is empty -- a cart that draws nothing is not a cart"]

    # Normalise every bound name to a canonical schema path. A cart may write `aggregate` or
    # `entrant.aggregate` and mean the same recorded field; the check must see the same field either
    # way, because an alias the check cannot see is an alias something can hide behind.
    canon = {}
    kinds = set()
    for i, b in enumerate(cart["bindings"]):
        if not isinstance(b, dict):
            fails.append("bindings[%d] is not an object" % i)
            continue
        b_extra = set(b) - BINDING_KEYS
        if b_extra:
            fails.append("bindings[%d] declares keys outside the closed set: %s" % (i, sorted(b_extra)))
        f = b.get("field")
        dr = b.get("draw")
        # R1 -- every draw target reachable from a field
        if not f:
            fails.append("bindings[%d]: `draw: %r` with no `field:` -- an unbound element is a "
                         "fabrication with pixels" % (i, dr))
        if dr not in DRAW_KINDS:
            fails.append("bindings[%d]: `draw: %r` is not one of %s" % (i, dr, sorted(DRAW_KINDS)))
        if not b.get("of"):
            fails.append("bindings[%d]: no `of:` -- the binding does not name the element it draws" % i)
        # R6 -- absence is declared, and never resolved to a default
        if b.get("if_absent") not in IF_ABSENT:
            fails.append("bindings[%d]: `if_absent` is %r, must be one of %s -- absence is a fact, "
                         "not a value" % (i, b.get("if_absent"), sorted(IF_ABSENT)))
        if "default" in b or "value" in b:
            fails.append("bindings[%d]: declares a default value for an absent field" % i)
        # R5 -- a condition names a recorded field
        if "when" in b:
            w = b["when"]
            if isinstance(w, dict):
                if not w.get("field"):
                    fails.append("bindings[%d]: `when` is a condition with no field behind it" % i)
                else:
                    kinds.add(_canonical(schema, w["field"]))
            elif w not in (True, False, None):
                fails.append("bindings[%d]: `when: %r` -- a condition must name a recorded field, "
                             "or be a literal boolean" % (i, w))
        # R4 -- the transform set is closed
        for key in ("from", "to"):
            if key in b and not _transform_ok(b[key]):
                fails.append("bindings[%d]: `%s: %r` is outside the closed transform set %s"
                             % (i, key, b[key], sorted(TRANSFORMS)))
        if "range" in b:
            r = b["range"]
            if not (isinstance(r, list) and len(r) == 2 and all(isinstance(x, (int, float)) for x in r)
                    and r[0] < r[1]):
                fails.append("bindings[%d]: `range: %r` is not a rising [lo, hi] pair -- a gauge is a "
                             "declared monotone map or it is decoration" % (i, r))
        if f:
            canon[i] = _canonical(schema, f)
            kinds.add(_canonical(schema, f))
    if fails:
        return fails          # do not cascade: schema rules below need clean fields

    # R2, first pass: every bound field must exist SOMEWHERE in the record, before any question of
    # which event. A name that exists nowhere is a fabrication the picture would assert.
    for i in sorted(canon):
        if canon[i] is None:
            near = _nearest_prefixed(schema, cart["bindings"][i].get("field"))
            fails.append("R2 bindings[%d]: `field: %r` exists in no recorded bundle%s -- a name "
                         "outside the record is a fabrication"
                         % (i, cart["bindings"][i].get("field"),
                            "" if not near else "; did you mean %r?" % near))
    if fails:
        return fails

    # Which event kind does this cart draw? A pattern like `round.wins` exists in ALL THREE kinds, so
    # a cart that binds only generic fields is ambiguous: it could be run against the wrong event and
    # nothing would say so. Resolution is the INTERSECTION over the bound fields, and a genuinely
    # ambiguous cart must declare `kind` explicitly.
    if cart.get("kind"):
        kinds_used = {cart["kind"]}
        if cart["kind"] not in schema["round"] and cart["kind"] != "any":
            return fails + ["cart declares `kind: %r`, which no recorded bundle has" % cart["kind"]]
    else:
        round_sets = []
        for k in sorted(kinds):
            s = _kinds_of(schema, k) - {"any"}
            if s:
                round_sets.append(s)
        if not round_sets:
            kinds_used = {"any"}          # binds nothing but facts common to every event
        else:
            kinds_used = set.intersection(*round_sets)
            if not kinds_used:
                return fails + ["cart binds fields from more than one event kind: %s -- a cart is one "
                                "cartridge" % sorted(set.union(*round_sets))]
            if len(kinds_used) > 1:
                return fails + ["cart binds only fields present in %s -- the binding does not say "
                                "which event it is a cartridge for; declare `kind`"
                                % sorted(kinds_used)]
    kind = sorted(kinds_used)[0]
    allowed = _schema_paths(schema, kind)

    for i, b in enumerate(cart["bindings"]):
        f = canon.get(i, "")
        # R2
        if f not in allowed:
            fails.append("R2 bindings[%d]: `field: %r` is not in the derived schema for kind %r "
                         "-- a name outside the record is a fabrication" % (i, f, kind))
            continue
        # R3 -- read the primitive, never the rendering
        if f in UNSAFE_DISPLAY:
            fails.append("R3 bindings[%d]: binds the stored display value %r -- in this record that "
                         "value disagrees with its own primitives on 52 of 119 graded entries; bind "
                         "%s instead" % (i, f, UNSAFE_DISPLAY[f]))
        if "when" in b and isinstance(b["when"], dict):
            wf = _canonical(schema, b["when"]["field"])
            if wf not in allowed:
                fails.append("R5 bindings[%d]: `when.field: %r` is not in the derived schema" % (i, wf))
        # a bound element must be drawable from the primitive, so a gauge names its own scale
        if b.get("draw") == "gauge" and "range" not in b:
            fails.append("bindings[%d]: a gauge with no `range` -- an undeclared scale is a scale the "
                         "cart chose, not one the record states" % i)

    # R9 -- THE CUE VOCABULARY IS THE RECORD'S, NOT THE CART'S. A cue name is an OUTCOME, and the
    # outcomes available to a cart are the ones its event's record can take -- derived above, per
    # kind, the same way the field list is. Two things this catches, and neither is taste:
    #   * a motif named after the DRAWING ("score", "miss") rather than the outcome is R3 one channel
    #     over -- the read rule with a sound where the number was;
    #   * a `resign` cue on an event whose record carries no unfinished run is a sound fired on a
    #     claim nobody recorded -- the audio twin of a plausible sprite where there is no field.
    # Silence is the default (spec 5), so `cues` may be absent entirely. It may not be invented.
    cues = cart.get("cues")
    if cues is not None:
        if not isinstance(cues, dict):
            fails.append("R9 `cues` is not an object -- a cue map is `outcome -> motif`")
        else:
            vocab = set(schema["round"].get(kind, {}).get("outcomes") or [])
            for name, motif in sorted(cues.items()):
                if name not in vocab:
                    fails.append("R9 cues: `%r` names no outcome this record carries for kind %r -- "
                                 "a sound fired on a claim with no carrier. The record's outcomes "
                                 "here are %s" % (name, kind, sorted(vocab)))
                if not isinstance(motif, str) or not motif.strip():
                    fails.append("R9 cues: `%r` declares no motif" % name)
    return fails


def _canonical(schema, field):
    """`aggregate` and `entrant.aggregate` are the same recorded field. -> the schema's own name."""
    if not isinstance(field, str):
        return None
    field = field.strip()
    if field in schema["entrant"]["fields"]:
        return field
    for k, v in schema["round"].items():
        if field in v["fields"]:
            return field
    for prefix in ("entrant.", "round."):
        if prefix + field in schema["entrant"]["fields"]:
            return prefix + field
        for k, v in schema["round"].items():
            if prefix + field in v["fields"]:
                return prefix + field
    return None


def _nearest_prefixed(schema, field):
    """For an error message only: the schema path whose last segment matches a bare name."""
    if not isinstance(field, str):
        return None
    seg = field.strip().split(".")[-1]
    hits = [p for p in schema["entrant"]["fields"] if p.split(".")[-1] == seg]
    for v in schema["round"].values():
        hits += [p for p in v["fields"] if p.split(".")[-1] == seg]
    return sorted(set(hits))[0] if hits else None


def _transform_ok(v):
    """The closed set: identity, 'a[0:2]', 'a[2:4]', 'index(n)', 'linear_map(lo,hi)', 'count_of(x)'."""
    if not isinstance(v, str):
        return False
    v = v.strip()
    if v in TRANSFORMS:
        return True
    if v.startswith("linear_map(") and v.endswith(")"):
        return True
    if v.startswith("index(") and v.endswith(")"):
        return True
    if v.startswith("count_of(") and v.endswith(")"):
        return True
    # a plain slice/index of a recorded string: name[2:4] or name[0:2]
    import re
    return bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]*\[\d*:\d*\]", v))


def _kinds_of(schema, field):
    """Which event kinds carry this field. 'any' = entrant-level, common to every event."""
    out = {k for k, v in schema["round"].items() if field in v["fields"]}
    if field in schema["entrant"]["fields"]:
        out.add("any")
    return out


# --- controls ----------------------------------------------------------------------------------

GOOD_CART = {
    "name": "fencing-json-schema",
    "kind": "structured_output",
    "atlas": "atlas/fencing.png",
    "bindings": [
        {"field": "round.wins", "draw": "gauge", "of": "score_bar", "range": [0, 6],
         "if_absent": "blank"},
        {"field": "round.trials", "draw": "text_panel", "of": "trial_count", "if_absent": "blank"},
        {"field": "round.items.R1.1_floor.score",
         "draw": "sprite", "of": "station_marker", "if_absent": "omit"},
        {"field": "round.finish_reasons.length", "draw": "text_panel", "of": "out_of_room_flag",
         "when": {"field": "round.finish_reasons.length"}, "if_absent": "blank"},
        {"field": "round.kind", "draw": "text_panel", "of": "event_label", "if_absent": "blank"},
    ],
    # THE CUE MAP IS `outcome -> motif`, and the outcome names are the record's (R9). The first
    # version of this example said {"score": "blip", "miss": "buzz"} -- names for the DRAWING, not the
    # outcome, which is the R3 defect with a sound where the number was. The honest three are the
    # room's own three (spec 5): win, loss, and resignation -- and resignation is legal here only
    # because structured_output's record carries runs that did not finish, which is derived, not
    # asserted. A cart on a kind that cannot run out would fail on this `cues` line, and should.
    "cues": {"win": "blip", "loss": "buzz", "resign": "descend"},
    "resolution": [320, 240],
}

BAD_CARTS = [
    ({"name": "x", "bindings": [{"draw": "gauge", "of": "g", "if_absent": "blank", "range": [0, 1]}]},
     "R1 an unbound draw target", "no `field:`"),
    ({"name": "x", "bindings": [{"field": "entrant.belt_colour_when_won", "draw": "sprite", "of": "belt",
                                 "if_absent": "blank"}]},
     "R2 a field not in the derived schema", "exists in no recorded bundle"),
    ({"name": "x", "bindings": [{"field": "aggregate", "draw": "gauge", "of": "belt_bar",
                                 "range": [0, 1], "if_absent": "blank"}]},
     "R3 the stored display value instead of its primitive", "R3 bindings"),
    ({"name": "x", "bindings": [{"field": "round.wins", "draw": "sprite", "of": "s",
                                 "from": "round.wins * 0.97", "if_absent": "blank"}]},
     "R4 a transform outside the closed set", "closed transform set"),
    ({"name": "x", "bindings": [{"field": "round.wins", "draw": "gauge", "of": "g", "range": [0, 6],
                                 "when": {"expr": "wins > 3"}, "if_absent": "blank"}]},
     "R5 a condition with no recorded field", "no field behind it"),
    ({"name": "x", "bindings": [{"field": "round.wins", "draw": "gauge", "of": "g", "range": [0, 6]}]},
     "R6 a binding that does not declare absence", "`if_absent` is None"),
    ({"name": "x", "autorun": "draw()", "bindings": [{"field": "round.wins", "draw": "gauge", "of": "g",
                                                      "range": [0, 6], "if_absent": "blank"}]},
     "R7 a cart carrying code/keys outside the closed set", "closed set"),
    ({"name": "x", "bindings": [{"field": "round.wins", "draw": "gauge", "of": "g",
                                 "if_absent": "zero"}]},
     "R6b absence resolved to a default value", "`if_absent` is 'zero'"),
    ({"name": "x", "bindings": [{"field": "round.wins", "draw": "gauge", "of": "g", "range": [0, 6],
                                 "if_absent": "blank"}]},
     "R8 kind-ambiguous: binds only fields every event carries", "declare `kind`"),
    (dict(GOOD_CART, cues={"fanfare": "blip"}),
     "R9 a cue naming an outcome the record cannot take", "R9 cues"),
    ({"name": "x", "bindings": [{"field": "round.kind", "draw": "state", "of": "out_of_room_flag",
                                 "if_absent": "blank"}]},
     "R10 a draw target with no primitive behind it", "not one of"),
]


def main(argv):
    schema = derive()
    blob = json.dumps(schema, sort_keys=True).encode()
    print("THE STATE SIDE OF THE BINDING CONTRACT")
    print("derived from %d recorded bundle(s), %d entrant entries"
          % (schema["derived_from"]["bundles"], schema["derived_from"]["entrant_entries"]))
    print("event kinds with recorded state: %s"
          % ", ".join("%s(%d fields)" % (k, len(v["fields"])) for k, v in schema["round"].items()))
    print("schema sha256 (first 12): %s" % hashlib.sha256(blob).hexdigest()[:12])
    with open(SCHEMA_PATH, "w", encoding="utf-8") as fh:
        json.dump(schema, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print("wrote %s" % os.path.relpath(SCHEMA_PATH, HERE))
    print("unsafe display fields, and what to bind instead:")
    for k, v in sorted(UNSAFE_DISPLAY.items()):
        print("  %-18s -> %s" % (k, v))
    print()

    print()
    print("THE OUTCOME VOCABULARY, DERIVED (what R9 lets a cart fire a cue on):")
    for k, v in schema["round"].items():
        print("  %-20s %s" % (k, ", ".join(v.get("outcomes") or []) or "(none)"))
    print()

    fails = []
    print("POSITIVE CONTROLS (each must fire, and for its OWN reason):")
    for cart, label, marker in BAD_CARTS:
        got = check_cart(cart, schema)
        right = any(marker in g for g in got)
        if not got:
            print("  %-9s %s" % ("DID NOT FIRE -- decoration", label))
            fails.append("positive control did not fire: %s" % label)
        elif not right:
            print("  %-9s %s" % ("WRONG REASON", label))
            for g in got:
                print("        %s" % g)
            fails.append("positive control fired for the wrong reason: %s (wanted %r)" % (label, marker))
        else:
            print("  %-9s %s" % ("FIRES", label))
    print()
    # R9b -- the "and, if it has one" clause, EXERCISED rather than described. Every kind in THIS
    # record carries an unfinished run, so the permissive branch is the live one and this control is
    # the only way to prove the restrictive one exists: removing `resign` from the honest cart's kind
    # is exactly what a future kind with no truncation state would look like, and the same cart must
    # then FAIL -- and fail ON THE CUE, not on something else.
    stripped = json.loads(json.dumps(schema))
    stripped["round"][GOOD_CART["kind"]]["outcomes"] = [
        o for o in stripped["round"][GOOD_CART["kind"]]["outcomes"] if o != "resign"]
    got = check_cart(GOOD_CART, stripped)
    if any("R9 cues" in g for g in got):
        print("  %-9s R9b a `resign` cue on a kind whose record cannot run out" % "FIRES")
    else:
        print("  %-9s R9b a `resign` cue on a kind whose record cannot run out -- the clause is "
              "described, not exercised" % "DID NOT FIRE")
        fails.append("R9b control did not fire: the resign clause is unenforced")
    print()
    print("NEGATIVE CONTROL (an honest cart must PASS):")
    got = check_cart(GOOD_CART, schema)
    if got:
        print("  FAIL  the honest cart was rejected -- the rule bans what it must permit")
        for g in got:
            print("        %s" % g)
        fails.append("negative control: an honest cart must pass")
    else:
        print("  ok    the honest cart passes on kind %s" % GOOD_CART["kind"])
    print()

    for p in (argv or []):
        cart = json.load(open(p, encoding="utf-8"))
        got = check_cart(cart, schema)
        print("%s: %s" % (p, "FAIL" if got else "ok"))
        for g in got:
            print("    %s" % g)
        fails.extend(got)

    if fails:
        print("\n%d violation(s)" % len(fails))
        return 1
    print("no violations: every draw target is bound, every field is in the derived schema, no "
          "display value is read in place of its primitive, and every cue names an outcome the "
          "record carries")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
