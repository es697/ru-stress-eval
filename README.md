# ru-stress-eval

Benchmark and post-processing layer for **Russian word stress placement**.

Russian stress is not fixed to a syllable: `замок` is *castle* with stress on the
first syllable and *lock* with stress on the second, and the only way to tell
them apart is context. Text-to-speech and audiobook pipelines need this right,
because a wrongly stressed word is instantly audible.

This repo does two things:

1. **Benchmarks** four publicly available stress engines on a hand-annotated
   gold corpus, with a metric that separates general accuracy from homograph
   disambiguation.
2. Ships a **meta-accentor**: a rule layer that sits on top of one engine and
   resolves context-dependent homographs the base model gets wrong.

## Results

All numbers below are produced by the scripts in this repo and are reproducible
with `python bench_engines.py` and `python bench_meta.py`.

### Engines compared (`bench_engines.py`)

| Engine | word_acc | homograph_acc | yo_acc |
|---|---|---|---|
| RUAccent turbo3.1 | 0.847 | 0.917 | 0.889 |
| stressonnx/ruaccent | 0.899 | 0.917 | 0.889 |
| stressonnx/silero | 0.750 | 0.583 | 0.778 |
| stressonnx/simple | 0.313 | 0.333 | 0.333 |

- `word_acc` - share of words whose stress mark matches the gold annotation
- `homograph_acc` - accuracy on the pairs where context has to pick the reading
- `yo_acc` - words that contain `ё` in the gold annotation and keep it in the output

### Base vs meta layer (`bench_meta.py`)

| Accentor | word_acc | homograph_acc | yo_acc |
|---|---|---|---|
| stressonnx/ruaccent (base) | 0.890 | 0.917 | 0.889 |
| meta-accentor | 0.924 | **1.000** | **1.000** |

The base engine misses exactly one homograph in the corpus - `Дверной замок
крепкий.` gets stress on the first syllable, reading it as *castle* instead of
*lock*. The meta layer resolves it and reaches 1.000 on both homographs and `ё`.

## How the meta layer works

`meta_accent.py` takes the base engine's output and rewrites stress marks using
three sources of knowledge from `stress_data.json`:

- **overrides** - words with a single correct stress in modern usage, where the
  base model is simply wrong (`договор`, `звонит`, `свёкла`, `щавель`, `торты`,
  `квартал`, `каталог`, `обеспечение`, ...)
- **collocations** - cue phrases scoped to the current clause. `Дверной замок`
  is a lock, `замок на горе` is a castle, so the cue phrase decides the reading
- **defaults** - the reading to fall back on when no cue fires

Two details matter for correctness:

- **Clause scoping.** Context is collected per clause, split on `, . ! ? ; : … —`,
  so a cue in a neighbouring clause does not leak into the decision.
- **Tokenization that respects the marks.** The output is re-tokenized with `+`
  kept attached to the following vowel, and the rewrite is spliced back into the
  original string, so punctuation, quotation marks, digits, latin words and word
  count all survive untouched.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

pytest -q                      # 49 tests
python bench_engines.py        # engine comparison
python bench_meta.py           # base vs meta
python run_meta.py             # meta layer on a dense homograph paragraph
python run_on_book.py          # meta layer over a real book chapter
```

`RUAccent` downloads its dictionaries and ONNX models to `./models_ru` on first
run (~500 MB, git-ignored). `stressonnx` fetches its own models on first use.

## Running real text

`run_on_book.py` applies the meta layer to the first night of Dostoevsky's
*White Nights* (1848, public domain; the text is in `chapter.txt`):

```
chapter: Dostoevsky, "White Nights", Night One
paragraphs: 18, words: 1961
meta corrections (words where meta differs from base): 13
word count preserved: True
double '+' introduced: False
```

That is the stress test the corpus cannot give you: long sentences, dialogue
dashes, quotation marks. The assertions at the end of the script check that the
meta layer changes nothing but the `+` marks.

## Layout

```
corpus.py             gold corpus: 3 groups, 32 annotated sentences
meta_accent.py        the meta-accentor (overrides + collocations + defaults)
stress_data.json      the rules it reads: overrides, collocation cues, defaults
bench_engines.py      scores 4 engines on the corpus
bench_meta.py         scores base vs meta on the same corpus
run_meta.py           base vs meta on a dense homograph paragraph
run_on_book.py        base vs meta over a real chapter, with invariants
test_stress_corpus.py 49 pytest cases: exact word stress + behavioural checks
profile.sb            macOS sandbox profile for running the models
chapter.txt           Dostoevsky, "White Nights", Night One (public domain)
```

The corpus is split by the kind of knowledge required:

- **A** - homographs that need context (замок, мука, белки/белка, атлас, орган,
  плачу, уже, дорога)
- **B** - words Russian speakers commonly stress wrong, plus `ё` handling
- **C** - further contested or context-dependent pairs (хлеба, руки, воды)

Annotations use `+` before the stressed vowel: `Дверной зам+ок крепкий.`

## Limitations

Read these before quoting the numbers:

- The gold corpus is **32 sentences written by hand** for this harness. It is
  sized to measure homograph resolution precisely, not to estimate general
  accuracy on arbitrary Russian text. Treat `word_acc` as indicative.
- The comparison covers four engines that were convenient to run locally (one
  dictionary-driven, three ONNX). It is not a survey of the field.
- The meta layer is **rule-based and hand-curated**, not trained. Its overrides
  do not generalise beyond the vocabulary in `stress_data.json`; outside the
  corpus it is a post-processor, not a better model.
- `profile.sb` is a macOS `sandbox-exec` profile used to run third-party models
  with network access and writes outside the working directory denied. It is
  kept here because that is how the benchmarks were run, not as a security
  guarantee.

## License

MIT - see [LICENSE](LICENSE).
