from wargame.engine.state import init_world
from wargame.engine.resolver import resolve_turn
from wargame.types import Action


def test_income_and_annex():
    ws = init_world()
    actions = {
        # Astra annexes B with 3 units
        "Astra": [Action(actor="Astra", type="ANNEX", from_node="A", to_node="B", amount=3)],
        "Borealis": [Action(actor="Borealis", type="BUILD_ECON")],
        "Cinder": [Action(actor="Cinder", type="BUILD_ECON")],
    }
    ws = resolve_turn(ws, actions)
    assert ws.nodes["B"].owner == "Astra"
    assert ws.econ["Astra"] > 8  # income applied
    assert ws.turn == 2
