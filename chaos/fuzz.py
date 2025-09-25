"""Lightweight fuzzer to propose new dataset entries for slugify().

Generates random strings, computes current `slugify()` outputs, and suggests
interesting cases. Optionally appends top-N cases to the dataset file.
"""
from __future__ import annotations

import argparse
import json
import random
import string
from pathlib import Path
from typing import Dict, List, Tuple

from .strings import slugify


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "chaos" / "datasets" / "slugify_cases.json"


def load_dataset() -> Dict[str, str]:
    with DATASET.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_dataset(data: Dict[str, str]) -> None:
    DATASET.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def interest_score(s: str, out: str) -> int:
    score = 0
    if not out:
        score += 10
    if any(ch in s for ch in "&'_—–中文測試%$#@!\t\n"):
        score += 5
    if len(s) > 32:
        score += 3
    if s != s.strip():
        score += 2
    if "--" in out:
        score += 5
    return score


def propose(count: int, seed: int) -> List[Tuple[str, str, int]]:
    rnd = random.Random(seed)
    # Include some unicode and punctuation
    unicode_extras = "éäöüß—–中文測試“”‘’•·×÷±≈∞"
    alphabet = string.ascii_letters + string.digits + string.punctuation + string.whitespace + unicode_extras
    seen = set()
    props: List[Tuple[str, str, int]] = []
    for _ in range(count):
        s = "".join(rnd.choice(alphabet) for _ in range(rnd.randint(0, 80)))
        if s in seen:
            continue
        seen.add(s)
        out = slugify(s)
        score = interest_score(s, out)
        props.append((s, out, score))
    props.sort(key=lambda x: x[2], reverse=True)
    return props


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("slugify", nargs="?", help="Target subject (only 'slugify' supported)")
    ap.add_argument("--count", type=int, default=200)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--append", type=int, default=0, help="Append top-N suggested cases to dataset")
    args = ap.parse_args()

    if args.slugify and args.slugify != "slugify":
        ap.error("Only 'slugify' is supported")

    ds = load_dataset()
    proposals = propose(args.count, args.seed)

    print("Top suggestions (input => output | score):")
    for s, out, sc in proposals[:10]:
        print(f"- {repr(s)} => {out} | {sc}")

    if args.append > 0:
        added = 0
        for s, out, sc in proposals:
            if s in ds:
                continue
            ds[s] = out
            added += 1
            if added >= args.append:
                break
        if added:
            save_dataset(ds)
            print(f"Appended {added} new cases to {DATASET}")
        else:
            print("No new cases appended")


if __name__ == "__main__":
    main()

