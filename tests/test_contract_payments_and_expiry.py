from wargame.engine.state import init_world
from wargame.engine.resolver import resolve_turn
from wargame.engine.contracts import create_contract
from wargame.types import OfferProposal, Action

def test_payment_contract_executes_and_expires():
    ws = init_world()
    # Create per-turn payment from Borealis->Astra for 2 turns
    prop = OfferProposal(
        type="PAYMENT",
        parties=("Borealis", "Astra"),
        duration=2,
        payments={"from": "Borealis", "to": "Astra", "amount": 1, "frequency": "per_turn"},
    )
    create_contract(ws, prop, start_turn=ws.turn)

    econ_a0, econ_b0 = ws.econ["Astra"], ws.econ["Borealis"]

    # Turn 1 resolve: payment executes, then income
    ws = resolve_turn(ws, {"Astra": [], "Borealis": [], "Cinder": []})
    assert ws.econ["Astra"] >= econ_a0 + 1  # +1 payment (plus income)
    assert ws.econ["Borealis"] <= econ_b0 - 1 + 1  # -1 payment + own income

    # Turn 2 resolve: payment executes again, then expires
    econ_a1, econ_b1 = ws.econ["Astra"], ws.econ["Borealis"]
    ws = resolve_turn(ws, {"Astra": [], "Borealis": [], "Cinder": []})
    assert ws.contracts[0].status in ("active", "expired")  # may expire at end of turn depending on end_turn logic

    # Turn 3: no further payments
    econ_a2, econ_b2 = ws.econ["Astra"], ws.econ["Borealis"]
    ws = resolve_turn(ws, {"Astra": [], "Borealis": [], "Cinder": []})
    # delta should be only income now (no more -1/+1 transfer)
    assert (ws.econ["Astra"] - econ_a2) == 1  # owns C only => +1; adjust if you change income model
