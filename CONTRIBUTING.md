## Contributing notes — engine semantics

Quick notes for contributors working on the game engine (important to avoid subtle bugs):

- resolve_turn is non-mutating: it deep-copies the incoming `WorldState`, applies actions to the copy, and returns the new state. Always use the returned state (do not assume the original `WorldState` is modified in place).

- Phase ordering is intentional and important:
  - BUILD
  - MOVES
  - COMBAT (ANNEX/STRIKE)
  - CONTRACTS
  - INCOME
  - CLEANUP (turn++ and defcon drift)

  Because BUILD runs before COMBAT, builds in the same turn as a capture will not affect that turn's combat. If you need builds to affect same-turn combat, consider the implications carefully and add tests that document the new behavior.

- MVP rule simplifications to preserve clarity:
  - Movement is only allowed between nodes you own. No pre-staging on neutral/enemy nodes.
  - Attacks (ANNEX/STRIKE) must originate from a node you own; we do not track per-player stacked units on nodes in the MVP.
  - Action cap: only the first two valid actions per player per turn are applied.

- Tests: run `pytest -q` from the project root (`wargame_mvp/`). When changing engine behavior, update or add tests that assert phase-specific expectations (e.g., capture timing, payments timing, income application).
