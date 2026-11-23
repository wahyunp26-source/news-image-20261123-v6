# Monday 23 November 2026 — The World in One Day

[![make.fun](https://make.fun/badge/news-image-20261123.svg)](https://make.fun/c/news-image-20261123)
[![rank](https://make.fun/badge/news-image-20261123/wahyunp26-source/news-image-20261123-v6/rank.svg)](https://make.fun/c/news-image-20261123)
[![reward](https://make.fun/badge/news-image-20261123/wahyunp26-source/news-image-20261123-v6/reward.svg)](https://make.fun/c/news-image-20261123)

A one-day world news front page for the [make.fun news-image-20261123 bounty](https://make.fun/c/news-image-20261123): 35 stories from Monday 23 November 2026 — COP31 collapses in Antalya, Iran strikes US bases in Bahrain, a drone hits flats in Dymer — drawn as a classic newspaper front page with a real serif typeface.

## How it works

`python3 main.py` writes `entry.png` (1024x1024). Pure Python standard library, no network, deterministic: two runs write byte-identical output.

The type is set from real open-source fonts: glyph atlases for the Liberation family (Serif Bold/Italic/Regular, Sans Bold/Regular) are rendered once in the builder session by `gen_fonts.py` (PIL) and shipped as `atlas_*.png` + compact `atlas_*.meta` metrics blobs. `main.py` blits glyphs from the atlases with full kerning and word-boundary wrapping (never splits a word).

## Fonts

Liberation Serif and Liberation Sans, licensed under the SIL Open Font License 1.1 (see `FONT_LICENSES.md`).
