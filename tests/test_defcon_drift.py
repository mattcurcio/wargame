from wargame.engine.state import init_world
from wargame.engine.resolver import resolve_turn

def test_defcon_drifts_toward_three():
    ws = init_world()
    # Start at 5; after a turn it should drop to 4
    ws = resolve_turn(ws, {"Astra": [], "Borealis": [], "Cinder": []})
    assert ws.defcon == 4
    # Next turn to 3
    ws = resolve_turn(ws, {"Astra": [], "Borealis": [], "Cinder": []})
    assert ws.defcon == 3
