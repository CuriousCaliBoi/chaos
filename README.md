# chaos

Small sandbox repo. Now includes a tiny `slugify()` utility with tests.

Running tests
- With Python 3.x installed, run: `python -m unittest discover -s tests -p 'test*.py' -v`

Usage
- Import and use in Python:
  - `from chaos.strings import slugify`
  - `slugify("Café déjà vu")  # -> 'cafe-deja-vu'`

CI
- GitHub Actions runs the unit tests on pushes and PRs (`.github/workflows/ci.yml`).

Evolver (Darwinian Gödel Machine inspired)
- A tiny, data-driven evolver explores rule configurations for `slugify()` and logs results.
- Run a quick search: `python -m chaos.evolver slugify --epochs 200 --seed 0`
- To adopt the candidate rules, rerun with `--write` and review the generated `chaos/rules.json` + tests.
- Dataset for evaluation lives at `chaos/datasets/slugify_cases.json`; extend it to steer behavior.

Automation
- Nightly GitHub Action (`.github/workflows/evolve.yml`) runs the evolver and opens a PR if `chaos/rules.json` changes while tests stay green.

Contributing
- Use test-first patches: add or tighten a failing test, then make it pass.
- Update `CHANGELOG.md` for user-visible changes.
- PRs should follow `.github/pull_request_template.md`.
- Optional (recommended) pre-push tests locally:
  - `git config core.hooksPath .githooks`
  - `git push` will run unit tests first and block on failure.
