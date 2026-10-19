"""Show base vs meta-accentor on a dense paragraph of homographs.

The paragraph deliberately packs every homograph pair from the corpus into
running text, so the diff between the two outputs is the whole point: the base
model has to guess from a single word, the meta layer gets the clause as
context.

Run:  python run_meta.py
"""
import re
import sys

sys.path.insert(0, ".")
from meta_accent import accent, base_stress  # noqa: E402

PARAGRAPH = (
    "Старинный замок на холме давно открыли для туристов, а дверной замок у входа так и не починили. "
    "Настоящая мука для смотрителя — когда по утрам он стоит у окна и видит, как на дорогу опускается туман. "
    "Он звонит в управление, просит средства на ремонт, но ему обещают всё и ничего: «Позвони позже», — отвечают, "
    "и он, вздыхая, вешает трубку. Для пирога нужна мука, и это была настоящая мука — он взбивал белки, "
    "пока белка не кончилась. Атлас тканей лежал на столе, а платье из атласа, сшитое к свадьбе, переливалось на свету. "
    "Орган в соборе звучал торжественно, и у бабушки, которая пришла послушать, уже болел слух — её орган сдавал. "
    "Я плачу от радости, когда плачу за обед, и уже понимаю, что река стала уже. "
    "Дорога вела в горы, и мне она дорога; красивее всего были торты в каталоге, договор подписали, "
    "щавель привезли из огорода, свёкла полезна, средства нашли, обеспечение качества, феномен науки, "
    "кухонные газы, газопровод протянули, ходатайство приняли, а досуг провели втроём."
)

WORD = re.compile(r"[А-Яа-яЁё]+\+?[А-Яа-яЁё]*")


def main():
    base = base_stress(PARAGRAPH)
    meta = accent(PARAGRAPH)

    base_words = WORD.findall(base)
    meta_words = WORD.findall(meta)
    fixes = [(b, m) for b, m in zip(base_words, meta_words) if b != m]

    print(f"words: {len(re.findall(r'[А-Яа-яЁё]+', PARAGRAPH))}")
    print(f"meta corrections: {len(fixes)} of {len(base_words)} words\n")

    for before, after in fixes:
        print(f"  {before} -> {after}")


if __name__ == "__main__":
    main()
