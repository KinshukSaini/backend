from fastapi import APIRouter, Request, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from ..services.session_manager import SessionManager

router = APIRouter()

class MessageModel(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    message_id: str

# Simple auth dependency - adapt to your Supabase setup
async def get_current_user_id(request: Request) -> str:
    return "test_user_123"

@router.post("/chat", response_model=ChatResponse)
async def chat_with_session(
    req: ChatRequest,
    request: Request,
    user_id: str = Depends(get_current_user_id)
):
    try:
        # Get services from app state
        chatbot = request.app.state.chatbot
        session_manager = request.app.state.session_manager  # Use app state
        
        # Handle session
        if req.session_id:
            session = await session_manager.get_session(req.session_id, user_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            session_id = req.session_id
        else:
            # Create new session with title from first message
            title = req.message[:50] + "..." if len(req.message) > 50 else req.message
            session_id = await session_manager.create_session(user_id, title)
        
        # Get conversation history
        history = await session_manager.get_session_history(session_id, limit=20)
        conversation_history = [
            {"role": msg.role, "content": msg.content} 
            for msg in history
        ]
        
        # Store user message
        await session_manager.add_message(session_id, req.message, "user")
        
        # Generate response with history
        reply = chatbot.process_query_with_history(req.message, conversation_history)
        
        # Store assistant response
        message_id = await session_manager.add_message(session_id, reply, "assistant")
        
        return ChatResponse(
            response=reply,
            session_id=session_id,
            message_id=message_id
        )
        
    except Exception as e:
        print(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions")
async def get_user_sessions(
    request: Request,
    user_id: str = Depends(get_current_user_id)
):
    """Get all sessions for user"""
    try:
        session_manager = request.app.state.session_manager  # ✅ Use app state
        sessions = await session_manager.get_user_sessions(user_id)
        
        return {"sessions": [
            {
                "id": session.id,
                "title": session.title,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat()
            }
            for session in sessions
        ]}
    except Exception as e:
        print(f"Sessions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
