from __future__ import annotations
from typing import Dict
from ..types import NodeState, WorldState, PlayerID, NodeID

LINEAR_EDGES: Dict[str, list[str]] = {
    "A": ["B"],
    "B": ["A", "C"],
    "C": ["B", "D"],
    "D": ["C", "E"],
    "E": ["D"],
}

START_NODES: Dict[NodeID, NodeState] = {
    "A": NodeState(owner="Astra", neutral_defense=0, stationed_mil=6),
    "B": NodeState(owner=None, neutral_defense=1, stationed_mil=0),
    "C": NodeState(owner="Borealis", neutral_defense=0, stationed_mil=5),
    "D": NodeState(owner=None, neutral_defense=1, stationed_mil=0),
    "E": NodeState(owner="Cinder", neutral_defense=0, stationed_mil=5),
}

START_ECON: Dict[PlayerID, int] = {"Astra": 8, "Borealis": 8, "Cinder": 8}

START_TRUST: Dict[PlayerID, Dict[PlayerID, float]] = {
    "Astra": {"Borealis": 0.5, "Cinder": 0.5},
    "Borealis": {"Astra": 0.5, "Cinder": 0.5},
    "Cinder": {"Astra": 0.5, "Borealis": 0.5},
}

def init_world() -> WorldState:
    return WorldState(
        turn=1,
        defcon=5,
        nodes={k: NodeState(**vars(v)) for k, v in START_NODES.items()},
        econ=START_ECON.copy(),
        trust={p: t.copy() for p, t in START_TRUST.items()},
        contracts=[],
    )

def income_phase(ws: WorldState) -> None:
    for node in ws.nodes.values():
        if node.owner:
            ws.econ[node.owner] = ws.econ.get(node.owner, 0) + node.income

def set_defcon(ws: WorldState, value: int) -> None:
    ws.defcon = max(1, min(5, value))
