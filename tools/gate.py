#!/usr/bin/env python3
"""Pre-generation gates. Run before spending credits.

  gate.py INTENT.json PROMPT.txt [PREVIOUS.txt]

G1 element coverage    - every required element must survive into the prompt
G2 constraint conflict - no prompt clause may assert a forbidden sentence
G3 affect/composition  - nor a forbidden affect or framing

A constraint added for one reason can delete a required element as a side effect,
and nothing downstream will catch it: every other check in the pipeline measures
pixels, not meaning.

Then a note, which gates nothing and changes no exit code. When a block has grown
a lot while the required element inside it still says what it said before, the
addition may now outweigh what it protects - G1 scores words present, not words
that won. PREVIOUS.txt defaults to the highest prompt.v<n>.txt beside this one."""
import json, pathlib, re, sys

STOP = set("""a an the of in on at to and or with his her its this that is are be as
for from into by up out over under near just only very much each both all some no not
so it he she they them their there here what which who whom whose about roughly
approximately across around""".split())


def toks(s):
    return {w for w in re.findall(r"[a-z]+", s.lower()) if len(w) > 3 and w not in STOP}


def stem(w):
    for suf in ("ing", "ed", "es", "s"):
        if w.endswith(suf) and len(w) - len(suf) > 3:
            return w[: -len(suf)]
    return w


def stems(ws):
    return {stem(w) for w in ws}


# A block header is a short line in capitals on its own: GLOBAL STYLE, PROP AND
# HANDS, TIMELINE. Capitalised words inside a sentence sit on longer lines.
HEAD = re.compile(r"^[A-Z][A-Z0-9 /&'()-]{2,28}$")


def split_blocks(text):
    """{block name: body}. Everything before the first header is dropped."""
    out, name, body = {}, None, []
    for line in text.splitlines():
        if HEAD.match(line.strip()):
            if name:
                out[name] = "\n".join(body)
            name, body = line.strip(), []
        elif name:
            body.append(line)
    if name:
        out[name] = "\n".join(body)
    return out


def anchor(blocks, want):
    """The block a required element lives in, and its clearest sentence there."""
    best = None
    for name, body in blocks.items():
        for s in re.split(r"(?<=[.!?])\s+|\n", body):
            if not s.strip():
                continue
            score = len(want & stems(toks(s)))
            if best is None or score > best[0]:
                best = (score, name, " ".join(s.split()))
    return best if best and best[0] else None


def previous(prompt_path):
    """The highest-numbered earlier revision beside this one, by convention."""
    p = pathlib.Path(prompt_path)
    m = re.search(r"\.v(\d+)\.", p.name)
    if not m:
        return None
    n = int(m.group(1))
    earlier = []
    for q in p.parent.glob(p.name.replace(f".v{n}.", ".v*.")):
        k = re.search(r"\.v(\d+)\.", q.name)
        if k and int(k.group(1)) < n:
            earlier.append((int(k.group(1)), q))
    return max(earlier)[1] if earlier else None


def note_growth(intent, prompt, prompt_path, prev_path, min_words=25, min_frac=0.25):
    """Blocks that grew while the element inside them stayed the same.

    Not a gate. A revision loses an element by outweighing it rather than by
    deleting it, which every other check here is blind to by construction.
    """
    prev_path = prev_path or previous(prompt_path)
    if not prev_path or not pathlib.Path(prev_path).exists():
        return
    prev = pathlib.Path(prev_path).read_text()
    now_b, was_b = split_blocks(prompt), split_blocks(prev)
    if not now_b or not was_b:
        return

    grown = {}
    for el in intent["elements"]:
        if el["necessity"] != "required":
            continue
        want = stems(toks(el["what"]))
        a, b = anchor(now_b, want), anchor(was_b, want)
        if not a or not b or a[2] != b[2]:      # assertion itself was rewritten
            continue
        name = a[1]
        if name not in was_b:
            continue
        old, new = len(was_b[name].split()), len(now_b[name].split())
        if new - old >= min_words and new - old >= old * min_frac:
            grown.setdefault((name, old, new), []).append(el["id"])

    if not grown:
        return
    print(f"\nnote  (against {pathlib.Path(prev_path).name})")
    for (name, old, new), ids in grown.items():
        print(f"  {name} grew {old} -> {new} words; "
              f"{', '.join(ids)} unchanged inside it.")
    print("  Check the additions against docs/prompt-language.md.")


def main(intent_path, prompt_path, prev_path=None, thresh=0.34):
    intent = json.load(open(intent_path))
    prompt = open(prompt_path).read()
    ptoks = stems(toks(prompt))
    fails = []

    print(f"== {prompt_path.split('/')[-1]} ==")
    print("\nG1 element coverage")
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
            fails.append(f"G1 missing required element '{el['id']}'")

    # Sentence-scoped, so a phrase counts as asserted only where it appears
    # together. Matching across the whole document instead invents phrases out of
    # tokens from unrelated clauses, and a noisy gate gets ignored.
    sents = [s for s in re.split(r"[.\n]", re.sub(r"\s+", " ", prompt.lower())) if s.strip()]

    def asserted(phrase, need=0.8):
        pt = stems(toks(phrase))
        if not pt:
            return None
        for s in sents:
            if len(pt & stems(toks(s))) / len(pt) >= need:
                return s.strip()
        return None

    print("\nG2 constraint conflict")
    for f in intent["forbidden_assertions"]:
        hit = asserted(f)
        if hit:
            print(f"  [FAIL] forbidden assertion '{f}'")
            print(f"         found in: \"{hit[:88]}\"")
            fails.append(f"G2 prompt asserts forbidden '{f}'")
        else:
            print(f"  [OK ] not asserted: '{f}'")

    print("\nG3 affect / composition")
    for key, sec in (("forbidden_affect", "performance"), ("forbidden", "composition")):
        for bad in intent[sec].get(key, []):
            hit = asserted(bad, need=1.0)
            if hit:
                print(f"  [FAIL] {sec} forbids '{bad}'")
                print(f"         found in: \"{hit[:88]}\"")
                fails.append(f"G3 {sec} forbids '{bad}'")
            else:
                print(f"  [OK ] not asserted: '{bad}'")

    note_growth(intent, prompt, prompt_path, prev_path)

    print(f"\nRESULT: {'PASS' if not fails else 'FAIL (' + str(len(fails)) + ')'}")
    for f in fails:
        print("  -", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:4]))
