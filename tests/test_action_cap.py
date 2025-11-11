from wargame.engine.state import init_world
from wargame.engine.resolver import resolve_turn
from wargame.types import Action

def test_action_limit_enforced():
    ws = init_world()
    actions = {
        "Astra": [
            Action(actor="Astra", type="BUILD_ECON"),
            Action(actor="Astra", type="BUILD_ECON"),
            Action(actor="Astra", type="BUILD_ECON"),  # should be ignored (cap=2)
        ]
    }
    ws2 = resolve_turn(ws, actions)
    # Only two BUILD_ECON should have applied (+4 total) plus income from owned nodes
    income_gain = sum(n.income for n in ws.nodes.values() if n.owner == "Astra")
    assert ws2.econ["Astra"] == ws.econ["Astra"] + 4 + income_gain
