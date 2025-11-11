from __future__ import annotations
from dataclasses import dataclass
from typing import Dict
from .types import PlayerID

@dataclass
class PlayerProfile:
    name: PlayerID
    aggression: float = 0.5
    deviousness: float = 0.5
    risk: float = 0.5
    prio_mil: float = 0.4
    prio_econ: float = 0.4
    prio_diplo: float = 0.2

@dataclass
class GameConfig:
    players: Dict[PlayerID, PlayerProfile]
    defcon_start: int = 5
    action_limit_per_turn: int = 2
    accept_limit_per_turn: int = 2
