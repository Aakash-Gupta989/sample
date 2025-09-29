import io
import tempfile
import whisper
import numpy as np
from typing import Optional

class WhisperService:
    """Production-ready Whisper service for speech-to-text conversion"""
    
    def __init__(self):
        self.model = None
        self.model_size = "base"  # base, small, medium, large
        self._load_model()
    
    def _load_model(self):
        """Load Whisper model with error handling"""
        try:
            print(f"🔄 Loading Whisper {self.model_size} model...")
            self.model = whisper.load_model(self.model_size)
            print(f"✅ Whisper {self.model_size} model loaded successfully")
        except Exception as e:
            print(f"❌ Failed to load Whisper model: {e}")
            self.model = None
    
    def transcribe_audio(self, audio_data: bytes, language: Optional[str] = None) -> str:
        """
        Transcribe audio bytes to text using Whisper
        
        Args:
            audio_data: Raw audio bytes (WAV, MP3, etc.)
            language: Optional language code (e.g., 'en', 'es')
        
        Returns:
            Transcribed text string
        """
        if not self.model:
            return "Whisper model not available"
        
        try:
            # Check if audio data is empty
            if not audio_data or len(audio_data) == 0:
                print("❌ No audio data received")
                return "No audio data received. Please try recording again."
            
            # Create temporary file for audio data - let Whisper handle format detection
            with tempfile.NamedTemporaryFile(suffix='.audio', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            # Transcribe using Whisper
            print(f"🎤 Transcribing audio file: {temp_file_path} ({len(audio_data)} bytes)")
            
            # Set transcription options
            options = {
                "fp16": False,  # Use fp32 for better compatibility
                "language": language,
                "task": "transcribe",
                "verbose": False  # Reduce output noise
            }
            
            # Remove None values
            options = {k: v for k, v in options.items() if v is not None}
            
            result = self.model.transcribe(temp_file_path, **options)
            
            # Clean up temporary file
            import os
            os.unlink(temp_file_path)
            
            transcribed_text = result["text"].strip()
            
            if not transcribed_text:
                print("⚠️ Transcription returned empty text")
                return "No speech detected in the audio. Please try speaking louder or closer to the microphone."
            
            print(f"✅ Transcription successful: '{transcribed_text[:50]}{'...' if len(transcribed_text) > 50 else ''}'")
            
            return transcribed_text
            
        except Exception as e:
            print(f"❌ Transcription error: {e}")
            return f"Error transcribing audio: {str(e)}"
    
    def transcribe_audio_stream(self, audio_data: bytes) -> dict:
        """
        Transcribe audio and return detailed results
        
        Returns:
            Dict with transcription, confidence, language detection, etc.
        """
        if not self.model:
            return {
                "text": "",
                "success": False,
                "error": "Whisper model not available"
            }
        
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix='.audio', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            # Transcribe with detailed output
            result = self.model.transcribe(
                temp_file_path,
                fp16=False,
                task="transcribe",
                verbose=False
            )
            
            # Clean up
            import os
            os.unlink(temp_file_path)
            
            return {
                "text": result["text"].strip(),
                "language": result.get("language", "unknown"),
                "segments": result.get("segments", []),
                "success": True,
                "confidence": self._calculate_average_confidence(result.get("segments", []))
            }
            
        except Exception as e:
            print(f"❌ Stream transcription error: {e}")
            return {
                "text": "",
                "success": False,
                "error": str(e)
            }
    
    def _calculate_average_confidence(self, segments: list) -> float:
        """Calculate average confidence from segments"""
        if not segments:
            return 0.0
        
        try:
            confidences = []
            for segment in segments:
                if "avg_logprob" in segment:
                    # Convert log probability to confidence (0-1)
                    confidence = np.exp(segment["avg_logprob"])
                    confidences.append(confidence)
            
            return float(np.mean(confidences)) if confidences else 0.0
        except:
            return 0.0
    
    def is_available(self) -> bool:
        """Check if Whisper service is available"""
        return self.model is not None
    
    def get_model_info(self) -> dict:
        """Get information about the loaded model"""
        return {
            "model_size": self.model_size,
            "available": self.is_available(),
            "languages_supported": "multilingual" if self.model else "none"
        }

