from wargame.engine.state import init_world
from wargame.engine.resolver import resolve_turn
from wargame.types import Action

def test_cannot_move_into_neutral_or_enemy():
    ws = init_world()
    # B is neutral, moving A->B should be rejected by validation (no staging in MVP)
    actions = {"Astra": [Action(actor="Astra", type="MOVE", from_node="A", to_node="B", amount=1)]}
    ws2 = resolve_turn(ws, actions)
    assert ws2.nodes["B"].owner is None
    assert ws2.nodes["A"].stationed_mil == ws.nodes["A"].stationed_mil
