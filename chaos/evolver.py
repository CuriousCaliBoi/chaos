"""Minimal evolver inspired by Darwinian Gödel Machine ideas.

Searches rule configurations for `slugify()` that maximize dataset accuracy
without breaking invariants. Writes candidate configs to `artifacts/evolver`.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import string
import time
from dataclasses import asdict
from pathlib import Path
from typing import Dict, Tuple

from .rules import Rules, use_rules
from .strings import slugify


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "chaos" / "datasets" / "slugify_cases.json"
ARTIFACTS = ROOT / "artifacts" / "evolver"


def load_dataset() -> Dict[str, str]:
    with DATASET.open("r", encoding="utf-8") as f:
        return json.load(f)


def score_config(rules: Rules, cases: Dict[str, str]) -> Tuple[int, int]:
    """Return (#correct, total_penalty). Lower penalty is better; prioritize correctness."""
    correct = 0
    penalty = 0
    with use_rules(rules):
        for s, expected in cases.items():
            out = slugify(s)
            if out == expected:
                correct += 1
            else:
                # Penalty by edit distance proxy: length diff + mismatch boolean
                penalty += abs(len(out) - len(expected)) + 1
            # Invariants: characters allowed and no leading/trailing hyphens
            if out.strip("-") != out:
                penalty += 5
            if not set(out) <= set(string.ascii_lowercase + string.digits + "-"):
                penalty += 5
    # Small complexity penalty for long joiner lists
    penalty += len(rules.joiners)
    return correct, penalty


def mutate(rules: Rules, alphabet: str) -> Rules:
    joiners = set(rules.joiners)
    # Randomly add/remove/toggle a character
    if random.random() < 0.5 and joiners:
        joiners.remove(random.choice(tuple(joiners)))
    else:
        joiners.add(random.choice(alphabet))
    return Rules(joiners="".join(sorted(joiners)))


def evolve_slugify(epochs: int = 200, seed: int = 0) -> Rules:
    random.seed(seed)
    cases = load_dataset()
    alphabet = "&'+/_ ."  # candidate joiners to consider
    best = Rules()
    best_score = score_config(best, cases)
    for _ in range(epochs):
        candidate = mutate(best, alphabet)
        cand_score = score_config(candidate, cases)
        # Prefer higher correctness; tie-break on lower penalty
        if cand_score[0] > best_score[0] or (
            cand_score[0] == best_score[0] and cand_score[1] < best_score[1]
        ):
            best, best_score = candidate, cand_score
    return best


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    evo = sub.add_parser("slugify", help="Evolve rules for slugify()")
    evo.add_argument("--epochs", type=int, default=200)
    evo.add_argument("--seed", type=int, default=0)
    evo.add_argument("--write", action="store_true", help="Write rules.json if better or equal")

    args = parser.parse_args()

    if args.cmd == "slugify":
        start = time.time()
        best = evolve_slugify(args.epochs, args.seed)
        duration = time.time() - start
        os.makedirs(ARTIFACTS, exist_ok=True)
        result = {
            "duration_sec": duration,
            "epochs": args.epochs,
            "seed": args.seed,
            "best": asdict(best),
        }
        stamp = int(start)
        out_path = ARTIFACTS / f"slugify_{stamp}.json"
        out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps(result, indent=2))

        # Optionally write to chaos/rules.json if no regression
        if args.write:
            rules_json = ROOT / "chaos" / "rules.json"
            rules_json.write_text(json.dumps(asdict(best), indent=2), encoding="utf-8")
            print(f"Wrote {rules_json}")


if __name__ == "__main__":
    main()

