"""
NyayaShastra - Chat Service
Handles chat session management and message persistence.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import logging

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ChatService:
    """Service for managing chat sessions and messages."""
    
    def __init__(self):
        """Initialize the chat service."""
        pass
    
    def get_or_create_session(
        self, 
        db: Session, 
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        language: str = "en",
        domain: Optional[str] = "all"
    ) -> "ChatSession":
        """Get existing session or create a new one."""
        from app.models import ChatSession
        
        if session_id:
            # Try to find existing session
            session = db.query(ChatSession).filter(
                ChatSession.session_id == session_id
            ).first()
            
            if session:
                # Update last activity and domain if it changed from 'all'
                session.last_activity = datetime.now()
                if domain and domain != "all" and session.domain == "all":
                    session.domain = domain
                db.commit()
                return session
        
        # Create new session
        new_session_id = session_id or str(uuid.uuid4())
        session = ChatSession(
            session_id=new_session_id,
            user_id=user_id,
            language=language,
            domain=domain or "all",
            started_at=datetime.now(),
            last_activity=datetime.now()
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        
        logger.info(f"Created new chat session: {new_session_id} in domain: {domain}")
        return session
    
    def save_message(
        self,
        db: Session,
        session_id: str,
        role: str,
        content: str,
        content_hi: Optional[str] = None,
        citations: Optional[List[Dict]] = None,
        agent_path: Optional[List[str]] = None,
        statutes_referenced: Optional[List[int]] = None
    ) -> "ChatMessage":
        """Save a message to the database."""
        from app.models import ChatSession, ChatMessage
        
        # Get session
        session = db.query(ChatSession).filter(
            ChatSession.session_id == session_id
        ).first()
        
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        # Create message
        message = ChatMessage(
            session_id=session.id,
            role=role,
            content=content,
            content_hi=content_hi,
            citations=citations,
            agent_path=agent_path,
            statutes_referenced=statutes_referenced,
            created_at=datetime.now()
        )
        db.add(message)
        
        # Update session last activity
        session.last_activity = datetime.now()
        
        db.commit()
        db.refresh(message)
        
        logger.info(f"Saved {role} message to session {session_id}")
        return message
    
    def get_session_messages(
        self,
        db: Session,
        session_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get all messages for a session."""
        from app.models import ChatSession, ChatMessage
        
        session = db.query(ChatSession).filter(
            ChatSession.session_id == session_id
        ).first()
        
        if not session:
            return []
        
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session.id
        ).order_by(ChatMessage.created_at).limit(limit).all()
        
        return [
            {
                "id": str(msg.id),
                "role": msg.role,
                "content": msg.content,
                "content_hi": msg.content_hi,
                "citations": msg.citations or [],
                "timestamp": msg.created_at.isoformat() if msg.created_at else None
            }
            for msg in messages
        ]
    
    def get_user_sessions(
        self,
        db: Session,
        user_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get all sessions for a user."""
        from app.models import ChatSession, ChatMessage
        from sqlalchemy import desc, func
        
        sessions = db.query(ChatSession).filter(
            ChatSession.user_id == user_id
        ).order_by(desc(ChatSession.last_activity)).limit(limit).all()
        
        result = []
        for session in sessions:
            # Get message count
            msg_count = db.query(func.count(ChatMessage.id)).filter(
                ChatMessage.session_id == session.id
            ).scalar()
            
            # Get first user message as title
            first_msg = db.query(ChatMessage).filter(
                ChatMessage.session_id == session.id,
                ChatMessage.role == "user"
            ).first()
            
            title = "New Chat"
            if first_msg:
                title = first_msg.content[:50] + "..." if len(first_msg.content) > 50 else first_msg.content
            
            # Format date
            date_str = self._format_date(session.last_activity)
            
            result.append({
                "id": session.session_id,
                "title": title,
                "date": date_str,
                "messageCount": msg_count,
                "language": session.language or "en",
                "domain": session.domain or "all"
            })
        
        return result
    
    def delete_session(self, db: Session, session_id: str) -> bool:
        """Delete a session and all its messages."""
        from app.models import ChatSession, ChatMessage
        
        session = db.query(ChatSession).filter(
            ChatSession.session_id == session_id
        ).first()
        
        if not session:
            return False
        
        # Delete messages first
        db.query(ChatMessage).filter(
            ChatMessage.session_id == session.id
        ).delete()
        
        # Delete session
        db.delete(session)
        db.commit()
        
        logger.info(f"Deleted session: {session_id}")
        return True
    
    def _format_date(self, dt: Optional[datetime]) -> str:
        """Format datetime to human-readable string."""
        if not dt:
            return "Unknown"
        
        from datetime import timedelta
        now = datetime.now()
        diff = now - dt
        
        if diff < timedelta(minutes=1):
            return "Just now"
        elif diff < timedelta(hours=1):
            mins = int(diff.seconds / 60)
            return f"{mins} minute{'s' if mins != 1 else ''} ago"
        elif diff < timedelta(days=1):
            hours = int(diff.seconds / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff < timedelta(days=7):
            return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        else:
            return dt.strftime("%b %d")


# Singleton instance
_chat_service: Optional[ChatService] = None


def get_chat_service() -> ChatService:
    """Get the chat service singleton."""
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service
