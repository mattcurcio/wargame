from __future__ import annotations
from typing import Dict, List, Optional
from pathlib import Path
from .types import WorldState, Action
from .engine.state import init_world, LINEAR_EDGES
from .engine.resolver import resolve_turn
from .engine.rules import validate_action
from .cli import parse_command, generate_legal_examples
from .engine.utils import print_turn, full_state_str, player_view_str, render_visual, scoreboard_str
from .agents.human import HumanAgent, ScriptedHumanAgent


def run_headless_match(
    agents: Dict[str, object], max_turns: int = 6, debug: bool = False, player_view: Optional[str] = None, visual: bool = False
) -> WorldState:
    """Run a headless match.

    If debug is True, print the full world state after each turn. If player_view
    is set to a player id, print that player's view (non-revealing) after each turn.
    """
    ws = init_world()
    human_players = set()
    for _ in range(max_turns):
        actions_by_player: Dict[str, List[Action]] = {}
        for pid, agent in agents.items():
            if isinstance(agent, HumanAgent) or isinstance(agent, ScriptedHumanAgent):
                actions = agent.decide(ws)
                actions_by_player[pid] = actions
                human_players.add(pid)
            elif isinstance(agent, str) and agent == "HUMAN":
                # legacy support: treat string marker as interactive human
                from .agents.human import HumanAgent as _HA

                ha = _HA(pid)
                actions = ha.decide(ws)
                actions_by_player[pid] = actions
                human_players.add(pid)
            else:
                actions = agent.decide(ws)
                actions_by_player[pid] = actions
        print_turn(ws, actions_by_player)
        if visual:
            print(render_visual(ws))
        ws = resolve_turn(ws, actions_by_player)
        # post-turn logging: concise scoreboard and optional visual of the updated state
        print(f"\n--- End of Turn {ws.turn - 1} Summary | DEFCON {ws.defcon} ---")
        print(scoreboard_str(ws))
        # Print any notable events (nuclear launches, etc.) that happened during the turn
        if getattr(ws, "events", None):
            RED = "\u001b[31;1m"
            RESET = "\u001b[0m"
            print("\nEvents:")
            for e in ws.events:
                # Pretty-highlight nuclear events so they stand out to humans
                if "NUCLEAR" in e.upper():
                    try:
                        print(RED + "!!! NUCLEAR EVENT !!!" + RESET)
                        print(RED + "  - " + e + RESET)
                    except Exception:
                        print("  -", e)
                else:
                    print("  -", e)
            # Clear events after printing so they don't repeat next turn
            try:
                ws.events.clear()
            except Exception:
                pass
        if visual:
            print(render_visual(ws))
        # post-turn state print
        if debug:
            print("\n[DEBUG STATE]\n" + full_state_str(ws))
        elif player_view:
            print(f"\n[PLAYER VIEW: {player_view}]\n" + player_view_str(ws, player_view))
    return ws

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="print full debug state each turn")
    parser.add_argument("--player", type=str, help="print player-specific view each turn")
    parser.add_argument("--visual", action="store_true", help="print enhanced ASCII visuals each turn")
    parser.add_argument("--turns", type=int, default=6, help="number of turns to run")
    parser.add_argument("--human", action="append", help="player id to control as human; can be repeated")
    args = parser.parse_args()

    from .agents.heuristic import HeuristicAgent
    agents = {
        "Astra": HeuristicAgent("Astra"),
        "Borealis": HeuristicAgent("Borealis"),
        "Cinder": HeuristicAgent("Cinder"),
    }

    # Replace specified agents with HUMAN marker
    if args.human:
        for hid in args.human:
            if hid in agents:
                agents[hid] = "HUMAN"

    final_state = run_headless_match(
        agents, max_turns=args.turns, debug=args.debug, player_view=args.player, visual=args.visual
    )
    print("\nFinal state:\n", full_state_str(final_state) if args.debug else (player_view_str(final_state, args.player) if args.player else final_state))


def _load_cheat_sheet() -> str:
    # Try a few reasonable locations for Grammar.txt so HELP works whether
    # the package is run from the repo, installed in editable mode, or run
    # from elsewhere.
    candidates = []
    # 1) repo root two levels up (original behavior)
    pkg_base = Path(__file__).resolve().parent.parent
    candidates.append(pkg_base / "Grammar.txt")
    # 2) package directory (next to this file)
    candidates.append(Path(__file__).resolve().parent / "Grammar.txt")
    # 3) current working directory (if user runs from repo root)
    candidates.append(Path.cwd() / "Grammar.txt")
    # 4) one level up from cwd (in case running from nested folder)
    candidates.append(Path.cwd().parent / "Grammar.txt")

    for gram in candidates:
        try:
            if gram.exists():
                return gram.read_text()
        except Exception:
            # ignore permission/IO errors and try next
            continue
    return "(cheat sheet not found)"


def generate_legal_examples(ws: WorldState, player: str, max_examples: int = 3) -> List[str]:
    """Generate a few legal example commands for the given player based on state."""
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
    # suggest enemy/neutral nodes that validate as legal NUCLEAR targets
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

    return examples[:max_examples]


def prompt_for_two_actions(ws: WorldState, player: str) -> List[Action]:
    """Prompt the human player for up to two actions using the project's grammar.

    Returns a list of 0..2 Action objects. Recognizes aliases and HELP command.
    """
    cheat = _load_cheat_sheet()
    actions: List[Action] = []

    # use shared parser (caller handles printing HELP)

    # show a few legal examples based on current state
    examples = generate_legal_examples(ws, player)
    if examples:
        print("Examples:")
        for ex in examples:
            print("  ", ex)

    for i in range(2):
        while True:
            prompt = f"[{player}] action {i+1} (HELP for cheat sheet, blank to skip): "
            try:
                raw = input(prompt)
            except EOFError:
                raw = ""
            if not raw.strip():
                break
            parsed = parse_command(raw, ws, player)
            if parsed is None:
                # either HELP was requested or parse error
                if raw.strip().upper() == "HELP":
                    print(cheat)
                    continue
                print("Could not parse command. Type HELP to see grammar examples.")
                continue
            # Validate MOVE target ownership before accepting
            if parsed.type == "MOVE":
                dest = parsed.to_node
                if dest is None or ws.nodes.get(dest) is None or ws.nodes[dest].owner != player:
                    print(f"Invalid MOVE: destination {dest} is not owned by {player}. Move only between owned nodes.")
                    continue
            # Validate NUCLEAR immediately so the human gets feedback
            if parsed.type == "NUCLEAR":
                ok, msg = validate_action(ws, parsed)
                if not ok:
                    print(f"Invalid NUCLEAR: {msg}")
                    continue
            # attach actor already set in parse
            actions.append(parsed)
            break
    return actions
