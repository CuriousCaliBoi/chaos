import json
import pathlib
import unittest

from chaos.strings import slugify


DATASET = pathlib.Path(__file__).parents[1] / "chaos" / "datasets" / "slugify_cases.json"


class TestSlugifyDataset(unittest.TestCase):
    def test_dataset_examples(self):
        with DATASET.open("r", encoding="utf-8") as f:
            cases = json.load(f)
        for s, expected in cases.items():
            with self.subTest(case=s):
                self.assertEqual(slugify(s), expected)


if __name__ == "__main__":
    unittest.main()

