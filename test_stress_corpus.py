"""Full pytest suite for the meta-accentor: exact word-level stress checks.

Three groups of expectations, matching the corpus:
  A  homographs whose reading depends on context (замок castle / замок lock)
  B  words Russian speakers commonly stress wrong, plus ё handling
  C  further contested or context-dependent pairs

Plus behavioural tests: punctuation, word count, no duplicated '+', latin
characters and digits surviving, empty input.

The gold strings are Russian on purpose — that is the language under test.
Run:  pytest -q
"""
import re

import pytest

from meta_accent import _tokenize, accent


def plus_of(word, out):
    """Return the '+' form of `word` as it appears in `out`, or None."""
    target = word.lower().replace("ё", "е")
    for token in _tokenize(out):
        if token.replace("+", "").lower().replace("ё", "е") == target:
            return token.lower()
    return None


def check_word(text, word, expected):
    out = accent(text)
    got = plus_of(word, out)
    assert got == expected.lower(), (
        f"'{text}' word '{word}': got {got!r}, expected {expected.lower()!r} | out={out!r}"
    )


# ----------------------------------------------------------------- group A

A = [
    ("Дверной замок крепкий.", "замок", "зам+ок"),
    ("Старинный замок на горе.", "замок", "з+амок"),
    ("Настоящая мука для повара.", "мука", "м+ука"),
    ("Для пирога нужна мука.", "мука", "мук+а"),
    ("В продукте много белка.", "белка", "белк+а"),
    ("Белки прыгали по веткам.", "белки", "б+елки"),
    ("Атлас тканей купили.", "Атлас", "+атлас"),
    ("Платье из атласа.", "атласа", "атл+аса"),
    ("Орган звучал в соборе.", "Орган", "+орган"),
    ("У больного болел орган.", "орган", "орг+ан"),
    ("Я плачу от счастья.", "плачу", "пл+ачу"),
    ("Я плачу за обед.", "плачу", "плач+у"),
    ("Уже поздно.", "Уже", "у+же"),
    ("Река стала уже.", "уже", "уж+е"),
    ("Дорога вела в горы.", "Дорога", "дор+ога"),
    ("И мне она дорога.", "дорога", "дорог+а"),
]


@pytest.mark.parametrize("text,word,expected", A)
def test_a_homographs(text, word, expected):
    check_word(text, word, expected)


# ----------------------------------------------------------------- group B

B = [
    ("Заключили договор.", "договор", "догов+ор"),
    ("Она звонит мне.", "звонит", "звон+ит"),
    ("Свекла полезна.", "свекла", "св+ёкла"),
    ("Щавель из огорода.", "щавель", "щав+ель"),
    ("Возьми торты.", "торты", "т+орты"),
    ("Первый квартал.", "квартал", "кварт+ал"),
    ("Каталог товаров.", "каталог", "катал+ог"),
    ("Нашли средства.", "средства", "ср+едства"),
    ("Обеспечение качества.", "обеспечение", "обесп+ечение"),
    ("Феномен науки.", "феномен", "фен+омен"),
    ("Кухонные газы.", "кухонные", "к+ухонные"),
    ("Газопровод протянули.", "газопровод", "газопров+од"),
    ("Ходатайство приняли.", "ходатайство", "ход+атайство"),
    ("Досуг провели.", "досуг", "дос+уг"),
    ("Это красивее.", "красивее", "крас+ивее"),
    ("Она стоит в гараже.", "стоит", "ст+оит"),
]


@pytest.mark.parametrize("text,word,expected", B)
def test_b_common_errors(text, word, expected):
    check_word(text, word, expected)


# ----------------------------------------------------------------- group C

C = [
    ("Купить хлеба.", "хлеба", "хл+еба"),
    ("В поле хлеба.", "хлеба", "хлеб+а"),
    ("Он поднял руки.", "руки", "р+уки"),
    ("Одной руки.", "руки", "рук+и"),
    ("Налей воды.", "воды", "вод+ы"),
    ("Минеральные воды.", "воды", "в+оды"),
    ("Ты молодец.", "молодец", "м+олодец"),
]


@pytest.mark.parametrize("text,word,expected", C)
def test_c_context_pairs(text, word, expected):
    check_word(text, word, expected)


# --------------------------------------------------- both readings in one text

def test_organ_both_readings():
    out = accent("Орган звучал, орган болел.")
    assert "+орган" in out.lower() and "орг+ан" in out.lower(), out


def test_uzhe_both_readings():
    out = accent("Уже поздно, но река стала уже.")
    assert "у+же" in out.lower() and "уж+е" in out.lower(), out


def test_atlas_both_readings():
    out = accent("Атлас тканей купили, платье из атласа сшили.")
    assert "+атлас" in out.lower() and "атл+ас" in out.lower(), out


# ------------------------------------------------------------- behavioural

def test_punctuation_preserved():
    out = accent("«Позвони позже», — попросила Мария, и он ушел.")
    for ch in ["«", "»", ",", "—", ".", " "]:
        assert ch in out, f"missing {ch!r} in {out!r}"


def test_period_and_dash_not_dropped():
    out = accent("Дверной замок крепкий. Он стоит в гараже — тихо.")
    assert out.count(".") == 2 and "—" in out, out


def test_no_duplicated_plus():
    out = accent("У больного болел орган.")
    assert "орг+ан" in out.lower() and "++" not in out, out


def test_survives_latin_and_digits():
    out = accent("Интеграция с API завершилась, релиз вышел 25 марта.")
    assert "интегр+ация" in out.lower(), out
    assert "25" in out


def test_empty_input():
    assert accent("") is not None


def test_word_count_preserved():
    text = "«Позвони позже», — попросила Мария. Он взял торты, каталог и договор."
    n_in = len(re.findall(r"[А-Яа-яЁё]+", text))
    n_out = len(re.findall(r"[А-Яа-яЁё]+", accent(text).replace("+", "")))
    assert n_in == n_out, f"words lost: {n_in} -> {n_out}"


def test_dialogue_punctuation_preserved():
    out = accent("«Позвони позже», — сказал он, — и я плачу за обед.")
    for ch in ["«", "»", ",", "—"]:
        assert ch in out, f"{ch!r} lost: {out!r}"
