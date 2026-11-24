#!/usr/bin/env python3
"""clinex: read scrap.tecy, keep what is useful, write clean.tecy.

    $ clinex                         scrap.tecy → clean.tecy
    $ clinex scrap.tecy clean.tecy   the same, with the names given

scrap.tecy is only read, never changed. clean.tecy has three kinds of pieces:

    l   letter: every useful letter, counted in all of scrap
    s   syllable: the pieces of scrap that pass the filter, as they are
    p   pair: the pieces that do not pass, cut into pairs of letters

One line per piece, kind first, then the most used:

    <piece> TAB <count> TAB <kind>

Letters: a-z and á é í ó ú ü ñ stay. Other Latin letters become their plain
form (ç → c, ö → o, à → a, ß → ss, æ → ae, œ → oe, ø → o, ł → l, þ → th…).
A letter with no plain form is dropped and splits the piece there.

Every piece is first cut with the Spanish syllable rules of the RAE (see
_syllables below), so each syllable has one vowel group: maria → ma·ria,
were → we·re.

A syllable passes when it has a vowel (y counts), at most 5 letters and at
most 2 consonants in a row. A syllable that does not pass is cut from the left
into pairs (straight → st·ra·ig·ht); a last single letter only counts as a
letter. A pair that is itself a passing syllable counts as a syllable.

The same scrap.tecy always gives the same clean.tecy.
"""
import hashlib
import os
import sys
import unicodedata

__version__ = "1.0.0"
__all__ = ["letters", "passes", "clean", "load", "save"]

SRC, DST = "scrap.tecy", "clean.tecy"
MAX_LEN = 5
MAX_CONSONANTS = 2
KEEP = set("abcdefghijklmnopqrstuvwxyzáéíóúüñ")
VOWELS = set("aeiouyáéíóúü")
SPECIAL = {"æ": "ae", "œ": "oe", "ø": "o", "ß": "ss", "ł": "l", "đ": "d",
           "ð": "d", "þ": "th", "ı": "i", "ħ": "h", "ŧ": "t"}
KINDS = ("l", "s", "p")              # letter, syllable, pair


# ---------- Spanish syllables: rules of the RAE ----------
#
# Vowels: a e o are strong, i u ü weak. An accented í or ú counts as strong
# (dí·a, ba·úl). Two vowels stay together unless both are strong (le·ón).
# An h between two vowels does not break a diphthong (prohi·bir).
# ch, ll, rr are one consonant; so are qu, and gu before e or i.
# y is a vowel at the end of a word after a vowel (rey, muy) and as the word "y".
# Between two vowel groups: one consonant goes to the next syllable; with more,
# the last one goes, or the last two if they are p b t d c g f k + l or r, or tl.

_CLUSTERS = {a + b for a in "pbtdcgfk" for b in "lr"} - {"dl"} | {"tl"}


def _base(c: str) -> str:
    return unicodedata.normalize("NFD", c)[0]


def _units(w: str) -> list:
    units, i, n = [], 0, len(w)
    while i < n:
        two = w[i:i + 2]
        if two in ("ch", "ll", "rr", "qu") or (two == "gu" and i + 2 < n and _base(w[i + 2]) in "ei"):
            units.append((two, "C"))
            i += 2
            continue
        c, b = w[i], _base(w[i])
        if c == "y":
            vowel = n == 1 or (i == n - 1 and units and units[-1][1] != "C")
            units.append((c, "W" if vowel else "C"))
        elif b in "aeo":
            units.append((c, "S"))
        elif b in "iu":
            units.append((c, "S" if c in "íúìù" else "W"))
        else:
            units.append((c, "C"))
        i += 1
    return units


