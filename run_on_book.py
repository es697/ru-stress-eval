"""Run the meta-accentor over a real book chapter and count its corrections.

Corpus sentences are short and controlled. This script checks the other
extreme: running prose with long sentences, dialogue dashes and quotation
marks, where the meta layer has to leave punctuation and word count alone.

The sample is the first night of Dostoevsky's "White Nights" (1848, public
domain), in chapter.txt.

Run:  python run_on_book.py
"""
import re
import sys

sys.path.insert(0, ".")
from meta_accent import accent, base_stress  # noqa: E402

WORD = re.compile(r"[А-Яа-яЁё]+\+?[А-Яа-яЁё]*")
PLAIN_WORD = re.compile(r"[А-Яа-яЁё]+")


def main():
    text = open("chapter.txt", encoding="utf-8").read()
    paragraphs = [p for p in text.split("\n\n") if p.strip()]

    print("chapter: Dostoevsky, \"White Nights\", Night One")
    print(f"paragraphs: {len(paragraphs)}, words: {len(PLAIN_WORD.findall(text))}\n")

    corrections = []
    for paragraph in paragraphs:
        base = base_stress(paragraph)
        meta = accent(paragraph)
        for before, after in zip(WORD.findall(base), WORD.findall(meta)):
            if before != after:
                corrections.append((before, after))

    print(f"meta corrections (words where meta differs from base): {len(corrections)}")
    for before, after in corrections[:40]:
        print(f"   {before} -> {after}")
    if len(corrections) > 40:
        print(f"   ... and {len(corrections) - 40} more")

    # Sanity checks: the meta layer must not touch anything but the '+' marks.
    base = base_stress(text)
    meta = accent(text)
    print()
    print("word count preserved:", len(PLAIN_WORD.findall(base)) == len(PLAIN_WORD.findall(meta)))
    print("double '+' introduced:", "++" in meta)


if __name__ == "__main__":
    main()
