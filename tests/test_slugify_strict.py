import unittest

from chaos.strings import slugify


class TestSlugifyStrict(unittest.TestCase):
    def test_strict_non_ascii_fallback(self):
        self.assertEqual(slugify("中文測試", strict=True), "n-a")

    def test_strict_max_len_truncates_cleanly(self):
        s = "hello-world-" * 10  # long, ends with hyphen when truncated
        out = slugify(s, strict=True, max_len=32)
        self.assertLessEqual(len(out), 32)
        self.assertFalse(out.startswith("-") or out.endswith("-"))
        # Still a valid slug
        self.assertEqual(slugify(out, strict=True, max_len=32), out)

    def test_strict_short_max_len(self):
        self.assertEqual(slugify("hello world", strict=True, max_len=5), "hello")

    def test_strict_idempotent(self):
        x = slugify("Café déjà vu", strict=True)
        self.assertEqual(slugify(x, strict=True), x)


if __name__ == "__main__":
    unittest.main()

