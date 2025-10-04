# Lightweight models without pydantic for Render free tier
from typing import List, Dict, Optional
from datetime import datetime

class WhiteboardAnalysisRequest:
    def __init__(self, image_data: str, user_speech: str = "", ai_model: str = "gpt4o", timestamp: datetime = None):
        self.image_data = image_data
        self.user_speech = user_speech
        self.ai_model = ai_model
        self.timestamp = timestamp or datetime.now()

class ChatMessage:
    def __init__(self, role: str, content: str, timestamp: datetime = None, message_type: str = "text"):
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.now()
        self.message_type = message_type

class AnalysisResponse:
    def __init__(self, visual_analysis: str, ai_response: str, timestamp: datetime = None, success: bool = True, error: str = None):
        self.visual_analysis = visual_analysis
        self.ai_response = ai_response
        self.timestamp = timestamp or datetime.now()
        self.success = success
        self.error = error

class SessionState:
    def __init__(self, session_id: str, conversation_history: List[ChatMessage] = None, created_at: datetime = None, last_activity: datetime = None):
        self.session_id = session_id
        self.conversation_history = conversation_history or []
        self.created_at = created_at or datetime.now()
        self.last_activity = last_activity or datetime.now()