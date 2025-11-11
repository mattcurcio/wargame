from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional, Tuple

PlayerID = str
NodeID = Literal["A", "B", "C", "D", "E"]  # MVP linear map
ActionType = Literal[
    "BUILD_ECON", "BUILD_MIL", "MOVE", "ANNEX", "STRIKE", "SPY",
    "DEESCALATE", "MOBILIZE", "OFFER", "ACCEPT", "REJECT"
]

@dataclass
class NodeState:
    owner: Optional[PlayerID]  # None -> Neutral
    neutral_defense: int
    stationed_mil: int
    income: int = 1

@dataclass
class ContractTerms:
    type: Literal["NAP", "PAYMENT", "CEASEFIRE", "DEFENSE_PACT"]
    nodes: List[NodeID] | None
    duration: int
    payments: Optional[dict] = None  # {from, to, amount, frequency}

@dataclass
class Contract:
    id: str
    parties: Tuple[PlayerID, PlayerID]
    terms: ContractTerms
    start_turn: int
    end_turn: int
    status: Literal["active", "fulfilled", "expired"] = "active"

@dataclass
class WorldState:
    turn: int
    defcon: int
    nodes: Dict[NodeID, NodeState]
    econ: Dict[PlayerID, int]
    trust: Dict[PlayerID, Dict[PlayerID, float]]
    contracts: List[Contract] = field(default_factory=list)

@dataclass
class OfferProposal:
    # lightweight structure for offers in MVP
    type: Literal["NAP", "PAYMENT", "CEASEFIRE", "DEFENSE_PACT"]
    parties: Tuple[PlayerID, PlayerID]
    duration: int
    nodes: Optional[List[NodeID]] = None
    payments: Optional[dict] = None  # {from, to, amount, frequency}

@dataclass
class Action:
    actor: PlayerID
    type: ActionType
    # Optional fields depending on action
    node: Optional[NodeID] = None
    from_node: Optional[NodeID] = None
    to_node: Optional[NodeID] = None
    amount: Optional[int] = None
    proposal: Optional[OfferProposal] = None
    proposal_id: Optional[str] = None
