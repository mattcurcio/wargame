from __future__ import annotations
import uuid
from ..types import WorldState, OfferProposal, Contract, ContractTerms


def create_contract(ws: WorldState, proposal: OfferProposal, start_turn: int) -> Contract:
    terms = ContractTerms(
        type=proposal.type,
        nodes=proposal.nodes,
        duration=proposal.duration,
        payments=proposal.payments,
    )
    c = Contract(
        id=str(uuid.uuid4()),
        parties=proposal.parties,
        terms=terms,
        start_turn=start_turn,
        end_turn=start_turn + proposal.duration,
        status="active",
    )
    ws.contracts.append(c)
    return c


def process_contracts(ws: WorldState) -> None:
    # Auto-payments + expirations (MVP: no breaches)
    for c in ws.contracts:
        if c.status != "active":
            continue
        # Expire contracts first to avoid executing payments on the end_turn
        if ws.turn >= c.end_turn:
            c.status = "expired"
            continue
        if c.terms.payments:
            if c.terms.payments.get("frequency") == "per_turn":
                src = c.terms.payments["from"]
                dst = c.terms.payments["to"]
                amt = int(c.terms.payments["amount"])
                if ws.econ.get(src, 0) >= amt:
                    ws.econ[src] -= amt
                    ws.econ[dst] = ws.econ.get(dst, 0) + amt
