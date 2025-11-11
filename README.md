# LLM WarGame — MVP

This repository contains a small Python-based MVP for the LLM WarGame project.

Quick start

1. Create and activate a virtual environment:

```bash
cd /path/to/wargame_mvp
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dev/test deps and optionally install editable:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python -m pip install -e .
```

3. Run tests:

```bash
pytest -q
```

4. Run an interactive match (example):

```bash
python -m wargame.run_match --human Astra --turns 6 --debug
```

Files of interest
- `wargame/` — package source (engine, agents, utils)
- `Grammar.txt` — cheat sheet used by the interactive prompt (also packaged into the package)
- `wargame/run_match.py` — CLI runner for matches
- `wargame/demo_human.py` — scripted demo runner

Contributing
- See `CONTRIBUTING.md` for notes on engine phases and resolver semantics.

License
- The project is licensed under the MIT License (see `LICENSE`).
# Wargame-MVP

Minimal turn-based war/diplomacy sim with a 5-node linear map. Deterministic core, LLM-friendly agents optional.

## Quickstart
```bash
pip install -e .
python -m wargame.run_match
```

## Tests

```bash
pytest -q
```
