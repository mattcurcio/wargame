from __future__ import annotations
from typing import Dict, List
from copy import deepcopy
import random
from ..types import Action, WorldState
from .rules import validate_action
from .actions import apply_build_econ, apply_build_mil, apply_move, resolve_annex, resolve_strike
from .contracts import process_contracts
from .state import set_defcon, income_phase

# Reproducible RNG for tie-breaking in simultaneous annex contests
_ANNEX_RNG = random.Random(0)

PHASE_ORDER = (
    "VALIDATE",
    "BUILD",
    "MOVES",
    "COMBAT",
    "CONTRACTS",
    "INCOME",
    "CLEANUP",
)


def resolve_turn(ws: WorldState, actions_by_player: Dict[str, List[Action]]) -> WorldState:
    # Work on a deep copy and return the new state (resolver is non-mutating)
    new_ws = deepcopy(ws)

    # 1) VALIDATE & truncate to action limit
    clean: Dict[str, List[Action]] = {}
    for pid, acts in actions_by_player.items():
        legal: List[Action] = []
        for a in acts[:2]:  # MVP action cap
            ok, _ = validate_action(new_ws, a)
            if ok:
                legal.append(a)
        clean[pid] = legal

    # 2) BUILD
    for acts in clean.values():
        for a in acts:
            if a.type == "BUILD_ECON":
                apply_build_econ(new_ws, a)
            elif a.type == "BUILD_MIL":
                apply_build_mil(new_ws, a)

    # 3) MOVES
    for acts in clean.values():
        for a in acts:
            if a.type == "MOVE":
                apply_move(new_ws, a)

    # 4) COMBAT (ANNEX, STRIKE)
    # First, collect ANNEX and STRIKE actions separately so we can handle
    # simultaneous ANNEX attempts against the same neutral node fairly.
    annex_actions: List[Action] = []
    strike_actions: List[Action] = []
    other_actions: List[Action] = []
    # preserve player order by iterating clean.values()
    for acts in clean.values():
        for a in acts:
            if a.type == "ANNEX":
                annex_actions.append(a)
            elif a.type == "STRIKE":
                strike_actions.append(a)
            else:
                other_actions.append(a)

    # Process simultaneous ANNEX on neutral targets: group by target node
    # Use the world state as of the start of combat (after moves)
    annex_by_target: Dict[str, List[Action]] = {}
    for a in annex_actions:
        annex_by_target.setdefault(a.to_node, []).append(a)

    # For each target, if it was neutral at combat start, resolve contest
    for target, actions_at_target in annex_by_target.items():
        node = new_ws.nodes.get(target)
        if node is None:
            # invalid target (shouldn't happen due to validation); skip
            continue
        if node.owner is None and len(actions_at_target) > 1:
            # contest among multiple attackers
            # find max amount
            max_amt = max((a.amount or 0) for a in actions_at_target)
            top_attackers = [a for a in actions_at_target if (a.amount or 0) == max_amt]
            # choose winner (random tie-break if needed)
            if len(top_attackers) > 1:
                winner = _ANNEX_RNG.choice(top_attackers)
            else:
                winner = top_attackers[0]
            # losers lose 1 unit (if available)
            losers = [a for a in actions_at_target if a is not winner]
            for a in losers:
                src = new_ws.nodes.get(a.from_node)
                if src and src.stationed_mil > 0:
                    src.stationed_mil -= 1

            # Logging: print contest summary
            try:
                winner_amt = winner.amount or 0
                beaten_summary = ", ".join([f"{a.actor}({a.amount or 0})" for a in losers])
                losers_loss_parts = ", ".join([f"{a.actor} loses 1 at {a.from_node or 'unknown'}" for a in losers])
                print(f"Contest for {target}: {winner.actor}({winner_amt}) beats {beaten_summary}; {losers_loss_parts}.")
            except Exception:
                # Best-effort logging; don't fail the resolver on logging errors
                pass
            # apply annex for winner
            resolve_annex(new_ws, winner)
            # mark these actions as handled by removing them from annex_actions
            for a in actions_at_target:
                if a in annex_actions:
                    annex_actions.remove(a)

    # Any remaining annex_actions (targets that were not neutral or single attackers)
    # process in player order (preserve original ordering by scanning clean again)
    remaining_annex = annex_actions[:]  # copy
    for acts in clean.values():
        for a in acts:
            if a in remaining_annex:
                resolve_annex(new_ws, a)

    # Now process STRIKE actions in player order
    for acts in clean.values():
        for a in acts:
            if a in strike_actions:
                resolve_strike(new_ws, a)

    # 5) CONTRACTS
    process_contracts(new_ws)

    # 6) INCOME
    income_phase(new_ws)

    # 7) CLEANUP
    new_ws.turn += 1
    # Simple DEFCON drift toward 3
    if new_ws.defcon > 3:
        set_defcon(new_ws, new_ws.defcon - 1)
    elif new_ws.defcon < 3:
        set_defcon(new_ws, new_ws.defcon + 1)
    return new_ws
