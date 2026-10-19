"""Compare four Russian stress-placement engines on the gold corpus.

Each engine takes a sentence and returns it with a '+' placed before every
stressed vowel. The scorer aligns the engine output with the gold annotation
word by word and reports three numbers:

  word_acc       share of aligned words whose stress mark matches the gold
  homograph_acc  accuracy on the group-A homograph pairs (замок castle / замок
                 lock, мука flour / мука torment, ...), where context has to
                 pick the reading
  yo_acc         share of words that contain ё in the gold annotation and keep
                 it in the engine output

Run:  python bench_engines.py
"""
import re
import sys

sys.path.insert(0, ".")
from corpus import CORPUS  # noqa: E402

TOKEN = re.compile(r"[А-Яа-яЁё]+(?:\+[А-Яа-яЁё]+)?")


# ---------------------------------------------------------------- engines

def ruaccent_proc():
    """RUAccent with the turbo omograph model and its built-in dictionary."""
    from ruaccent import RUAccent

    a = RUAccent()
    a.load(omograph_model_size="turbo3.1", use_dictionary=True, workdir="./models_ru")
    return a.process_all


def make_stressonnx(model):
    """stressonnx wrappers around the packaged ONNX models."""
    from stressonnx import stress

    return lambda text: stress(text, "ru", model=model, notation="plus")


ENGINES = {
    "RUAccent turbo3.1": ruaccent_proc,
    "stressonnx/ruaccent": lambda: make_stressonnx("ruaccent"),
    "stressonnx/silero": lambda: make_stressonnx("silero"),
    "stressonnx/simple": lambda: make_stressonnx("simple"),
}


# ---------------------------------------------------------------- scoring

def tokens(s):
    return TOKEN.findall(s)


def stress_index(word):
    """Index of the stressed vowel inside the bare word, or None."""
    m = re.match(r"^([А-Яа-яЁё]*)\+", word)
    return len(m.group(1)) if m else None


def bare(word):
    return word.replace("+", "")


def main():
    loaded = {name: factory() for name, factory in ENGINES.items()}

    print("| Engine | word_acc | homograph_acc | yo_acc |")
    print("|---|---|---|---|")

    for name, fn in loaded.items():
        word_hits, homo_hits, yo_hits = [], [], []
        diffs = []

        for label, rows in CORPUS.items():
            for text, expected in rows:
                got = fn(text)
                exp_tokens, got_tokens = tokens(expected), tokens(got)
                n = min(len(exp_tokens), len(got_tokens))

                hits = total = 0
                for i in range(n):
                    if bare(exp_tokens[i]) != bare(got_tokens[i]):
                        continue
                    total += 1
                    if stress_index(exp_tokens[i]) == stress_index(got_tokens[i]):
                        hits += 1
                word_hits.append(hits / total if total else 0.0)

                # group A holds homograph pairs; the second word is the one
                # whose reading depends on context
                if label == "A" and len(exp_tokens) > 1 and len(got_tokens) > 1:
                    if bare(exp_tokens[1]) == bare(got_tokens[1]):
                        ok = stress_index(exp_tokens[1]) == stress_index(got_tokens[1])
                        homo_hits.append(1.0 if ok else 0.0)
                        if not ok:
                            diffs.append((text, exp_tokens[1], got_tokens[1]))

                if "ё" in bare(expected):
                    yo_hits.append(1.0 if "ё" in bare(got) else 0.0)

        word = sum(word_hits) / len(word_hits) if word_hits else 0.0
        homo = sum(homo_hits) / len(homo_hits) if homo_hits else 0.0
        yo = sum(yo_hits) / len(yo_hits) if yo_hits else 0.0

        print(f"| {name} | {word:.3f} | {homo:.3f} | {yo:.3f} |")

        if diffs:
            for text, expected_word, got_word in diffs[:6]:
                print(f"    {name} MISS: {text} -> {got_word} (expected {expected_word})")

    # Show what a correct '+' rendering looks like, using the strongest engine.
    print("\n### Reference '+' output (RUAccent turbo3.1), group A ###")
    fn = loaded["RUAccent turbo3.1"]
    for text, _expected in CORPUS["A"]:
        print(f"  {fn(text)}")


if __name__ == "__main__":
    main()
