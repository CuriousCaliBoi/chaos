from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import json
import pathlib


@dataclass
class Rules:
    joiners: str = "&'"  # characters removed (not turned to '-') before sanitation


_MODULE_RULES = Rules()


def get_rules() -> Rules:
    return _MODULE_RULES


def load_rules_from_json(path: Optional[pathlib.Path] = None) -> Rules:
    if path is None:
        path = pathlib.Path(__file__).with_name("rules.json")
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return Rules(**data)
    return Rules()


class use_rules:
    def __init__(self, r: Rules):
        self._new = r
        self._old = None

    def __enter__(self):
        global _MODULE_RULES
        self._old = _MODULE_RULES
        _MODULE_RULES = self._new
        return self

    def __exit__(self, exc_type, exc, tb):
        global _MODULE_RULES
        _MODULE_RULES = self._old  # type: ignore
        return False


# Initialize rules from optional JSON override
_MODULE_RULES = load_rules_from_json()

