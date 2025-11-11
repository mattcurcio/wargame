from wargame.engine.state import init_world
from wargame.engine.rules import validate_action
from wargame.types import Action


def test_move_into_non_owned_node_invalid():
    ws = init_world()
    act = Action(actor="Astra", type="MOVE", from_node="A", to_node="B", amount=1)
    ok, msg = validate_action(ws, act)
    assert not ok
    assert "MOVE into non-owned node" in msg


def test_attack_from_unowned_node_invalid():
    ws = init_world()
    act = Action(actor="Astra", type="STRIKE", from_node="B", to_node="C", amount=1)
    ok, msg = validate_action(ws, act)
    assert not ok
    assert "STRIKE from non-owned node" in msg


def test_annex_from_non_owned_invalid():
    ws = init_world()
    act = Action(actor="Astra", type="ANNEX", from_node="B", to_node="A", amount=3)
    ok, msg = validate_action(ws, act)
    assert not ok
    assert "ANNEX from non-owned node" in msg


def test_move_between_owned_nodes_valid():
    ws = init_world()
    # Make B owned by Astra and give units on A
    ws.nodes["B"].owner = "Astra"
    ws.nodes["A"].stationed_mil = 3
    act = Action(actor="Astra", type="MOVE", from_node="A", to_node="B", amount=2)
    ok, msg = validate_action(ws, act)
    assert ok, msg
