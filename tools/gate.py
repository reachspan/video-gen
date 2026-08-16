#!/usr/bin/env python3
"""Pre-generation gates. Run before spending credits.

G2 element coverage  - every required element must survive into the prompt
G3 constraint conflict - no prompt clause may contradict the premise

A constraint added for one reason can delete a required element as a side effect,
and nothing downstream will catch it: every other check in the pipeline measures
pixels, not meaning."""
import json, re, sys

STOP = set("""a an the of in on at to and or with his her its this that is are be as
for from into by up out over under near just only very much each both all some no not
so that it he she they them their there here what which who whom whose about roughly
about approximately across around""".split())


def toks(s):
    return {w for w in re.findall(r"[a-z]+", s.lower()) if len(w) > 3 and w not in STOP}


def stem(w):
    for suf in ("ing", "ed", "es", "s"):
        if w.endswith(suf) and len(w) - len(suf) > 3:
            return w[: -len(suf)]
    return w


def stems(ws):
    return {stem(w) for w in ws}


def main(intent_path, prompt_path, thresh=0.34):
    intent = json.load(open(intent_path))
    prompt = open(prompt_path).read()
    ptoks = stems(toks(prompt))
    fails = []

    print(f"== {prompt_path.split('/')[-1]} ==")
    print("\nG2 element coverage")
    for el in intent["elements"]:
        if el["necessity"] != "required":
            continue
        want = stems(toks(el["what"]))
        hit = want & ptoks
        cov = len(hit) / max(len(want), 1)
        ok = cov >= thresh
        print(f"  [{'OK ' if ok else 'MISS'}] {el['id']:<20} coverage {cov:.0%}")
        if not ok:
            print(f"         function: {el['function'][:78]}")
            print(f"         absent:   {', '.join(sorted(want - hit)[:8])}")
            fails.append(f"G2 missing required element '{el['id']}'")

    # Sentence-scoped so a phrase must actually be asserted together. Document-wide
    # token matching produced false positives ("wide" from "wide phone lens" plus
    # "shot" from "medium shot" => phantom "wide shot"), and a noisy gate gets ignored.
    sents = [s for s in re.split(r"[.\n]", re.sub(r"\s+", " ", prompt.lower())) if s.strip()]

    def asserted(phrase, need=0.8):
        pt = stems(toks(phrase))
        if not pt:
            return None
        for s in sents:
            if len(pt & stems(toks(s))) / len(pt) >= need:
                return s.strip()
        return None

    print("\nG3 constraint conflict")
    for f in intent["forbidden_assertions"]:
        hit = asserted(f)
        if hit:
            print(f"  [FAIL] forbidden assertion '{f}'")
            print(f"         found in: \"{hit[:88]}\"")
            fails.append(f"G3 prompt asserts forbidden '{f}'")
        else:
            print(f"  [OK ] not asserted: '{f}'")

    print("\nG4 affect / composition")
    for key, sec in (("forbidden_affect", "performance"), ("forbidden", "composition")):
        for bad in intent[sec].get(key, []):
            hit = asserted(bad, need=1.0)
            if hit:
                print(f"  [FAIL] {sec} forbids '{bad}'")
                print(f"         found in: \"{hit[:88]}\"")
                fails.append(f"{sec} forbids '{bad}'")
            else:
                print(f"  [OK ] not asserted: '{bad}'")

    print(f"\nRESULT: {'PASS' if not fails else 'FAIL (' + str(len(fails)) + ')'}")
    for f in fails:
        print("  -", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
