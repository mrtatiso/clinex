# clinex

Reads `scrap.tecy` from [tecy](https://github.com/mrtatiso/tecy), keeps what is useful and writes `clean.tecy`.

```
$ python3 clinex.py
scrap.tecy: 12,003 pieces → clean.tecy: 6,416 pieces
  letters       33   e a o n i r s t l d c u m h p
  syllables  6,243   de a the la re en in to te ta se e na of ca
  pairs        140   st th ch gh sc nt rs ts rt rd rl nd ng nk ht
sha256 a2593fa55ce78bdea018fdf3b261d44b8131f35eda059bf063db3ab087ad2341
```

No dependencies. `scrap.tecy` is only read, never changed. The same `scrap.tecy` always gives the same `clean.tecy`.

## Run

```
python3 clinex.py                          # scrap.tecy → clean.tecy
python3 clinex.py scrap.tecy clean.tecy    # the same, with the names given
```

It refuses to write over its own source.

## clean.tecy

One piece per line:

```
<piece> TAB <count> TAB <kind>
```

Sorted by kind (`l`, then `s`, then `p`), then the most used first:

| kind | | what it is |
|---|---|---|
| `l` | letter | every useful letter, counted across all of scrap |
| `s` | syllable | the pieces of scrap that pass the filter, as they are |
| `p` | pair | the pieces that do not pass, cut into pairs of letters |

Nothing useful is thrown away: a piece that does not pass is cut, not dropped.

## Published table

This repository includes `clean.tecy`, made by clinex v1.0.0 from the `scrap.tecy` published in [tecy](https://github.com/mrtatiso/tecy). Anyone can check it: the same scrap always gives the same clean.

| file | sha256 |
|---|---|
| `scrap.tecy` (tecy, commit `860f866`) | `204265e682fe006f25969344f02a53ea77ead809b40ecb234929de4fbc4d3ca7` |
| `clean.tecy` | `a2593fa55ce78bdea018fdf3b261d44b8131f35eda059bf063db3ab087ad2341` |

When `scrap.tecy` grows, `clean.tecy` is made again and both hashes here change with it. Tools that read `clean.tecy` should check its sha256.

## What it does

**Letters.** a–z and á é í ó ú ü ñ stay. Other Latin letters become their plain form: ç → c, ö → o, à → a, ß → ss, æ → ae, œ → oe, ø → o, ł → l, þ → th. A letter with no plain form is dropped and splits the piece there.

**Cut with the RAE rules.** Every piece is first cut with the Spanish syllable rules of the RAE, so each syllable has one vowel group. English pieces that tecy left whole are cut the way Spanish would read them: `maria` → `ma·ria`, `were` → `we·re`, `time` → `ti·me`.

**Syllables.** A syllable passes when it has a vowel (y counts), at most 5 letters and at most 2 consonants in a row. It goes to `clean.tecy` as it is, with its count. Pieces that end up the same are added together (garçon and garcon are one).

**Pairs.** A syllable that does not pass is cut from the left into pairs of letters: `straight` → `st·ra·ig·ht`. A pair that passes on its own (`ra`, `ig`) counts as a syllable; the rest (`st`, `ht`) count as pairs. A last single letter only counts as a letter.

| from scrap | goes to clean.tecy |
|---|---|
| de, trans, ción | syllables, as they are |
| casa, maria, valentina | syllables `ca·sa`, `ma·ria`, `va·len·ti·na` |
| garçon, großen | syllables `gar·con`, `gros·sen` |
| straight | pairs `st`, `ht` · syllables `ra`, `ig` |
| schmidt | pairs `sc`, `hm` · syllable `id` · the `t` only as a letter |

## Test

```
python3 -m unittest discover test
```

## Licence

MIT, see `LICENSE`.

## Verify

```
sha256sum clinex.py
```

v1.0.0:

```
c843bbe351a0d0671d8965c60a8c47904e03ad21b60f08a0184fe57be65c627f
```
