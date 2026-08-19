from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db
from app.database.repositories import TicketRepository


router = APIRouter(prefix="/tickets", tags=["Tickets"])


class TicketCreate(BaseModel):
    user_id: str
    session_id: str = "default"
    description: str
    department: str = "General"
    priority: str = "MEDIUM"


@router.post("/")
async def create_ticket(req: TicketCreate, db: AsyncSession = Depends(get_db)):
    repo = TicketRepository(db)
    ticket = await repo.create(
        user_id=req.user_id,
        session_id=req.session_id,
        description=req.description,
        department=req.department,
        priority=req.priority,
    )
    return {"ticket_id": ticket.id, "status": ticket.status, "priority": ticket.priority}


@router.get("/")
async def list_tickets(user_id: str = "anonymous", db: AsyncSession = Depends(get_db)):
    repo = TicketRepository(db)
    tickets = await repo.get_by_user(user_id)
    return [
        {"id": t.id, "status": t.status, "priority": t.priority, "department": t.department,
         "description": t.description, "created_at": str(t.created_at)}
        for t in tickets
    ]
