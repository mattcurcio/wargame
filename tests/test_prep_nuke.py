from wargame.engine.state import init_world, set_defcon
from wargame.engine.resolver import resolve_turn
from wargame.types import Action


def test_prep_nuke_decreases_defcon_once_and_increments_research():
    ws = init_world()
    # start at DEFCON 5 and have two players both prepare nukes
    set_defcon(ws, 5)
    actions = {
        "Astra": [Action(actor="Astra", type="PREP_NUKE")],
        "Borealis": [Action(actor="Borealis", type="PREP_NUKE")],
        "Cinder": [],
    }
    new_ws = resolve_turn(ws, actions)
    # PREP_NUKE is provocative: when multiple players prepare in the same
    # turn DEFCON jumps to 2 (heavy escalation)
    assert new_ws.defcon == 2
    # research progress should increment for those who prepared
    assert new_ws.research_progress.get("Astra", 0) == 1
    assert new_ws.research_progress.get("Borealis", 0) == 1
    # events should include a note about preparation and research progress
    assert any("prep" in e.lower() or "prepar" in e.lower() for e in new_ws.events)
    assert any("research" in e.lower() and "astra" in e.lower() for e in new_ws.events)


def test_prep_nuke_allowed_at_any_defcon():
    ws = init_world()
    # test at DEFCON 2 and DEFCON 1
    for level in (2, 1, 3, 5):
        set_defcon(ws, level)
        ok_ws = resolve_turn(ws, {"Astra": [Action(actor="Astra", type="PREP_NUKE")], "Borealis": [], "Cinder": []})
        # research increments regardless of DEFCON
        assert ok_ws.research_progress.get("Astra", 0) >= 1
        # reset research for next iteration
        ws.research_progress["Astra"] = 0
