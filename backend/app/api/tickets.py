from fastapi import APIRouter

from app.services.ticket_service import list_handoff_tickets, resolve_handoff_ticket


router = APIRouter()


@router.get("/api/handoff-tickets")
def handoff_tickets():
    return list_handoff_tickets()


@router.post("/api/handoff-tickets/{ticket_id}/resolve")
def resolve_ticket(ticket_id: str):
    return resolve_handoff_ticket(ticket_id)
