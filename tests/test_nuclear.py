from wargame.engine.state import init_world, set_defcon
from wargame.engine.resolver import resolve_turn
from wargame.engine.rules import validate_action
from wargame.types import Action


def test_nuclear_disallowed_at_high_defcon():
    ws = init_world()
    act = Action(actor="Astra", type="NUCLEAR", to_node="C")
    ok, msg = validate_action(ws, act)
    assert not ok
    assert "NUCLEAR disallowed" in msg


def test_nuclear_launch_effects():
    ws = init_world()
    # bring DEFCON down to 2 so nuclear is allowed
    set_defcon(ws, 2)
    # give Astra enough econ to launch
    ws.econ["Astra"] = 10
    # mark research as completed for Astra
    ws.research_progress["Astra"] = 2
    # ensure target is owned and has stationed forces
    ws.nodes["C"].owner = "Borealis"
    ws.nodes["C"].stationed_mil = 4

    actions = {
        "Astra": [Action(actor="Astra", type="NUCLEAR", from_node="A", to_node="C")],
        "Borealis": [],
        "Cinder": [],
    }

    new_ws = resolve_turn(ws, actions)

    # econ deducted by 10 (accounting for income phase after combat)
    initial = ws.econ.get("Astra", 0)
    income_sum = sum(n.income for n in new_ws.nodes.values() if n.owner == "Astra")
    # Nuclear reduces next-turn income by 10% (applied as int truncation)
    applied_income = int(income_sum * 0.9)
    assert new_ws.econ.get("Astra", 0) == initial - 10 + applied_income
    # target node neutralized
    assert new_ws.nodes["C"].owner is None
    assert new_ws.nodes["C"].stationed_mil == 0
    # DEFCON was escalated during combat and drift is suppressed after a nuclear launch
    assert new_ws.defcon == 1
