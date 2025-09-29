"""Mock OpenAI service to avoid dependency issues"""

class MockOpenAIService:
    def __init__(self):
        self.client = None
        self.model = "gpt-4o"
        print("✅ Mock OpenAI service initialized")

    def analyze_whiteboard_and_speech(self, image_data: str, user_speech: str = "") -> str:
        return "Mock analysis: This appears to be a technical diagram. The approach looks reasonable, but consider adding more detailed calculations."

    def analyze_practice_answer(self, user_answer: str, question_text: str, model_answer: str, image_data: str = None) -> str:
        return "Mock feedback: Your answer demonstrates good understanding of the key concepts. Consider providing more specific examples to strengthen your response."

    def test_connection(self) -> bool:
        return True
