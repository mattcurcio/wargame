# Wargame MVP — Player Cheat Sheet

Commands (one per line). You may enter up to two actions per turn.

## Core commands

- BUILD_ECON
  - Build national economy (no args). Grants +2 econ when applied.

- BUILD_MIL <NODE>
  - Train/build two military units at a node you own. Costs 2 econ.

- MOVE <FROM> <TO> <AMOUNT>
  - Move AMOUNT units from node FROM to adjacent node TO.
  - MOVE is only allowed between nodes you own. Nodes must be adjacent.
  - AMOUNT must be a positive integer and cannot exceed stationed units at FROM.

- ANNEX <FROM> <TO> <AMOUNT>
  - Attempt to annex a neutral node TO from your owned node FROM using AMOUNT units.
  - To succeed you generally need AMOUNT > neutral_defense (and larger AMOUNT wins in contests).
  - If multiple players ANNEX the same neutral node in the same turn, highest AMOUNT wins; ties are broken reproducibly by RNG and losers each lose 1 unit.

- STRIKE <FROM> <TO> <AMOUNT>
  - Attack an enemy-owned node TO from your owned node FROM using AMOUNT units.
  - If AMOUNT > defender stationed_mil you take the node (attacker leaves >=1 unit); otherwise attacker loses 1 unit.

- NUCLEAR <TARGET_NODE>
  - Launch a nuclear strike against TARGET_NODE. No FROM node is required.
  - Cost: 5 econ. Must have econ >= 5 to launch (validation will reject otherwise).
  - Allowed only at DEFCON 1 or 2 (high tension). Launching sets DEFCON to 1 immediately and neutralizes the target node (owner=None, stationed_mil=0).
  - Nuclear launch events are shown in the post-turn event log and are highlighted in the interactive runner.

- PREP_NUKE
  - Begin/continue multi-turn nuclear research/preparation. No arguments.
  - PREP_NUKE is allowed at any DEFCON level. However, it is a provocative action: whenever any player issues PREP_NUKE during a turn, DEFCON is lowered by 1 (tension rises).
  - Use PREP_NUKE when you intend to unlock a future NUCLEAR launch, but be aware it signals escalation.

## Aliases

- BUILD  -> BUILD_ECON
- MIL    -> BUILD_MIL
- TAKE   -> ANNEX
- ATTACK -> STRIKE

## HELP

- Print this cheat sheet and show a few legal example commands for your current state.

## NONE or blank

- Skip this action slot.

## Examples

```
BUILD_ECON
BUILD_MIL A
MOVE A B 1
ANNEX A B 3
STRIKE A C 2
NUCLEAR C
```

## DEFCON quick guide (1..5)

- DEFCON 5: Peacetime. Conventional actions are allowed (ANNEX/STRIKE/MOVE/BUILD). Nuclear launches are disallowed.
- DEFCON 4: Elevated tensions.
- DEFCON 3: Normal/standard operations.
- DEFCON 2: High tension — NUCLEAR allowed (if you can pay the cost).
- DEFCON 1: Maximum tension — NUCLEAR allowed. A nuclear launch sets DEFCON to 1; the engine suppresses upward DEFCON drift for that turn so the high tension persists during the cleanup.

## When to use actions (practical notes)

- BUILD_ECON: safe, always useful to increase future options.
- BUILD_MIL: spend econ to increase stationed forces; must be done at a node you own.
- MOVE: reposition forces between owned nodes; useful to prepare ANNEX or STRIKE next turn.
- ANNEX: use to take neutral nodes. Bring more units than neutral_defense and be careful if multiple players contest the same node.
- STRIKE: use to take enemy nodes — if you fail you still pay a small loss (attacker -1).
- NUCLEAR: last-resort, high-impact. Use only when you can afford the cost and you accept global escalation consequences.
 - PREP_NUKE: provocative research; reduces DEFCON by 1 when used and advances your nuclear research progress by 1 turn.

## Supported commands (max 2 per turn)

- BUILD_ECON
- BUILD_MIL <node>
- ANNEX <from> <to> <amount>
- STRIKE <from> <to> <amount>
- MOVE <from> <to> <amount> (owned→owned only)
- NUCLEAR <target_node> (only at DEFCON 1 or 2 and econ>=5)
 - NUCLEAR <target_node> (only at DEFCON 1 or 2 and econ>=5)
 - PREP_NUKE (no args; allowed at any DEFCON)
- HELP (show cheat sheet + legal examples)
- NONE or blank (skip)

## Grammar (EBNF-ish)

```
command      := build_econ | build_mil | annex | strike | move | nuclear | help | none
build_econ   := "BUILD_ECON" | "BUILD"
build_mil    := ("BUILD_MIL" | "MIL") node
annex        := ("ANNEX" | "TAKE") from node to node amount
strike       := ("STRIKE" | "ATTACK") from node to node amount
move         := "MOVE" from node to node amount
nuclear      := ("NUCLEAR" | "NUC") node
prep_nuke    := ("PREP_NUKE" | "PREP")
help         := "HELP"
none         := "NONE" | ""   (blank)
node         := "A" | "B" | "C" | "D" | "E"
amount       := integer > 0
```
