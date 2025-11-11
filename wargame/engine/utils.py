from __future__ import annotations
from typing import Dict, List, Optional
from ..types import WorldState, Contract


def public_summary(ws: WorldState) -> dict:
    return {
        "turn": ws.turn,
        "defcon": ws.defcon,
        "owner": {k: v.owner for k, v in ws.nodes.items()},
        "mil": {k: v.stationed_mil for k, v in ws.nodes.items()},
        "econ": ws.econ.copy(),
    }


def _format_contract(c: Contract) -> str:
    terms = c.terms
    parts = [f"id={c.id}", f"parties={c.parties}", f"type={terms.type}", f"dur={terms.duration}"]
    if terms.nodes:
        parts.append(f"nodes={terms.nodes}")
    if terms.payments:
        parts.append(f"payments={terms.payments}")
    parts.append(f"status={c.status}")
    parts.append(f"start={c.start_turn}")
    parts.append(f"end={c.end_turn}")
    return " | ".join(parts)


def full_state_str(ws: WorldState) -> str:
    """Return a multi-line debug string showing the full world state.

    Includes turn, DEFCON, node owners and stationed mil, econ for all players,
    and full contract details.
    """
    lines: List[str] = []
    lines.append(f"Turn: {ws.turn}")
    lines.append(f"DEFCON: {ws.defcon}")
    lines.append("Nodes:")
    for nid, node in ws.nodes.items():
        lines.append(f"  {nid}: owner={node.owner or 'Neutral'}, mil={node.stationed_mil}, income={node.income}, neutral_def={node.neutral_defense}")
    lines.append("Econ:")
    for p, v in ws.econ.items():
        lines.append(f"  {p}: {v}")
    lines.append("Contracts:")
    if not ws.contracts:
        lines.append("  (none)")
    else:
        for c in ws.contracts:
            lines.append(f"  { _format_contract(c) }")
    return "\n".join(lines)


def player_view_str(ws: WorldState, player: str, reveal: bool = False) -> str:
    """Return a player-specific view string.

    If reveal=True then same as full_state_str (debug). Otherwise:
    - show node ownership and stationed mil (these are public in MVP)
    - show econ for the requesting player; other players' econ are masked
    - show only contracts that involve the player; others are listed as hidden counts
    """
    if reveal:
        return full_state_str(ws)

    lines: List[str] = []
    lines.append(f"Turn: {ws.turn}")
    lines.append(f"DEFCON: {ws.defcon}")
    lines.append("Nodes (public):")
    for nid, node in ws.nodes.items():
        lines.append(f"  {nid}: owner={node.owner or 'Neutral'}, mil={node.stationed_mil}")
    lines.append("Econ:")
    for p, v in ws.econ.items():
        if p == player:
            lines.append(f"  {p}: {v}")
        else:
            lines.append(f"  {p}: ?")

    # Contracts: show only those involving the player
    player_contracts = [c for c in ws.contracts if player in c.parties]
    other_count = len(ws.contracts) - len(player_contracts)
    lines.append("Contracts:")
    if not ws.contracts:
        lines.append("  (none)")
    else:
        for c in player_contracts:
            lines.append(f"  { _format_contract(c) }")
        if other_count:
            lines.append(f"  ({other_count} other contract(s) hidden)")
    return "\n".join(lines)


def print_turn(ws, actions_by_player):
    print(f"\n=== Turn {ws.turn} START | DEFCON {ws.defcon} ===")
    for pid, acts in actions_by_player.items():
        if not acts:
            continue
        pretty = [a.type + (f"({a.from_node}->{a.to_node},{a.amount})" if a.from_node else (f"({a.node})" if a.node else "")) for a in acts]
        print(f"{pid:9s}: " + ", ".join(pretty))
    # Print a compact scoreboard summary per player
    print(scoreboard_str(ws))
    # Also keep node-level debug for quick inspection
    owners = ", ".join([f"{nid}:{node.owner or 'Neutral'}" for nid, node in ws.nodes.items()])
    mils   = ", ".join([f"{nid}:{node.stationed_mil}" for nid, node in ws.nodes.items()])
    econ   = ", ".join([f"{p}:{v}" for p, v in ws.econ.items()])
    print("Owners:", owners)
    print("Mil   :", mils)
    print("Econ  :", econ)


def scoreboard_str(ws: WorldState) -> str:
    """Return a compact scoreboard string summarizing territories, econ, and total mil per player.

    Example:
      Territories: Astra=2, Borealis=1, Cinder=2
      Econ: Astra=12, Borealis=10, Cinder=12
      Mil (total): Astra=5, Borealis=7, Cinder=6
    """
    # Collect players from econ keys and any node owners, then sort alphabetically
    players_set = set(ws.econ.keys())
    for n in ws.nodes.values():
        if n.owner:
            players_set.add(n.owner)
    players = sorted(players_set)

    # Territories: count owned nodes per player
    terr_counts = {p: 0 for p in players}
    for node in ws.nodes.values():
        if node.owner:
            terr_counts[node.owner] = terr_counts.get(node.owner, 0) + 1

    # Econ: use ws.econ (default 0 if missing)
    econ_vals = {p: ws.econ.get(p, 0) for p in players}

    # Mil: total stationed mills per player across nodes they own
    mil_totals = {p: 0 for p in players}
    for node in ws.nodes.values():
        if node.owner:
            mil_totals[node.owner] = mil_totals.get(node.owner, 0) + node.stationed_mil

    terr_part = ", ".join([f"{p}={terr_counts.get(p,0)}" for p in players])
    econ_part = ", ".join([f"{p}={econ_vals.get(p,0)}" for p in players])
    mil_part  = ", ".join([f"{p}={mil_totals.get(p,0)}" for p in players])

    lines = [f"Territories: {terr_part}", f"Econ: {econ_part}", f"Mil (total): {mil_part}"]
    return "\n".join(lines)
