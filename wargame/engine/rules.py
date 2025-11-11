from __future__ import annotations
from ..types import Action, WorldState, NodeID
from .state import LINEAR_EDGES

def is_adjacent(a: NodeID, b: NodeID) -> bool:
    return b in LINEAR_EDGES.get(a, [])

def validate_action(ws: WorldState, act: Action) -> tuple[bool, str]:
    # Basic legality checks (MVP)
    # DEFCON restrictions (high-level):
    # - DEFCON 5 (peacetime): mostly peacetime behavior (ANNEX allowed)
    # - DEFCON 4: increased tensions
    # - DEFCON 3: normal (all conventional actions allowed)
    # - DEFCON 2 and 1: same as DEFCON 3, plus NUCLEAR allowed (subject to cost)
    # These are conservative defaults; they can be tuned via PRD later.
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
        # BUILD_ECON may be blocked by sanctions
        if ws.sanctions.get(act.actor, 0) > 0:
            return False, "BUILD_ECON disallowed under sanctions"
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
    if act.type == "PREP_NUKE":
        # Prepare nuclear research; allowed at any DEFCON level per PRD,
        # but PREP_NUKE is a provocative action that will be seen by others.
        return True, ""
    if act.type == "NUCLEAR":
        # Nuclear strike preconditions per PRD
        if ws.defcon > 2:
            return False, f"NUCLEAR disallowed at DEFCON {ws.defcon}"
        if act.to_node is None:
            return False, "NUCLEAR missing target"
        # require launch site (from_node) with sufficient mil
        if act.from_node is None:
            return False, "NUCLEAR requires launch site node"
        launch = ws.nodes.get(act.from_node)
        if launch is None or launch.owner != act.actor:
            return False, "NUCLEAR launch site invalid or not owned"
        if launch.stationed_mil < 3:
            return False, "NUCLEAR launch site requires >=3 mil"
        # require research progress (>=2 turns) and econ >= 10
        if ws.research_progress.get(act.actor, 0) < 2:
            return False, "NUCLEAR pre-research incomplete"
        if ws.econ.get(act.actor, 0) < 10:
            return False, "Not enough econ to launch NUCLEAR (need 10)"
        # sanctions may prevent DEESCALATE/BUILD_ECON but not nuclear
        return True, ""
    if act.type == "SPY":
        return True, ""
    if act.type == "DEESCALATE":
        # DEESCALATE only allowed if DEFCON >= 3 and not under sanctions
        if ws.defcon < 3:
            return False, f"DEESCALATE allowed only at DEFCON >= 3"
        if ws.sanctions.get(act.actor, 0) > 0:
            return False, "DEESCALATE disallowed under sanctions"
        return True, ""
    if act.type == "MOBILIZE":
        return True, ""
    if act.type in ("OFFER", "ACCEPT", "REJECT"):
        return True, ""
    return False, "Unknown action"
