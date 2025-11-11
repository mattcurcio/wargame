from __future__ import annotations
from typing import Dict, List
from copy import deepcopy
import random
from ..types import Action, WorldState
from .rules import validate_action
from .actions import (
    apply_build_econ,
    apply_build_mil,
    apply_move,
    resolve_annex,
    resolve_strike,
    resolve_nuclear,
)
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

    # Handle PREP_NUKE research actions during build/mobilization phase
    for acts in clean.values():
        for a in acts:
            if a.type == "PREP_NUKE":
                # increment research progress (counts turns of preparation)
                new_ws.research_progress[a.actor] = new_ws.research_progress.get(a.actor, 0) + 1
                try:
                    new_ws.events.append(f"RESEARCH: {a.actor} progressed nuclear research ({new_ws.research_progress[a.actor]})")
                except Exception:
                    pass

    # 4) COMBAT (ANNEX, STRIKE)
    # First, collect ANNEX and STRIKE actions separately so we can handle
    # simultaneous ANNEX attempts against the same neutral node fairly.
    annex_actions: List[Action] = []
    strike_actions: List[Action] = []
    nuclear_actions: List[Action] = []
    other_actions: List[Action] = []
    # preserve player order by iterating clean.values()
    for acts in clean.values():
        for a in acts:
            if a.type == "ANNEX":
                annex_actions.append(a)
            elif a.type == "STRIKE":
                strike_actions.append(a)
            elif a.type == "NUCLEAR":
                nuclear_actions.append(a)
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
    # First process nuclear actions (they are global and may neutralize nodes)
    # Process in player order so attackers act deterministically
    nuclear_launched = False
    for acts in clean.values():
        for a in acts:
            if a in nuclear_actions:
                resolve_nuclear(new_ws, a)
                nuclear_launched = True

    # Now process STRIKE actions in player order
    for acts in clean.values():
        for a in acts:
            if a in strike_actions:
                resolve_strike(new_ws, a)

    # 5) CONTRACTS
    # Before contracts/income, resolve DEFCON shifts based on actions this turn
    def resolve_defcon(pre: WorldState, post: WorldState, actions: Dict[str, List[Action]]) -> int:
        # Triggers per PRD
        delta = 0
        # If a nuclear launch occurred this turn, skip other DEFCON triggers (nuclear overrides)
        if any(a.type == "NUCLEAR" for acts in actions.values() for a in acts):
            post.events.append("DEFCON: nuclear launch -> maximum tension")
            return

        # STRIKE used -> -1 (once)
        # PREP_NUKE used -> -1 for single user, but if multiple players
        # prepare in the same turn this is highly provocative and should
        # immediately set DEFCON to 2 per updated rules. Handle the multi-
        # player case first and short-circuit other triggers.
        prep_actors = {a.actor for acts in actions.values() for a in acts if a.type == "PREP_NUKE"}
        if len(prep_actors) >= 2:
            post.events.append("DEFCON: multiple players preparing nukes -> immediate heavy escalation to DEFCON 2")
            set_defcon(post, 2)
            # mark the post state so cleanup can avoid drifting DEFCON upward
            try:
                setattr(post, "_provocative_escalation", True)
            except Exception:
                pass
            return 0
        prep_used = len(prep_actors) == 1
        if prep_used:
            delta -= 1
            post.events.append("DEFCON: nuclear preparation detected -> tension rises")

        strike_used = any(a.type == "STRIKE" for acts in actions.values() for a in acts)
        if strike_used:
            delta -= 1
            post.events.append("DEFCON: strike detected -> tension rises")
        # ANNEX against player -> -1
        annex_against_player = any(a.type == "ANNEX" and pre.nodes.get(a.to_node) and pre.nodes[a.to_node].owner is not None and pre.nodes[a.to_node].owner != a.actor for acts in actions.values() for a in acts)
        if annex_against_player:
            delta -= 1
            post.events.append("DEFCON: hostile annex detected -> tension rises")
        # Multiple BUILD_MIL by 2+ players -> -1 (50% deterministic rule: apply on even turns)
        builders = {pid for pid, acts in actions.items() for a in acts if a.type == "BUILD_MIL"}
        if len(builders) >= 2 and (pre.turn % 2 == 0):
            delta -= 1
            post.events.append("DEFCON: arms race detected -> tension rises")
        # Large mil growth >2 at any node -> -1
        large_growth = any((post.nodes[nid].stationed_mil - pre.nodes[nid].stationed_mil) > 2 for nid in post.nodes.keys())
        if large_growth:
            delta -= 1
            post.events.append("DEFCON: rapid militarization detected -> tension rises")
        # Peaceful turn (no STRIKE/ANNEX) -> +1 per peaceful turn
        any_strike_or_annex = any(a.type in ("STRIKE", "ANNEX") for acts in actions.values() for a in acts)
        if not any_strike_or_annex:
            delta += 1
            post.events.append("DEFCON: peaceful turn -> tension eases")
            post.last_turn_peaceful = True
        else:
            post.last_turn_peaceful = False
        # DEESCALATE action -> +1 (limited to DEFCON >=3)
        deescalate_used = any(a.type == "DEESCALATE" for acts in actions.values() for a in acts)
        if deescalate_used and pre.defcon >= 3:
            delta += 1
            post.events.append("DEFCON: diplomatic de-escalation used -> tension eases")

        if post.defcon == 1 and any(a.type == "NUCLEAR" for acts in actions.values() for a in acts):
            # nuclear already handled
            return 0
        # Apply delta (clamped)
        if delta != 0:
            set_defcon(post, post.defcon + delta)
        return delta

    applied_defcon_delta = resolve_defcon(ws, new_ws, clean)

    process_contracts(new_ws)

    # 6) INCOME
    income_phase(new_ws)

    # 7) CLEANUP
    new_ws.turn += 1
    # Simple DEFCON drift toward 3
    # If a nuclear launch occurred this turn, do not drift DEFCON upward in cleanup
    # Also, if we applied a positive defcon delta (de-escalation) skip the cleanup decrement
    if new_ws.defcon > 3:
        if applied_defcon_delta and applied_defcon_delta > 0:
            # skip the automatic decrement when we just de-escalated
            pass
        else:
            set_defcon(new_ws, new_ws.defcon - 1)
    elif new_ws.defcon < 3:
        # suppress upward cleanup drift if a nuclear launch happened this turn
        # or if a multi-player PREP_NUKE provocative escalation was applied
        if not nuclear_launched and not getattr(new_ws, "_provocative_escalation", False):
            set_defcon(new_ws, new_ws.defcon + 1)
    return new_ws
