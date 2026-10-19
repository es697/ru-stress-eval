"""Benchmark: base stressonnx/ruaccent vs the meta-accentor on the same corpus.

Reports word accuracy, homograph accuracy and ё accuracy for both, so the
effect of the meta layer (collocations + overrides + defaults) is measurable
rather than anecdotal.

Run:  ./.venv/bin/python bench_meta.py
"""
import re
import sys

sys.path.insert(0, ".")
from corpus import CORPUS  # noqa: E402
from meta_accent import accent, base_stress  # noqa: E402

TOKEN = re.compile(r"[А-Яа-яЁё]+(?:\+[А-Яа-яЁё]+)?")


def tokens(s):
    return TOKEN.findall(s)


def stress_index(word):
    """Index of the stressed vowel inside the bare word, or None."""
    m = re.match(r"^([А-Яа-яЁё]*)\+", word)
    return len(m.group(1)) if m else None


def bare(word):
    return word.replace("+", "")


def evaluate(fn):
    """Score one accentor over the whole corpus."""
    word_hit = word_total = 0
    homo_hit = homo_total = 0
    yo_hit = yo_total = 0
    fixed = []

    for label, rows in CORPUS.items():
        for text, expected in rows:
            got = fn(text)
            exp_tokens, got_tokens = tokens(expected), tokens(got)
            n = min(len(exp_tokens), len(got_tokens))

            for i in range(n):
                e, g = exp_tokens[i], got_tokens[i]
                if bare(e) != bare(g):
                    continue
                word_total += 1
                ei, gi = stress_index(e), stress_index(g)
                if (ei is None and gi is None) or ei == gi:
                    word_hit += 1

            # Group A is built from homograph pairs: the second word carries the
            # disambiguation, so that is what we score.
            if label == "A" and len(exp_tokens) > 1 and len(got_tokens) > 1:
                if bare(exp_tokens[1]) == bare(got_tokens[1]):
                    homo_total += 1
                    if stress_index(exp_tokens[1]) == stress_index(got_tokens[1]):
                        homo_hit += 1
                    else:
                        fixed.append((text, exp_tokens[1], got_tokens[1]))

            if "ё" in bare(expected):
                yo_total += 1
                if "ё" in bare(got):
                    yo_hit += 1

    return {
        "word": word_hit / word_total if word_total else 0.0,
        "homograph": homo_hit / homo_total if homo_total else 0.0,
        "yo": yo_hit / yo_total if yo_total else 0.0,
        "missed_homographs": fixed,
    }


def main():
    base = evaluate(base_stress)
    meta = evaluate(accent)

    print("| Accentor | word_acc | homograph_acc | yo_acc |")
    print("|---|---|---|---|")
    print(f"| stressonnx/ruaccent (base) | {base['word']:.3f} | {base['homograph']:.3f} | {base['yo']:.3f} |")
    print(f"| meta-accentor | {meta['word']:.3f} | {meta['homograph']:.3f} | {meta['yo']:.3f} |")
    print()
    delta = meta["homograph"] - base["homograph"]
    print(f"homograph accuracy: {base['homograph']:.3f} -> {meta['homograph']:.3f} ({delta:+.3f})")
    print(f"word accuracy:      {base['word']:.3f} -> {meta['word']:.3f} ({meta['word'] - base['word']:+.3f})")

    if base["missed_homographs"]:
        print(f"\nhomographs the base got wrong ({len(base['missed_homographs'])}):")
        for text, exp, got in base["missed_homographs"]:
            print(f"  {text}\n    expected {exp}, base said {got}")
    if meta["missed_homographs"]:
        print(f"\nhomographs the meta layer still gets wrong ({len(meta['missed_homographs'])}):")
        for text, exp, got in meta["missed_homographs"]:
            print(f"  {text}\n    expected {exp}, meta said {got}")


if __name__ == "__main__":
    main()