def _syllables(w: str) -> list:
    u = _units(w)
    vowel = lambda k: k in "SW"
    together = lambda a, b: not (a == "S" and b == "S")
    nuclei, i = [], 0
    while i < len(u):
        if not vowel(u[i][1]):
            i += 1
            continue
        j = i
        while True:
            if j + 1 < len(u) and vowel(u[j + 1][1]) and together(u[j][1], u[j + 1][1]):
                j += 1
            elif (j + 2 < len(u) and u[j + 1][0] == "h" and vowel(u[j + 2][1])
                  and together(u[j][1], u[j + 2][1])):
                j += 2
            else:
                break
        nuclei.append((i, j))
        i = j + 1
    cuts = []
    for (_, a), (b, _) in zip(nuclei, nuclei[1:]):
        between = [t for t, _ in u[a + 1:b]]
        if len(between) >= 2 and between[-2][-1] + between[-1][0] in _CLUSTERS:
            cuts.append(b - 2)
        elif between:
            cuts.append(b - 1)
        else:
            cuts.append(b)
    edges = [0] + cuts + [len(u)]
    return ["".join(t for t, _ in u[x:y]) for x, y in zip(edges, edges[1:])]


def letters(piece: str) -> list:
    """The piece written only with useful letters, split where a letter had to go."""
    out = []
    for c in piece.lower():
        if c in KEEP:
            out.append(c)
        elif c in SPECIAL:
            out.append(SPECIAL[c])
        else:
            plain = "".join(x for x in unicodedata.normalize("NFD", c) if not unicodedata.combining(x))
            out.append(plain if plain and all(x in KEEP for x in plain) else " ")
    return "".join(out).split()


def passes(s: str) -> bool:
    """A usable syllable: a vowel, at most MAX_LEN letters, at most MAX_CONSONANTS in a row."""
    if not s or len(s) > MAX_LEN or not any(c in VOWELS for c in s):
        return False
    run = 0
    for c in s:
        run = 0 if c in VOWELS else run + 1
        if run > MAX_CONSONANTS:
            return False
    return True


def clean(rows) -> dict:
    """{(piece, kind): count} from the rows of scrap.tecy."""
    out = {}

    def add(piece, kind, n):
        out[(piece, kind)] = out.get((piece, kind), 0) + n

    for entry, n in rows:
        for w in letters(entry):
            for c in w:
                add(c, "l", n)
            for syl in _syllables(w):
                if passes(syl):
                    add(syl, "s", n)
                    continue
                for i in range(0, len(syl) - 1, 2):
                    p = syl[i:i + 2]
                    add(p, "s" if passes(p) else "p", n)
    return out


def load(path: str) -> list:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if line:
                piece, n = line.split("\t")[:2]
                rows.append((piece, int(n)))
    return rows


def save(table: dict, path: str) -> None:
    order = {k: i for i, k in enumerate(KINDS)}
    rows = sorted(table.items(), key=lambda x: (order[x[0][1]], -x[1], x[0][0]))
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("".join(f"{p}\t{n}\t{k}\n" for (p, k), n in rows))
    os.replace(tmp, path)


def main(args=None) -> int:
    args = sys.argv[1:] if args is None else args
    if len(args) > 2 or (args and args[0] in ("-h", "--help")):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    src = args[0] if args else SRC
    dst = args[1] if len(args) > 1 else DST
    if os.path.abspath(src) == os.path.abspath(dst):
        print("clinex: the destination must differ from the source", file=sys.stderr)
        return 2
    try:
        rows = load(src)
    except (OSError, ValueError) as e:
        print(f"clinex: {e}", file=sys.stderr)
        return 2
    table = clean(rows)
    save(table, dst)
    with open(dst, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    print(f"{src}: {len(rows):,} pieces → {dst}: {len(table):,} pieces")
    for kind, name in zip(KINDS, ("letters", "syllables", "pairs")):
        top = sorted(((p, n) for (p, k), n in table.items() if k == kind), key=lambda x: (-x[1], x[0]))
        print(f"  {name:<10}{len(top):>6,}   {' '.join(p for p, _ in top[:15])}")
    print(f"sha256 {digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
