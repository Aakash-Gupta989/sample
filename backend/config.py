import os
from dotenv import load_dotenv

# Load environment variables from the project root, overriding any pre-set env vars
load_dotenv(dotenv_path="../.env", override=True)
print(f"🔧 Loading .env from: ../.env")
print(f"🔧 GROQ_API_KEY loaded: {os.getenv('GROQ_API_KEY', 'NOT_FOUND')[:20]}...")

class Config:
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # Remove hardcoded fallback - use env variable only

    # OpenAI Configuration (for image analysis fallback)
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
    
    # Groq Configuration (Default AI Model)
    GROQ_MODEL = "meta-llama/llama-4-maverick-17b-128e-instruct"  # Groq's current supported model

    # Server Configuration
    BACKEND_PORT = int(os.getenv("BACKEND_PORT", 8000))
    FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", 3000))
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        # Allow mock keys for development
        valid_openai = cls.OPENAI_API_KEY and cls.OPENAI_API_KEY not in ["", "your-openai-key-here"]
        valid_groq = cls.GROQ_API_KEY and cls.GROQ_API_KEY not in ["", "your-groq-key-here"]
        
        if not valid_groq:
            print("⚠️ Warning: No valid Groq API key found, using mock services")
        if not valid_openai:
            print("⚠️ Warning: No valid OpenAI API key found, image analysis will use fallback")
        return True
