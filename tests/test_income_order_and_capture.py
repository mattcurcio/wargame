from wargame.engine.state import init_world
from wargame.engine.resolver import resolve_turn
from wargame.types import Action

def test_annex_then_income_applies_to_new_owner():
    ws = init_world()
    # Turn 1: Astra annexes B (3 units); others idle
    actions1 = {
        "Astra": [Action(actor="Astra", type="ANNEX", from_node="A", to_node="B", amount=3)],
        "Borealis": [],
        "Cinder": [],
    }
    econ_before = ws.econ["Astra"]
    ws = resolve_turn(ws, actions1)
    # Ownership updated before income; Astra should receive +1 income for both A and B
    assert ws.nodes["B"].owner == "Astra"
    assert ws.econ["Astra"] == econ_before + 2  # +1 (A) +1 (B)
