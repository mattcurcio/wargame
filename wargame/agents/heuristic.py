from __future__ import annotations
from typing import List
from ..types import WorldState, Action
from ..engine.state import LINEAR_EDGES

class HeuristicAgent:
    """Very simple baseline agent for MVP.
    Priority: annex adjacent neutral with 3 units if possible; else build econ; else build mil at capital.
    """
    def __init__(self, player_id: str):
        self.player_id = player_id

    def decide(self, ws: WorldState) -> List[Action]:
        acts: List[Action] = []
        # find my nodes
        my_nodes = [nid for nid, n in ws.nodes.items() if n.owner == self.player_id]
        # 1) Try to annex an adjacent neutral with at least 3 units
        for nid in my_nodes:
            for nbr in LINEAR_EDGES[nid]:
                if ws.nodes[nbr].owner is None and ws.nodes[nid].stationed_mil >= 3:
                    acts.append(Action(actor=self.player_id, type="ANNEX", from_node=nid, to_node=nbr, amount=3))
                    return acts
        # 2) Otherwise build econ
        acts.append(Action(actor=self.player_id, type="BUILD_ECON"))
        # 3) And try to build mil at the first owned node if we can afford it
        first_owned = my_nodes[0] if my_nodes else None
        if first_owned and ws.econ.get(self.player_id, 0) >= 2:
            acts.append(Action(actor=self.player_id, type="BUILD_MIL", node=first_owned))
        return acts[:2]
