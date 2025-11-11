from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional, Tuple

PlayerID = str
NodeID = Literal["A", "B", "C", "D", "E"]  # MVP linear map
ActionType = Literal[
    "BUILD_ECON", "BUILD_MIL", "MOVE", "ANNEX", "STRIKE", "SPY",
    "DEESCALATE", "MOBILIZE", "OFFER", "ACCEPT", "REJECT", "NUCLEAR",
    "PREP_NUKE"
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
    # Event log for the turn (append-only; resolver may populate with notable events)
    events: List[str] = field(default_factory=list)
    # Nuclear research progress (counts turns of PREP_NUKE); when >=2 considered completed
    research_progress: Dict[PlayerID, int] = field(default_factory=dict)
    # Sanctions: number of turns a player is sanctioned (cannot BUILD_ECON or DEESCALATE)
    sanctions: Dict[PlayerID, int] = field(default_factory=dict)
    # Next-turn income multiplier (e.g., 0.9 after nuclear)
    next_income_multiplier: Dict[PlayerID, float] = field(default_factory=dict)
    # Whether the previous turn was peaceful (no STRIKE/ANNEX)
    last_turn_peaceful: bool = False

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
