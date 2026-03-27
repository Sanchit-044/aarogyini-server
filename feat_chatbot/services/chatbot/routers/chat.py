"""
Aarogyini Chatbot - Chat Router
FastAPI routes for the chat API.
"""

from fastapi import APIRouter, HTTPException, Depends
from models import ChatRequest, ChatResponse, UserHealthProfile
from chatbot import AarogyiniChatbot
from typing import Optional

router = APIRouter()

# Single shared chatbot instance (stateless LLM, stateful memory handled per-session)
chatbot = AarogyiniChatbot()


def get_chatbot() -> AarogyiniChatbot:
    return chatbot


@router.post("/message", response_model=ChatResponse)
async def send_message(
        request: ChatRequest,
        bot: AarogyiniChatbot = Depends(get_chatbot),
):
    """
    Send a message to Aarogyini and receive a health-informed response.

    - Fetches user profile (stub — replace with real DB call)
    - Runs rule engine on profile
    - Sends to LLM with context
    - Returns structured response
    """
    # TODO: Replace with real DB fetch using request.user_id
    # profile = await db.get_user_profile(request.user_id)
    profile: Optional[UserHealthProfile] = None  # Set to None if no profile

    try:
        result = await bot.chat(
            user_message=request.message,
            session_id=request.session_id,
            profile=profile,
            history=request.history,
        )
        return ChatResponse(
            session_id=request.session_id,
            **result,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chatbot error: {str(e)}")


@router.delete("/session/{session_id}")
def clear_session(session_id: str, bot: AarogyiniChatbot = Depends(get_chatbot)):
    """Clear conversation memory for a session."""
    from chatbot import memory_store
    memory_store.clear(session_id)
    return {"message": f"Session {session_id} cleared."}