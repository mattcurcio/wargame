from wargame.engine.state import init_world
from wargame.engine.resolver import resolve_turn
from wargame.types import Action


def test_strike_defender_holds_on_tie():
    ws = init_world()
    # Put 2 units on B for Astra, 2 on C for Borealis
    ws.nodes["A"].stationed_mil = 5
    # Turn 1: Astra annexes B from A with 3 units (leaves 2 on B),
    # Borealis builds mil at C (+2 -> 7)
    actions1 = {
        "Astra": [Action(actor="Astra", type="ANNEX", from_node="A", to_node="B", amount=3)],
        "Borealis": [Action(actor="Borealis", type="BUILD_MIL", node="C")],
        "Cinder": [],
    }
    ws = resolve_turn(ws, actions1)
    # Turn 2: Astra strikes C with 2 vs defender >=2 -> defender holds, attacker loses 1
    actions2 = {
        "Astra": [Action(actor="Astra", type="STRIKE", from_node="B", to_node="C", amount=2)],
        "Borealis": [],
        "Cinder": [],
    }
    before = ws.nodes["A"].stationed_mil + ws.nodes["B"].stationed_mil
    ws = resolve_turn(ws, actions2)
    after = ws.nodes["A"].stationed_mil + ws.nodes["B"].stationed_mil
    assert after == before - 1
    assert ws.nodes["C"].owner == "Borealis"
