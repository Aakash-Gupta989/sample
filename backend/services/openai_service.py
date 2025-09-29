import os
import json
import requests
import base64
import re
from typing import Optional, Dict, Any
from config import Config

class OpenAIService:
    """
    OpenAI GPT-4o service for image and text analysis
    Rewritten from scratch with proper base64 handling
    """
    
    def __init__(self):
        self.api_key = Config.OPENAI_API_KEY
        self.base_url = "https://api.openai.com/v1/chat/completions"
        self.model = "gpt-4o"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Add client attribute for compatibility with main.py health check
        self.client = self.api_key and self.api_key not in ["", "your-openai-key-here"]
        
        # Test connection on initialization
        print(f"🔧 Initializing OpenAI service...")
        if self.client:
            print(f"✅ OpenAI API key found: {self.api_key[:10]}...")
        else:
            print("⚠️ No valid OpenAI API key found")
    
    def test_connection(self) -> bool:
        """Test OpenAI API connection"""
        if not self.api_key or self.api_key in ["", "your-openai-key-here"]:
            print("❌ OpenAI: No valid API key")
            return False
            
        try:
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 5
            }
            
            response = requests.post(self.base_url, headers=self.headers, json=payload, timeout=10)
            success = response.status_code == 200
            
            if success:
                print("✅ OpenAI API connection successful")
            else:
                print(f"❌ OpenAI API connection failed: {response.status_code} - {response.text}")
                
            return success
            
        except Exception as e:
            print(f"❌ OpenAI API connection error: {e}")
            return False
    
    def _clean_base64_image(self, image_data: str) -> str:
        """
        Clean and validate base64 image data
        Handles both data URLs and raw base64 strings
        """
        try:
            # Remove data URL prefix if present
            if image_data.startswith('data:'):
                # Extract just the base64 part after the comma
                if ',' in image_data:
                    image_data = image_data.split(',', 1)[1]
                else:
                    # Malformed data URL
                    raise ValueError("Malformed data URL - missing comma")
            
            # Remove any whitespace/newlines
            image_data = re.sub(r'\s+', '', image_data)
            
            # Validate base64 by trying to decode it
            try:
                decoded = base64.b64decode(image_data)
                if len(decoded) == 0:
                    raise ValueError("Empty decoded data")
                print(f"✅ Valid base64 image: {len(decoded)} bytes")
                return image_data
            except Exception as decode_error:
                raise ValueError(f"Invalid base64 data: {decode_error}")
                
        except Exception as e:
            print(f"❌ Base64 cleaning error: {e}")
            raise ValueError(f"Failed to clean base64 image: {e}")
    
    def analyze_whiteboard_and_speech(self, image_data: str, user_speech: str = "") -> str:
        """
        Analyze whiteboard image with optional speech context using GPT-4o
        """
        try:
            if not self.api_key or self.api_key in ["", "your-openai-key-here"]:
                return "OpenAI service not available - no API key configured"
            
            # Clean the base64 image data
            clean_image_data = self._clean_base64_image(image_data)
            
            # Build the message content
            content = [
                {
                    "type": "text",
                    "text": f"""Analyze this whiteboard drawing and provide helpful feedback.

User Context: {user_speech if user_speech else "User submitted drawing for analysis"}

Please:
1. Describe what you see in the image
2. Identify any text, diagrams, equations, or concepts
3. Provide constructive feedback on the approach
4. Suggest improvements or corrections if needed
5. Offer relevant educational guidance

Be encouraging and focus on helping the user learn."""
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{clean_image_data}",
                        "detail": "high"
                    }
                }
            ]
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                "max_tokens": 1500,
                "temperature": 0.7
            }
            
            print(f"🔍 Sending OpenAI request...")
            response = requests.post(self.base_url, headers=self.headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                analysis = result['choices'][0]['message']['content']
                print(f"✅ OpenAI analysis successful: {len(analysis)} chars")
                return analysis
            else:
                error_msg = f"OpenAI API error {response.status_code}: {response.text}"
                print(f"❌ {error_msg}")
                return f"Sorry, I encountered an error analyzing your image. Please try again. (Error: {response.status_code})"
                
        except ValueError as ve:
            # Base64 specific errors
            error_msg = f"Image format error: {ve}"
            print(f"❌ {error_msg}")
            return "Sorry, there was an issue with the image format. Please try drawing again and resubmitting."
            
        except Exception as e:
            error_msg = f"OpenAI analysis error: {e}"
            print(f"❌ {error_msg}")
            return "Sorry, I encountered an error analyzing your image. Please try again."
    
    def analyze_practice_answer(self, user_answer: str, question_text: str, model_answer: str = "", image_data: str = "") -> str:
        """
        Analyze practice answer with optional image context
        """
        try:
            if not self.api_key or self.api_key in ["", "your-openai-key-here"]:
                return "OpenAI service not available - no API key configured"
            
            # Build content based on whether image is provided
            if image_data:
                # Clean the base64 image data
                clean_image_data = self._clean_base64_image(image_data)
                
                content = [
                    {
                        "type": "text",
                        "text": f"""Analyze this practice answer with both text and visual components.

QUESTION: {question_text}

USER'S TEXT ANSWER: {user_answer}

MODEL ANSWER (for reference): {model_answer if model_answer else "No model answer provided"}

Please analyze both the text response and the drawing/diagram, then provide:
1. Assessment of the written explanation
2. Analysis of the visual components (diagrams, calculations, etc.)
3. How well the text and visuals work together
4. Specific feedback on accuracy and approach
5. Suggestions for improvement

Be constructive and educational in your feedback."""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{clean_image_data}",
                            "detail": "high"
                        }
                    }
                ]
            else:
                # Text-only analysis
                content = [
                    {
                        "type": "text",
                        "text": f"""Analyze this practice answer.

QUESTION: {question_text}

USER'S ANSWER: {user_answer}

MODEL ANSWER (for reference): {model_answer if model_answer else "No model answer provided"}

Please provide:
1. Assessment of the answer's accuracy and completeness
2. Strengths in the response
3. Areas for improvement
4. Specific suggestions to enhance understanding

Be constructive and educational in your feedback."""
                    }
                ]
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                "max_tokens": 800,
                "temperature": 0.3
            }
            
            print(f"🔍 Sending OpenAI practice analysis request...")
            response = requests.post(self.base_url, headers=self.headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                analysis = result['choices'][0]['message']['content']
                print(f"✅ OpenAI practice analysis successful: {len(analysis)} chars")
                return analysis
            else:
                error_msg = f"OpenAI API error {response.status_code}: {response.text}"
                print(f"❌ {error_msg}")
                return f"Sorry, I encountered an error analyzing your answer. Please try again. (Error: {response.status_code})"
                
        except ValueError as ve:
            # Base64 specific errors
            error_msg = f"Image format error: {ve}"
            print(f"❌ {error_msg}")
            return "Sorry, there was an issue with the image format. Please try again."
            
        except Exception as e:
            error_msg = f"OpenAI analysis error: {e}"
            print(f"❌ {error_msg}")
            return "Sorry, I encountered an error analyzing your answer. Please try again."
