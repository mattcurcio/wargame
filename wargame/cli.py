from __future__ import annotations
from typing import List, Optional
from .types import Action, WorldState
from .engine.rules import validate_action
from .engine.state import LINEAR_EDGES


def generate_legal_examples(ws: WorldState, player: str, max_examples: int = 3) -> List[str]:
    """Generate a few legal example commands for the given player based on state.

    This is a shared utility used by the interactive runner and the human agent.
    """
    examples: List[str] = []
    # BUILD_ECON always legal
    examples.append("BUILD_ECON")
    # BUILD_MIL if player can afford and has a node
    if ws.econ.get(player, 0) >= 2:
        for nid, node in ws.nodes.items():
            if node.owner == player:
                cmd = f"BUILD_MIL {nid}"
                ok, _ = validate_action(ws, Action(actor=player, type="BUILD_MIL", node=nid))
                if ok:
                    examples.append(cmd)
                    break
    # MOVEs between owned nodes
    for nid, node in ws.nodes.items():
        if node.owner != player:
            continue
        for nbr in LINEAR_EDGES.get(nid, []):
            if ws.nodes[nbr].owner == player and node.stationed_mil > 0:
                cmd = f"MOVE {nid} {nbr} 1"
                ok, _ = validate_action(ws, Action(actor=player, type="MOVE", from_node=nid, to_node=nbr, amount=1))
                if ok:
                    examples.append(cmd)
                    if len(examples) >= max_examples:
                        return examples
    # ANNEX/STRIKE candidates
    for nid, node in ws.nodes.items():
        if node.owner != player:
            continue
        for nbr in LINEAR_EDGES.get(nid, []):
            tgt = ws.nodes[nbr]
            # annex neutral
            if tgt.owner is None and node.stationed_mil > tgt.neutral_defense:
                amt = min(node.stationed_mil, max(tgt.neutral_defense + 1, 1))
                cmd = f"ANNEX {nid} {nbr} {amt}"
                ok, _ = validate_action(ws, Action(actor=player, type="ANNEX", from_node=nid, to_node=nbr, amount=amt))
                if ok:
                    examples.append(cmd)
                    if len(examples) >= max_examples:
                        return examples
            # strike enemy
            if tgt.owner not in (None, player) and node.stationed_mil > 0:
                amt = min(node.stationed_mil, tgt.stationed_mil + 1)
                cmd = f"STRIKE {nid} {nbr} {amt}"
                ok, _ = validate_action(ws, Action(actor=player, type="STRIKE", from_node=nid, to_node=nbr, amount=amt))
                if ok:
                    examples.append(cmd)
                    if len(examples) >= max_examples:
                        return examples
    # NUCLEAR: suggest targets if allowed (show after conventional examples)
    # Suggest enemy/neutral nodes that validate as legal NUCLEAR targets. Since
    # the interactive grammar allows omitting a FROM launch-site, attempt to
    # auto-select a valid launch site (owned node with >=3 mil) when validating
    # examples so the human sees only actually-legal suggestions.
    for node_id, node in ws.nodes.items():
        if node.owner == player:
            continue
        # find a candidate launch site owned by player with enough mil
        launch_site = None
        for nid, n in ws.nodes.items():
            if n.owner == player and n.stationed_mil >= 3:
                launch_site = nid
                break
        candidate = Action(actor=player, type="NUCLEAR", to_node=node_id, from_node=launch_site)
        ok, _ = validate_action(ws, candidate)
        if ok:
            examples.append(f"NUCLEAR {node_id}")
            if len(examples) >= max_examples:
                return examples[:max_examples]

    # PREP_NUKE: suggest research/prep action if valid (provocative - will lower DEFCON)
    prep_candidate = Action(actor=player, type="PREP_NUKE")
    ok, _ = validate_action(ws, prep_candidate)
    if ok:
        examples.append("PREP_NUKE")

    return examples[:max_examples]


def parse_command(s: str, ws: WorldState, player: str) -> Optional[Action]:
    """Parse a user command string into an Action or None.

    This function does not print HELP text; callers should handle HELP by
    checking for the raw input and printing the cheat sheet as needed.
    """
    tok = s.strip().upper().split()
    if not tok:
        return None
    cmd = tok[0]
    # aliases
    if cmd == "BUILD":
        cmd = "BUILD_ECON"
    if cmd == "MIL":
        cmd = "BUILD_MIL"
    if cmd == "TAKE":
        cmd = "ANNEX"
    if cmd == "ATTACK":
        cmd = "STRIKE"
    if cmd == "NUC":
        cmd = "NUCLEAR"
    if cmd == "PREP":
        cmd = "PREP_NUKE"

    try:
        if cmd in ("BUILD_ECON",):
            return Action(actor=player, type="BUILD_ECON")
        if cmd == "BUILD_MIL":
            node = tok[1]
            return Action(actor=player, type="BUILD_MIL", node=node)
        if cmd == "ANNEX":
            frm, to, amt = tok[1], tok[2], int(tok[3])
            return Action(actor=player, type="ANNEX", from_node=frm, to_node=to, amount=amt)
        if cmd == "STRIKE":
            frm, to, amt = tok[1], tok[2], int(tok[3])
            return Action(actor=player, type="STRIKE", from_node=frm, to_node=to, amount=amt)
        if cmd == "MOVE":
            frm, to, amt = tok[1], tok[2], int(tok[3])
            return Action(actor=player, type="MOVE", from_node=frm, to_node=to, amount=amt)
        if cmd == "NUCLEAR":
            # nuclear takes a single target node. The interactive prompt
            # allows omitting an explicit launch site; auto-select a
            # valid owned node with >=3 mil if available so validation
            # succeeds and the human gets clearer feedback.
            if len(tok) < 2:
                return None
            tgt = tok[1]
            launch_site = None
            for nid, n in ws.nodes.items():
                if n.owner == player and n.stationed_mil >= 3:
                    launch_site = nid
                    break
            return Action(actor=player, type="NUCLEAR", to_node=tgt, from_node=launch_site)
        if cmd == "PREP_NUKE":
            return Action(actor=player, type="PREP_NUKE")
        if cmd in ("NONE", ""):
            return None
    except Exception:
        return None
    return None
