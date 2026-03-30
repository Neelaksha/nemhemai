# Auth Routes
import datetime
from fastapi import FastAPI, HTTPException, Depends, Query, Response
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from models import get_db, User, ChatHistory
from auth import get_current_user, verify_password, get_password_hash, create_access_token, require_role
from config import TRIAL_DAYS

# Pydantic Models
class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "user"

class Token(BaseModel):
    access_token: str
    token_type: str

class ChatMessageRequest(BaseModel):
    session_id: str
    prompt: str
    response: str

class ChatMessageResponse(BaseModel):
    id: int
    session_id: str
    prompt: str
    response: str
    timestamp: datetime.datetime

def register_auth_routes(app: FastAPI):
    
    @app.post("/register")
    def register_user(data: RegisterRequest, db=Depends(get_db)):
        if db.query(User).filter(User.username == data.username).first():
            raise HTTPException(status_code=400, detail="Username already registered")
        user = User(
            username=data.username,
            password_hash=get_password_hash(data.password),
            role=data.role,
            created_at=datetime.datetime.utcnow()
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return {"msg": "User registered successfully"}

    @app.post("/login")
    def login(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db), response=None):
        """Authenticate user and set HttpOnly access token cookie for production-safe auth.

        Returns only a success message (token is in HttpOnly cookie, not in response body).
        """
        import os
        from fastapi import Response
        if response is None or not isinstance(response, Response):
            # FastAPI will inject a Response object when declared; ensure we have one
            response = Response()

        user = db.query(User).filter(User.username == form_data.username).first()
        if not user or not verify_password(form_data.password, user.password_hash):
            raise HTTPException(status_code=400, detail="Incorrect username or password")
        access_token = create_access_token(data={"sub": user.username, "role": user.role})

        # Cookie settings: secure flag enabled only in production
        secure_flag = os.getenv('ENV', 'development') == 'production'
        max_age = 60 * 60 * 24 * 7  # 1 week

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=secure_flag,
            samesite="lax",
            max_age=max_age,
            path="/",
        )

        # Return success message only (cookie-only auth)
        return {"msg": "Login successful"}

    @app.get("/me")
    def read_users_me(current_user=Depends(get_current_user)):
        return {"username": current_user.username, "role": current_user.role}

    @app.post("/logout")
    def logout(response: Response, current_user=Depends(get_current_user)):
        """Clear the access_token cookie on logout."""
        response.delete_cookie("access_token", path="/")
        return {"msg": "Logged out"}

    @app.get("/admin-only")
    def admin_only_endpoint(user=Depends(require_role("admin"))):
        return {"msg": f"Hello, admin {user.username}!"}

    @app.post("/history", response_model=ChatMessageResponse)
    def save_chat_message(
        data: ChatMessageRequest,
        db=Depends(get_db),
        current_user=Depends(get_current_user)
    ):
        chat = ChatHistory(
            user_id=current_user.id,
            session_id=data.session_id,
            prompt=data.prompt,
            response=data.response
        )
        db.add(chat)
        db.commit()
        db.refresh(chat)
        return ChatMessageResponse(
            id=getattr(chat, 'id'),
            session_id=getattr(chat, 'session_id'),
            prompt=getattr(chat, 'prompt'),
            response=getattr(chat, 'response'),
            timestamp=getattr(chat, 'timestamp')
        )

    @app.get("/chat-sessions")
    def list_chat_sessions(
        db=Depends(get_db),
        current_user=Depends(get_current_user)
    ):
        """List all chat sessions for the current user with their last message."""
        from sqlalchemy import func
        from typing import List
        
        # Get distinct session_ids with their latest timestamp and message
        subquery = db.query(
            ChatHistory.session_id,
            func.max(ChatHistory.timestamp).label('latest_timestamp')
        ).filter(
            ChatHistory.user_id == current_user.id
        ).group_by(ChatHistory.session_id).subquery()
        
        # Join to get the full record for the latest message in each session
        sessions = db.query(ChatHistory).join(
            subquery,
            (ChatHistory.session_id == subquery.c.session_id) &
            (ChatHistory.timestamp == subquery.c.latest_timestamp)
        ).filter(
            ChatHistory.user_id == current_user.id
        ).order_by(ChatHistory.timestamp.desc()).all()
        
        return [
            {
                "session_id": chat.session_id,
                "last_message": chat.prompt or chat.response or "New Chat",
                "timestamp": chat.timestamp
            }
            for chat in sessions
        ]

    @app.get("/history")
    def get_chat_history(
        session_id: str = Depends(Query(..., description="Session ID to filter chat history")),
        db=Depends(get_db),
        current_user=Depends(get_current_user)
    ):
        from typing import List
        chats = db.query(ChatHistory).filter(
            ChatHistory.user_id == current_user.id, 
            ChatHistory.session_id == session_id
        ).order_by(ChatHistory.timestamp.asc()).all()
        return [
            ChatMessageResponse(
                id=getattr(chat, 'id'),
                session_id=getattr(chat, 'session_id'),
                prompt=getattr(chat, 'prompt'),
                response=getattr(chat, 'response'),
                timestamp=getattr(chat, 'timestamp')
            ) for chat in chats
        ]

    @app.get("/trial-remaining")
    def trial_remaining(current_user=Depends(get_current_user)):
        if not current_user.created_at:
            return {"remaining_seconds": 0}
        expiry_time = current_user.created_at + datetime.timedelta(days=TRIAL_DAYS)
        remaining = int((expiry_time - datetime.datetime.utcnow()).total_seconds())
        if remaining < 0:
            remaining = 0
        return {"remaining_seconds": remaining}