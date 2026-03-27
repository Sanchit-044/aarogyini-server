"""
Aarogyini – Chatbot Service
Runs on port 8001. Reached by Flutter only via the API Gateway (port 8000).

CHANGE FROM ORIGINAL:
  - Removed /api/health/* profile/log CRUD routes. Those now live exclusively
    in the Tracker service (port 8002). The chatbot still accepts a profile
    payload inside the ChatRequest body so it can personalise responses,
    but it no longer owns the persistence of that data.
  - Port changed to 8001 in Dockerfile / docker-compose.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import chat           # only the chat router remains
from config import settings

app = FastAPI(
    title="Aarogyini Chatbot Service",
    description="LangChain-powered AI health assistant",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Only the chat router — health data CRUD moved to tracker service
app.include_router(chat.router, prefix="/chat", tags=["chat"])


@app.get("/health")
def health_check():
    return {"service": "chatbot", "status": "healthy"}