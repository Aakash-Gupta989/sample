import io
import tempfile
from typing import Optional

class WhisperService:
    """Lightweight Whisper service for Render free tier - uses OpenAI API instead of local model"""
    
    def __init__(self):
        self.model = None
        self.model_size = "openai-api"  # Using OpenAI API instead of local model
        self.openai_client = None
        self._initialize_openai()
    
    def _initialize_openai(self):
        """Initialize OpenAI client for Whisper API"""
        try:
            from openai import OpenAI
            import os
            
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key and api_key not in ["", "your-openai-key-here"]:
                self.openai_client = OpenAI(api_key=api_key)
                print("✅ OpenAI Whisper API client initialized")
            else:
                print("⚠️ No OpenAI API key found, Whisper service disabled")
                self.openai_client = None
        except Exception as e:
            print(f"❌ Failed to initialize OpenAI client: {e}")
            self.openai_client = None
    
    def transcribe_audio(self, audio_data: bytes, language: Optional[str] = None) -> str:
        """
        Transcribe audio bytes to text using OpenAI Whisper API
        
        Args:
            audio_data: Raw audio bytes (WAV, MP3, etc.)
            language: Optional language code (e.g., 'en', 'es')
        
        Returns:
            Transcribed text string
        """
        if not self.openai_client:
            return "Audio transcription service not available. Please type your response instead."
        
        try:
            # Check if audio data is empty
            if not audio_data or len(audio_data) == 0:
                print("❌ No audio data received")
                return "No audio data received. Please try recording again."
            
            # Create temporary file for audio data
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            print(f"🎤 Transcribing audio file: {temp_file_path} ({len(audio_data)} bytes)")
            
            # Transcribe using OpenAI Whisper API
            with open(temp_file_path, 'rb') as audio_file:
                transcript = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language,
                    response_format="text"
                )
            
            # Clean up temporary file
            import os
            os.unlink(temp_file_path)
            
            transcribed_text = transcript.strip()
            
            if not transcribed_text:
                print("⚠️ Transcription returned empty text")
                return "No speech detected in the audio. Please try speaking louder or closer to the microphone."
            
            print(f"✅ Transcription successful: '{transcribed_text[:50]}{'...' if len(transcribed_text) > 50 else ''}'")
            
            return transcribed_text
            
        except Exception as e:
            print(f"❌ Transcription error: {e}")
            return f"Error transcribing audio: {str(e)}. Please type your response instead."
    
    def transcribe_audio_stream(self, audio_data: bytes) -> dict:
        """
        Transcribe audio and return detailed results
        
        Returns:
            Dict with transcription, confidence, language detection, etc.
        """
        if not self.openai_client:
            return {
                "text": "",
                "success": False,
                "error": "Audio transcription service not available"
            }
        
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            # Transcribe with OpenAI API
            with open(temp_file_path, 'rb') as audio_file:
                transcript = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json"
                )
            
            # Clean up
            import os
            os.unlink(temp_file_path)
            
            return {
                "text": transcript.text.strip(),
                "language": transcript.language,
                "duration": transcript.duration,
                "success": True,
                "confidence": 0.95  # OpenAI Whisper API doesn't provide confidence scores
            }
            
        except Exception as e:
            print(f"❌ Stream transcription error: {e}")
            return {
                "text": "",
                "success": False,
                "error": str(e)
            }
    
    def is_available(self) -> bool:
        """Check if Whisper service is available"""
        return self.openai_client is not None
    
    def get_model_info(self) -> dict:
        """Get information about the loaded model"""
        return {
            "model_size": self.model_size,
            "available": self.is_available(),
            "languages_supported": "multilingual" if self.openai_client else "none",
            "service_type": "openai-api"
        }
