import random
import string
import unittest

from chaos.strings import slugify


class TestSlugifyInvariants(unittest.TestCase):
    def test_invariants_on_random_data(self):
        rnd = random.Random(1234)
        unicode_extras = "éäöüß—–中文測試"
        alphabet = string.ascii_letters + string.digits + string.punctuation + string.whitespace + unicode_extras
        for _ in range(100):
            s = "".join(rnd.choice(alphabet) for _ in range(rnd.randint(0, 50)))
            out = slugify(s)
            # Allowed chars
            self.assertTrue(set(out) <= set(string.ascii_lowercase + string.digits + "-"))
            # No leading/trailing hyphens
            self.assertEqual(out.strip("-"), out)
            # No consecutive hyphens
            self.assertNotIn("--", out)
            # Idempotency
            self.assertEqual(slugify(out), out)


if __name__ == "__main__":
    unittest.main()

