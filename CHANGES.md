# Changelog — recent changes

Date: 2025-11-11

Summary of notable updates:

- Add NUCLEAR action (new action type):
  - Cost: 5 econ. Allowed only at DEFCON 1 or 2.
  - Effects: neutralizes target node (owner=None, stationed_mil=0) and escalates DEFCON to 1.
  - Engine logs NUCLEAR launches into `WorldState.events`.

- Event logging & UI:
  - Added `events: List[str]` to `WorldState` for per-turn notable events.
  - Interactive runner (`run_match.py`) prints events after each turn and highlights nuclear events with a red banner.

- DEFCON behavior:
  - If a nuclear launch occurs during the combat phase, the cleanup-phase upward DEFCON drift is suppressed so the escalated DEFCON remains for the remainder of the turn.

- Tests:
  - Added unit tests for NUCLEAR behavior and simultaneous launches; all tests pass.

- Docs:
  - Added `CHEATSHEET.md` (Markdown) with NUCLEAR and DEFCON guidance and examples. Also updated packaged `wargame/Grammar.txt` and README to reference it.

Notes / next steps:
- Consider structured event objects instead of free-form strings for easier UI integration.
- Expand event types (annex contests, contract events) and UI notifications.
