from __future__ import annotations
from ..types import Action, WorldState, NodeID
from .state import LINEAR_EDGES

def is_adjacent(a: NodeID, b: NodeID) -> bool:
    return b in LINEAR_EDGES.get(a, [])

def validate_action(ws: WorldState, act: Action) -> tuple[bool, str]:
    # Basic legality checks (MVP)
    if act.type == "MOVE":
        if act.from_node is None or act.to_node is None or act.amount is None:
            return False, "MOVE missing fields"
        if not is_adjacent(act.from_node, act.to_node):
            return False, "MOVE non-adjacent"
        node = ws.nodes[act.from_node]
        dst = ws.nodes[act.to_node]
        # MVP simplification: movement is only allowed between nodes you own.
        if node.owner != act.actor:
            return False, "MOVE from non-owned node"
        if dst.owner != act.actor:
            return False, "MOVE into non-owned node"
        if node.stationed_mil < act.amount or act.amount <= 0:
            return False, "MOVE invalid amount"
        return True, ""
    if act.type == "BUILD_ECON":
        return True, ""
    if act.type == "BUILD_MIL":
        if act.node is None:
            return False, "BUILD_MIL missing node"
        if ws.nodes[act.node].owner != act.actor:
            return False, "BUILD_MIL node not owned"
        if ws.econ.get(act.actor, 0) < 2:
            return False, "Not enough econ"
        return True, ""
    if act.type in ("ANNEX", "STRIKE"):
        if act.from_node is None or act.to_node is None or act.amount is None:
            return False, f"{act.type} missing fields"
        if not is_adjacent(act.from_node, act.to_node):
            return False, f"{act.type} non-adjacent"
        # Attacks/annexes must originate from a node you own (no pre-staging on
        # neutral/enemy nodes in MVP since we don't track per-player stacks).
        if ws.nodes[act.from_node].owner != act.actor:
            return False, f"{act.type} from non-owned node"
        if ws.nodes[act.from_node].stationed_mil < act.amount or act.amount <= 0:
            return False, f"{act.type} invalid amount"
        return True, ""
    if act.type == "SPY":
        return True, ""
    if act.type in ("DEESCALATE", "MOBILIZE"):
        return True, ""
    if act.type in ("OFFER", "ACCEPT", "REJECT"):
        return True, ""
    return False, "Unknown action"
