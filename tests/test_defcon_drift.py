from wargame.engine.state import init_world, set_defcon
from wargame.engine.resolver import resolve_turn

def test_defcon_drifts_toward_three():
    ws = init_world()
    # Per PRD: de-escalation requires two consecutive peaceful turns.
    # Start at DEFCON 3 and two peaceful turns should raise it to 5.
    set_defcon(ws, 3)
    ws = resolve_turn(ws, {"Astra": [], "Borealis": [], "Cinder": []})
    assert ws.defcon == 4
    ws = resolve_turn(ws, {"Astra": [], "Borealis": [], "Cinder": []})
    assert ws.defcon == 5
