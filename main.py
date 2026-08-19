from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.chat import router as chat_router
from app.api.v1.document import router as document_router
from app.api.v1.tickets import router as ticket_router
from app.api.v1.memory import router as memory_router
from app.api.v1.health import router as health_router
from app.core.logging import setup_logfire
from app.database.connection import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logfire()
    await init_db()
    yield


app = FastAPI(title="Organizational Intelligent AI Platform", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(document_router)
app.include_router(ticket_router)
app.include_router(memory_router)


from fastapi.responses import FileResponse
import tempfile
from app.workflows.graph import graph
import os

@app.get("/graph")
async def print_graph():
    """Generate and return the LangGraph visualization."""
    png_data = graph.get_graph().draw_mermaid_png()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f:
        f.write(png_data)
        temp_path = f.name

    return FileResponse(
        temp_path,
        media_type="image/png",
        filename="langgraph.png",
    )