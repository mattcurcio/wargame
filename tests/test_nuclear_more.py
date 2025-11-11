from wargame.engine.state import init_world, set_defcon
from wargame.engine.resolver import resolve_turn
from wargame.types import Action


def test_simultaneous_nukes_and_logging():
    ws = init_world()
    # allow nuclear
    set_defcon(ws, 2)
    ws.econ["Astra"] = 10
    ws.econ["Borealis"] = 10
    ws.research_progress["Astra"] = 2
    ws.research_progress["Borealis"] = 2

    # Astra nukes C (Borealis), Borealis nukes A (Astra)
    actions = {
        "Astra": [Action(actor="Astra", type="NUCLEAR", from_node="A", to_node="C")],
        "Borealis": [Action(actor="Borealis", type="NUCLEAR", from_node="C", to_node="A")],
        "Cinder": [],
    }

    new_ws = resolve_turn(ws, actions)

    # Both targets should be neutralized
    assert new_ws.nodes["C"].owner is None
    assert new_ws.nodes["A"].owner is None

    # Both attackers paid (economies reduced compared to before)
    assert new_ws.econ["Astra"] < 10
    assert new_ws.econ["Borealis"] < 10

    # DEFCON should have been escalated to 1 and remain at 1 because drift is suppressed
    assert new_ws.defcon == 1

    # Events should include nuclear messages for both launches
    events = new_ws.events
    assert any("NUCLEAR" in e and "Astra" in e for e in events)
    assert any("NUCLEAR" in e and "Borealis" in e for e in events)
