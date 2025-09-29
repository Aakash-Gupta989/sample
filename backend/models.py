from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

class WhiteboardAnalysisRequest(BaseModel):
    image_data: str  # Base64 encoded image
    user_speech: Optional[str] = ""
    ai_model: Optional[str] = "gpt4o"
    timestamp: Optional[datetime] = None

class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    message_type: Optional[str] = "text"  # 'text', 'image', 'audio'

class AnalysisResponse(BaseModel):
    visual_analysis: str
    ai_response: str
    timestamp: datetime
    success: bool
    error: Optional[str] = None

class SessionState(BaseModel):
    session_id: str
    conversation_history: List[ChatMessage] = []
    created_at: datetime
    last_activity: datetime