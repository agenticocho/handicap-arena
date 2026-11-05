#!/usr/bin/env python3
"""DEFINITIONS -- WordNet terse-definition clues, and the measurement that decides the design.

Why terse and not the gloss. A WordNet gloss conceals its answer and still identifies it: `"a committee
having supervisory powers"` fits BOARD and essentially nothing else, so a crate built from glosses has a
ceiling of 20/20 and the crossings are decoration. **Concealment and ambiguity are different requirements.**
A clue is a TERSE definition -- one to four words cut from the gloss -- because terseness is what makes a
definition fit several words, and that is what makes the grid load-bearing.

Filters, both mechanical, both applied here:
  * STEM-clean: no token of the clue shares a Porter stem with the answer. A token test leaks
    (`WRAPS :: "cloak that is folded or wrapped around a person"`), and the leak is the same defect as the
    crate's, one layer down.
  * POS-matched: the sense's part of speech is recorded, so a verb gloss cannot stand in for a noun entry.

    python3 definitions.py --out definitions.json
    python3 definitions.py --report      # ambiguity distribution, the number that decides the design
"""
import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEXICON = HERE / "wordlist_3_7.txt"
ARTICLES = {"a", "an", "the"}
MAX_SENSE_RANK = 2      # the 3 most frequent senses of a word; beyond that a gloss describes a rare usage


def stemmer():
    from nltk.stem import PorterStemmer
    ps = PorterStemmer()
    return ps.stem


def hypernym_clue(sense, stem, answer_stem, max_words=3):
    """A DEFINITION THAT KEEPS THE SENSE. Truncating a gloss takes its modifier and discards its head --
    "lightweight cord..." becomes the clue "lightweight", which reads as an adjective meaning tiny while the
    answer STRINGS is the noun. A hypernym lemma is short by construction and names the sense: cord, war,
    advantage. Instance hypernyms cover proper-noun senses."""
    names = []
    for h in list(sense.hypernyms()) + list(getattr(sense, "instance_hypernyms", lambda: [])()):
        for l in h.lemmas():
            nm = l.name().replace("_", " ").lower()
            toks = nm.split()
            if not toks or len(toks) > max_words:
                continue
            if any(stem(t) == answer_stem for t in toks):
                continue
            names.append(nm)
    if not names:
        return None
    names.sort(key=lambda x: (len(x.split()), len(x)))
    return names[0]


def terse_of(gloss, stem, answer_stem, max_words=4):
    """The shortest leading phrase of the gloss that is a definition in its own right."""
    words = re.findall(r"[A-Za-z'-]+", gloss)
    body = [w for w in words if w.lower() not in ARTICLES]
    for n in range(1, max_words + 1):
        if len(body) < n:
            break
        phrase = " ".join(body[:n])
        if any(stem(w.lower()) == answer_stem for w in body[:n]):
            return None
        if n >= 1 and len(phrase) >= 3:
            cand = phrase
            # a terse definition must not end on a connective; stop before one
            if cand.split()[-1].lower() in {"of", "in", "on", "with", "that", "which", "for", "and", "or"}:
                continue
            return cand.lower()
    return None


def build(lexicon):
    stem = stemmer()
    from nltk.corpus import wordnet as wn
    POS = {"n": "n", "v": "v", "a": "a", "s": "a", "r": "r"}
    out, missing = {}, 0
    for w in lexicon:
        ans_stem = stem(w.lower())
        senses = []
        for rank, s in enumerate(wn.synsets(w.lower())):
            if rank > MAX_SENSE_RANK:      # WordNet orders synsets by frequency: rank 0 is the common sense
                break
            gloss = s.definition()
            if not gloss or len(gloss) > 60:
                continue
            toks = re.findall(r"[A-Za-z'-]+", gloss.lower())
            if any(stem(t) == ans_stem for t in toks):
                continue
            terse = terse_of(gloss, stem, ans_stem)
            clue = hypernym_clue(s, stem, ans_stem)
            if not clue:
                continue
            senses.append(dict(gloss=gloss, terse=terse, clue=clue, pos=POS.get(s.pos(), s.pos()),
                               synset=s.name(), sense_rank=rank))
        if senses:
            out[w] = senses
        else:
            missing += 1
    return out, missing


def report(defs):
    """How ambiguous is a terse definition, against how ambiguous a full gloss is?"""
    terse_index, gloss_index = defaultdict(list), defaultdict(list)
    for w, senses in defs.items():
        for s in senses:
            terse_index[s["terse"]].append(w)
            gloss_index[s["gloss"]].append(w)
    t_counts = Counter(len(v) for v in terse_index.values())
    g_counts = Counter(len(v) for v in gloss_index.values())
    n_terse, n_gloss = sum(len(v) for v in terse_index.values()), sum(len(v) for v in gloss_index.values())

    def share(counts, total, limit):
        return round(sum(c for k, c in counts.items() if k <= limit) / total, 4) if total else None

    print(f"words with >=1 clean sense: {len(defs)}")
    print(f"terse definitions {len(terse_index)} (senses {n_terse})   glosses {len(gloss_index)} (senses {n_gloss})")
    print(f"  terse: unique-to-one-word {share(t_counts, n_terse, 1)}   shared by >=2 {share(t_counts, n_terse, 99) and round(1 - share(t_counts, n_terse, 1), 4)}")
    print(f"  gloss: unique-to-one-word {share(g_counts, n_gloss, 1)}")
    print(f"  busiest terse definitions: {[(k, len(v)) for k, v in sorted(terse_index.items(), key=lambda kv: -len(kv[1]))[:5]]}")
    return terse_index, gloss_index


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lexicon", default=str(LEXICON))
    ap.add_argument("--out", default=str(HERE / "definitions.json"))
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    lexicon = sorted({w.strip().upper() for w in Path(a.lexicon).read_text().split() if w.strip()})
    defs, missing = build(lexicon)
    p = Path(a.out)
    p.write_text(json.dumps(dict(lexicon_size=len(lexicon), sourced="WordNet 3.0 via NLTK",
                                 stemmer="porter", max_terse_words=4, max_gloss_chars=60,
                                 words=defs), indent=0) + "\n")
    print(f"lexicon {len(lexicon)}  with clean senses {len(defs)}  without {missing}  wrote {p}")
    if a.report:
        report(defs)
    return 0


if __name__ == "__main__":
    sys.exit(main())
