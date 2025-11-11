from wargame.engine.state import init_world
from wargame.engine.resolver import resolve_turn
from wargame.types import Action

def test_strike_success_captures_and_leaves_garrison():
    ws = init_world()
    # Turn 1: Astra annexes B (3)
    actions1 = {
        "Astra": [Action(actor="Astra", type="ANNEX", from_node="A", to_node="B", amount=3)],
        "Borealis": [],
        "Cinder": [],
    }
    ws = resolve_turn(ws, actions1)

    # Turn 2: build mil at B to increase attacker pool
    actions2 = {
        "Astra": [Action(actor="Astra", type="BUILD_MIL", node="B")],
        "Borealis": [],
        "Cinder": [],
    }
    ws = resolve_turn(ws, actions2)

    # Simulate defender weakened
    ws.nodes["C"].stationed_mil = 2

    # Turn 3: strike C with 3 from B
    actions3 = {
        "Astra": [Action(actor="Astra", type="STRIKE", from_node="B", to_node="C", amount=3)],
        "Borealis": [],
        "Cinder": [],
    }
    ws = resolve_turn(ws, actions3)

    assert ws.nodes["C"].owner == "Astra"
    # Attacker leaves >=1 to hold; with 3 used, garrison should be at least 1 by our rule (max(1, amount-1))
    assert ws.nodes["C"].stationed_mil >= 1
    # Attacker should have lost some units at B
    assert ws.nodes["B"].stationed_mil <= 2
