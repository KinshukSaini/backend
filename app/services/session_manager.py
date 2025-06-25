import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class ChatMessage(BaseModel):
    id: str
    session_id: str
    content: str
    role: str
    created_at: datetime

class ChatSession(BaseModel):
    id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    is_active: bool

class SessionManager:
    def __init__(self):
        # In-memory storage for now (replace with database later)
        self.sessions = {}  # session_id -> session_data
        self.user_sessions = {}  # user_id -> [session_ids]
    
    async def create_session(self, user_id: str, title: str = "New Conversation") -> str:
        """Create a new chat session"""
        session_id = str(uuid.uuid4())
        now = datetime.now()
        
        self.sessions[session_id] = {
            'id': session_id,
            'user_id': user_id,
            'title': title,
            'messages': [],
            'created_at': now,
            'updated_at': now,
            'is_active': True
        }
        
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = []
        self.user_sessions[user_id].append(session_id)
        
        return session_id
    
    async def get_session(self, session_id: str, user_id: str):
        """Get session by ID"""
        session = self.sessions.get(session_id)
        if session and session['user_id'] == user_id and session['is_active']:
            return ChatSession(**session)
        return None
    
    async def add_message(self, session_id: str, content: str, role: str) -> str:
        """Add message to session"""
        message_id = str(uuid.uuid4())
        now = datetime.now()
        
        if session_id in self.sessions:
            self.sessions[session_id]['messages'].append({
                'id': message_id,
                'content': content,
                'role': role,
                'created_at': now
            })
            self.sessions[session_id]['updated_at'] = now
        
        return message_id
    
    async def get_session_history(self, session_id: str, limit: int = 20) -> List[ChatMessage]:
        """Get conversation history"""
        if session_id in self.sessions:
            messages = self.sessions[session_id]['messages']
            return [
                ChatMessage(
                    id=msg['id'],
                    session_id=session_id,
                    content=msg['content'],
                    role=msg['role'],
                    created_at=msg['created_at']
                )
                for msg in messages[-limit:]
            ]
        return []
    
    async def get_user_sessions(self, user_id: str, limit: int = 50) -> List[ChatSession]:
        """Get all sessions for user"""
        user_session_ids = self.user_sessions.get(user_id, [])
        sessions = []
        
        for session_id in user_session_ids[-limit:]:
            if session_id in self.sessions:
                session_data = self.sessions[session_id]
                if session_data['is_active']:
                    sessions.append(ChatSession(**session_data))
        
        return sorted(sessions, key=lambda x: x.updated_at, reverse=True)