from __future__ import annotations
from ..types import WorldState, Action


def apply_build_econ(ws: WorldState, act: Action) -> None:
    ws.econ[act.actor] = ws.econ.get(act.actor, 0) + 2


def apply_build_mil(ws: WorldState, act: Action) -> None:
    assert act.node is not None
    ws.econ[act.actor] -= 2
    ws.nodes[act.node].stationed_mil += 2


def apply_move(ws: WorldState, act: Action) -> None:
    assert act.from_node and act.to_node and act.amount
    src = ws.nodes[act.from_node]
    dst = ws.nodes[act.to_node]
    src.stationed_mil -= act.amount
    # Movement into non-owned nodes is disallowed by validation.
    # If we get here, the destination must be owned by the actor and we add the
    # moved units to the destination stack.
    if dst.owner == act.actor:
        dst.stationed_mil += act.amount
    else:
        # Defensive fallback: return moved units to source to avoid loss if
        # validation was bypassed unexpectedly.
        src.stationed_mil += act.amount


def resolve_annex(ws: WorldState, act: Action) -> None:
    assert act.from_node and act.to_node and act.amount
    src = ws.nodes[act.from_node]
    tgt = ws.nodes[act.to_node]
    if tgt.owner is None:
        if act.amount > tgt.neutral_defense:
            src.stationed_mil -= act.amount
            tgt.owner = act.actor
            tgt.neutral_defense = 0
            tgt.stationed_mil = max(1, act.amount - 1)  # leave ≥1 to hold
        else:
            # fail: attacker loses 1
            src.stationed_mil -= 1


def resolve_strike(ws: WorldState, act: Action) -> None:
    assert act.from_node and act.to_node and act.amount
    src = ws.nodes[act.from_node]
    tgt = ws.nodes[act.to_node]
    if tgt.owner is None or tgt.owner == act.actor:
        return
    if act.amount > tgt.stationed_mil:
        src.stationed_mil -= act.amount
        tgt.owner = act.actor
        tgt.neutral_defense = 0
        tgt.stationed_mil = max(1, act.amount - 1)
    else:
        src.stationed_mil -= 1
