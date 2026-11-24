import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import clinex  # noqa: E402


class TestLetters(unittest.TestCase):
    def test_plain_forms(self):
        self.assertEqual(clinex.letters("garçon"), ["garcon"])
        self.assertEqual(clinex.letters("großen"), ["grossen"])
        self.assertEqual(clinex.letters("kœnig"), ["koenig"])
        self.assertEqual(clinex.letters("ñandú"), ["ñandú"])
        self.assertEqual(clinex.letters("mü"), ["mü"])

    def test_letter_with_no_plain_form_splits(self):
        self.assertEqual(clinex.letters("abʃde"), ["ab", "de"])


class TestPasses(unittest.TestCase):
    def test_passes(self):
        for s in ("de", "a", "tren", "trans", "ción", "rey", "muy"):
            self.assertTrue(clinex.passes(s), s)

    def test_does_not_pass(self):
        for s in ("str", "straight", "bcd", "schmi", "abcdef", ""):
            self.assertFalse(clinex.passes(s), s)


class TestClean(unittest.TestCase):
    def test_kinds(self):
        t = clinex.clean([("casa", 3), ("straight", 2)])
        self.assertEqual(t[("ca", "s")], 3)                # cut with the RAE rules first
        self.assertEqual(t[("sa", "s")], 3)
        self.assertNotIn(("casa", "s"), t)
        self.assertEqual(t[("st", "p")], 2)
        self.assertEqual(t[("ra", "s")], 2)       # a pair that passes is a syllable
        self.assertEqual(t[("ig", "s")], 2)
        self.assertEqual(t[("ht", "p")], 2)
        self.assertEqual(t[("a", "l")], 3 * 2 + 2)  # every letter of scrap, counted

    def test_every_syllable_has_one_vowel_group(self):
        t = clinex.clean([("maria", 1), ("were", 1), ("valentina", 1)])
        syl = {p for p, k in t if k == "s"}
        self.assertEqual(syl, {"ma", "ria", "we", "re", "va", "len", "ti", "na"})

    def test_odd_letter_only_counts_as_letter(self):
        t = clinex.clean([("schmidt", 1)])
        self.assertEqual({p for p, k in t if k != "l"}, {"sc", "hm", "id"})
        self.assertIn(("t", "l"), t)

    def test_same_scrap_same_clean(self):
        rows = [("de", 9), ("straight", 2), ("garçon", 1)]
        with tempfile.TemporaryDirectory() as d:
            a, b = os.path.join(d, "a"), os.path.join(d, "b")
            clinex.save(clinex.clean(rows), a)
            clinex.save(clinex.clean(list(reversed(rows))), b)
            with open(a, "rb") as fa, open(b, "rb") as fb:
                self.assertEqual(fa.read(), fb.read())


class TestFiles(unittest.TestCase):
    def test_scrap_is_never_changed(self):
        with tempfile.TemporaryDirectory() as d:
            src, dst = os.path.join(d, "scrap.tecy"), os.path.join(d, "clean.tecy")
            with open(src, "w", encoding="utf-8") as f:
                f.write("de\t9\nstraight\t2\n")
            before = open(src, "rb").read()
            self.assertEqual(clinex.main([src, dst]), 0)
            self.assertEqual(open(src, "rb").read(), before)
            for line in open(dst, encoding="utf-8"):
                p, n, k = line.rstrip("\n").split("\t")
                self.assertIn(k, clinex.KINDS)
                self.assertTrue(n.isdigit())

    def test_refuses_same_file(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "x.tecy")
            open(p, "w").write("de\t1\n")
            self.assertEqual(clinex.main([p, p]), 2)


if __name__ == "__main__":
    unittest.main()
