from __future__ import annotations
from typing import List, Optional
from pathlib import Path
from ..types import Action, WorldState
from ..engine.rules import validate_action
from ..engine.state import LINEAR_EDGES


class HumanAgent:
    """Interactive human agent that prompts on stdin for up to two actions per turn."""

    def __init__(self, player_id: str):
        self.player_id = player_id

    def decide(self, ws: WorldState) -> List[Action]:
        # Simplest interactive wrapper: reuse the prompt loop here
        print(f"Human player: {self.player_id} ")
        actions: List[Action] = []

        cheat = self._load_cheat_sheet()
        # use shared parser and example generator from wargame.cli
        from ..cli import parse_command, generate_legal_examples

        # show a few legal examples
        examples = generate_legal_examples(ws, self.player_id)
        if examples:
            print("Examples:")
            for ex in examples:
                print(" ", ex)

        for i in range(2):
            while True:
                prompt = f"[{self.player_id}] action {i+1} (HELP for cheat sheet, blank to skip): "
                try:
                    raw = input(prompt)
                except EOFError:
                    raw = ""
                if not raw.strip():
                    break
                parsed = parse_command(raw, ws, self.player_id)
                if parsed is None:
                    if raw.strip().upper() == "HELP":
                        print(cheat)
                        continue
                    print("Could not parse command. Type HELP to see grammar examples.")
                    continue
                # validate MOVE target ownership before accepting
                if parsed.type == "MOVE":
                    dest = parsed.to_node
                    if dest is None or ws.nodes.get(dest) is None or ws.nodes[dest].owner != self.player_id:
                        print(f"Invalid MOVE: destination {dest} is not owned by {self.player_id}. Move only between owned nodes.")
                        continue
                # optional: validate full action and show reason
                ok, reason = validate_action(ws, parsed)
                if not ok:
                    print(f"Action invalid: {reason}")
                    continue
                actions.append(parsed)
                break
        return actions

    def _load_cheat_sheet(self) -> str:
        base = Path(__file__).resolve().parent.parent
        gram = base / "Grammar.txt"
        if gram.exists():
            return gram.read_text()
        return "(cheat sheet not found)"

    def _generate_legal_examples(self, ws: WorldState, max_examples: int = 3) -> List[str]:
        examples: List[str] = []
        examples.append("BUILD_ECON")
        if ws.econ.get(self.player_id, 0) >= 2:
            for nid, node in ws.nodes.items():
                if node.owner == self.player_id:
                    examples.append(f"BUILD_MIL {nid}")
                    break
        for nid, node in ws.nodes.items():
            if node.owner != self.player_id:
                continue
            for nbr in LINEAR_EDGES.get(nid, []):
                if ws.nodes[nbr].owner == self.player_id and node.stationed_mil > 0:
                    examples.append(f"MOVE {nid} {nbr} 1")
                    if len(examples) >= max_examples:
                        return examples
        return examples[:max_examples]


class ScriptedHumanAgent(HumanAgent):
    """Non-interactive human agent for scripted runs/tests.

    Provide a list of command strings; decide() will consume up to two per call.
    """

    def __init__(self, player_id: str, script: Optional[List[str]] = None):
        super().__init__(player_id)
        self.script = script or []

    def decide(self, ws: WorldState) -> List[Action]:
        out: List[Action] = []
        for _ in range(2):
            if not self.script:
                break
            raw = self.script.pop(0)
            # reuse parsing from HumanAgent but without input loop
            act = None
            tok = raw.strip().upper().split()
            if not tok:
                continue
            cmd = tok[0]
            if cmd == "BUILD":
                cmd = "BUILD_ECON"
            if cmd == "MIL":
                cmd = "BUILD_MIL"
            if cmd == "TAKE":
                cmd = "ANNEX"
            if cmd == "ATTACK":
                cmd = "STRIKE"
            try:
                if cmd == "BUILD_ECON":
                    act = Action(actor=self.player_id, type="BUILD_ECON")
                elif cmd == "BUILD_MIL":
                    node = tok[1]
                    act = Action(actor=self.player_id, type="BUILD_MIL", node=node)
                elif cmd == "ANNEX":
                    frm, to, amt = tok[1], tok[2], int(tok[3])
                    act = Action(actor=self.player_id, type="ANNEX", from_node=frm, to_node=to, amount=amt)
                elif cmd == "STRIKE":
                    frm, to, amt = tok[1], tok[2], int(tok[3])
                    act = Action(actor=self.player_id, type="STRIKE", from_node=frm, to_node=to, amount=amt)
                elif cmd == "MOVE":
                    frm, to, amt = tok[1], tok[2], int(tok[3])
                    act = Action(actor=self.player_id, type="MOVE", from_node=frm, to_node=to, amount=amt)
            except Exception:
                act = None
            if act is None:
                continue
            # Validate move destination ownership
            if act.type == "MOVE":
                dest = act.to_node
                if dest is None or ws.nodes.get(dest) is None or ws.nodes[dest].owner != self.player_id:
                    continue
            ok, reason = validate_action(ws, act)
            if not ok:
                continue
            out.append(act)
        return out
