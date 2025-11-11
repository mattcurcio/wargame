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


def resolve_nuclear(ws: WorldState, act: Action) -> None:
    """Apply a nuclear strike to the target node.

    Effects (MVP):
    - Deduct launch cost from attacker (5 econ)
    - Target node becomes neutral (owner=None) and stationed_mil=0
    - Escalate DEFCON to 1
    - Note: contracts and other global effects are not modeled here yet.
    """
    if act.to_node is None:
        return
    attacker = act.actor
    # Charge econ cost (validation ensures sufficient funds)
    # PRD requires econ >= 10 and we charge 10 on launch
    ws.econ[attacker] = ws.econ.get(attacker, 0) - 10

    # Log the nuclear event for UI/debugging
    try:
        ws.events.append(f"NUCLEAR: {attacker} launched a nuclear strike on {act.to_node}")
    except Exception:
        # best-effort logging; don't raise from logging
        pass

    tgt = ws.nodes.get(act.to_node)
    if tgt is None:
        return
    # Wipe out stationed forces and ownership
    # Also apply adjacent fallout damage of 1-2 units
    try:
        import random

        adj_damage = lambda: random.randint(1, 2)
    except Exception:
        adj_damage = lambda: 1

    prev_owner = tgt.owner
    tgt.stationed_mil = 0
    tgt.owner = None
    # increase neutral defense as fallout (small arbitrary value)
    tgt.neutral_defense = max(tgt.neutral_defense, 2)
    # adjacent nodes: reduce stationed_mil by 1-2
    from .state import LINEAR_EDGES

    for adj in LINEAR_EDGES.get(act.to_node, []):
        node = ws.nodes.get(adj)
        if node:
            dmg = adj_damage()
            node.stationed_mil = max(0, node.stationed_mil - dmg)
    # Set DEFCON to maximum tension
    from .state import set_defcon

    set_defcon(ws, 1)
    # Halve target owner's econ
    if prev_owner:
        ws.econ[prev_owner] = ws.econ.get(prev_owner, 0) // 2
    # Reduce all players' next-turn income by 10%
    for p in list(ws.next_income_multiplier.keys()):
        ws.next_income_multiplier[p] = ws.next_income_multiplier.get(p, 1.0) * 0.9
    # Aggressor sanctions (2 turns): cannot BUILD_ECON or DEESCALATE
    ws.sanctions[attacker] = max(ws.sanctions.get(attacker, 0), 2)
