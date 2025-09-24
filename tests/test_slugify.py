import unittest

from chaos.strings import slugify


class TestSlugify(unittest.TestCase):
    def test_basic_letters_and_spaces(self):
        self.assertEqual(slugify("Hello World"), "hello-world")

    def test_multiple_spaces_collapse(self):
        self.assertEqual(slugify("  multiple   spaces  "), "multiple-spaces")

    def test_underscores_and_punctuation(self):
        self.assertEqual(slugify("__a__b__"), "a-b")
        self.assertEqual(slugify("S&P 500"), "sp-500")

    def test_accents_are_stripped(self):
        self.assertEqual(slugify("Café déjà vu"), "cafe-deja-vu")
        self.assertEqual(slugify("naïve façade"), "naive-facade")

    def test_unicode_dashes_normalized(self):
        self.assertEqual(slugify("A—B – C"), "a-b-c")  # em/en dashes become hyphens

    def test_existing_hyphens_preserved_and_trimmed(self):
        self.assertEqual(slugify("--already-slug--"), "already-slug")


if __name__ == "__main__":
    unittest.main()

