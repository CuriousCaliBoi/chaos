# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project adheres to Semantic Versioning.

## [Unreleased]

### Added
- `slugify()` utility with unicode normalization, joiners, and hyphen collapse.
- Unit tests for `slugify()` covering spaces, punctuation, accents, and dashes.
- GitHub Actions CI to run unit tests on pushes and pull requests.
- Dataset-backed tests for `slugify()` (`chaos/datasets/slugify_cases.json`).
- Minimal evolver CLI (`python -m chaos.evolver slugify`) that searches rule configs and logs artifacts; optional `--write` to propose `chaos/rules.json`.
 - Strict mode for `slugify()` with `strict=True` (fallback `n-a`, `max_len` truncation).
 - Fuzzer CLI to propose dataset additions (`python -m chaos.fuzz slugify`).
 - Nightly workflow to auto-propose evolved rules via PR (`.github/workflows/evolve.yml`).

## [0.0.1] - 2025-09-24
### Added
- Initial repository scaffolding.
