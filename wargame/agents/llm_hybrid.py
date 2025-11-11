from __future__ import annotations
from typing import List
from ..types import WorldState, Action

class HybridAgent:
    def __init__(self, player_id: str):
        self.player_id = player_id

    def candidate_actions(self, ws: WorldState) -> List[Action]:
        # deterministic generator of 3–6 candidates based on state (stub)
        cands: List[Action] = [Action(actor=self.player_id, type="BUILD_ECON")]
        # add a conservative BUILD_MIL if affordable on first owned node
        for nid, node in ws.nodes.items():
            if node.owner == self.player_id and ws.econ.get(self.player_id, 0) >= 2:
                cands.append(Action(actor=self.player_id, type="BUILD_MIL", node=nid))
                break
        return cands

    def rank_with_llm(self, candidates: List[Action]) -> List[Action]:
        # placeholder; integrate LLM later (return first two)
        return candidates[:2]

    def decide(self, ws: WorldState) -> List[Action]:
        cands = self.candidate_actions(ws)
        if not cands:
            return []
        return self.rank_with_llm(cands)
