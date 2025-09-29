import base64
import json
from groq import Groq
from config import Config

class GroqService:
    def __init__(self):
        self.client = None
        if Config.GROQ_API_KEY:
            try:
                self.client = Groq(api_key=Config.GROQ_API_KEY)
                print("✅ Groq client initialized successfully")
            except Exception as e:
                print(f"❌ Failed to initialize Groq client: {e}")
                self.client = None
    
    def test_connection(self):
        """Test Groq API connection"""
        if not self.client:
            return False
        
        try:
            # Simple test message
            response = self.client.chat.completions.create(
                model="meta-llama/llama-4-maverick-17b-128e-instruct",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            return bool(response.choices[0].message.content)
        except Exception as e:
            print(f"❌ Groq connection test failed: {e}")
            return False
    
    def analyze_whiteboard_and_speech(self, image_data, user_speech=""):
        """Analyze whiteboard drawing with speech using Groq's multimodal model"""
        if not self.client:
            return "Groq service is not available. Please check your API key."
        
        try:
            # Prepare the message content
            messages = []
            
            # System message for interview context
            system_message = {
                "role": "system",
                "content": """You are an expert AI interviewer conducting technical interviews. 
                Analyze the whiteboard drawing and user's speech to provide insightful follow-up questions 
                and feedback. Focus on system design, problem-solving approach, and technical depth."""
            }
            messages.append(system_message)
            
            # User message with image and text
            user_content = []
            
            if user_speech:
                user_content.append({
                    "type": "text",
                    "text": f"User said: {user_speech}"
                })
            
            if image_data and image_data.startswith('data:image'):
                # Extract base64 data
                base64_data = image_data.split(',')[1]
                user_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": image_data
                    }
                })
            
            if not user_content:
                user_content.append({
                    "type": "text", 
                    "text": "Please provide feedback on the current discussion."
                })
            
            messages.append({
                "role": "user",
                "content": user_content
            })
            
            # Make API call to Groq
            response = self.client.chat.completions.create(
                model="meta-llama/llama-4-maverick-17b-128e-instruct",
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"❌ Groq analysis error: {e}")
            return f"I apologize, but I encountered an error analyzing your response with Groq: {str(e)}. Please try again."
    
    def generate_response(self, prompt: str, temperature: float = 0.1, max_tokens: int = 2000) -> str:
        """Generate response using Groq API - interface method for interview system"""
        if not self.client:
            raise Exception("Groq service is not available. Please check your API key.")
        
        try:
            response = self.client.chat.completions.create(
                model="meta-llama/llama-4-maverick-17b-128e-instruct",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"❌ Groq generate_response error: {e}")
            raise Exception(f"Groq API call failed: {str(e)}")
    
    def generate_interview_question(self, domain="system_design", difficulty="medium", form_data=None):
        """Generate interview questions using Groq"""
        if not self.client:
            return {
                "question_text": "Groq service is not available. Please check your configuration.",
                "initial_diagram": None,
                "scenario": "Service unavailable",
                "evaluation_criteria": []
            }
        
        try:
            # Build context from form data
            context = ""
            if form_data:
                context = f"""
                Candidate: {form_data.get('firstName', '')} {form_data.get('lastName', '')}
                Position: {form_data.get('position', '')}
                Company: {form_data.get('company', '')}
                Interview Type: {form_data.get('interviewType', '')}
                """
                
                if form_data.get('jobDescription'):
                    context += f"Job Description: {form_data.get('jobDescription')[:500]}..."
                
                if form_data.get('interviewerLinkedIn'):
                    context += f"Interviewer Profile: {form_data.get('interviewerLinkedIn')[:300]}..."

                # Add previously asked list to discourage repeats
                asked = form_data.get('asked', [])
                if asked:
                    context += f"\nAlready asked (avoid repeating or paraphrasing): {asked[:5]}"
            
            prompt = f"""
You are conducting a technical interview.
Goal: Generate ONE conversational technical question for the candidate.

Context:
{context}

Instructions:
- Return ONLY the question text. No preface, no labels, no bullets, no headings, no follow-ups, no evaluation.
- Exactly one question, 1-2 sentences max.
- Make it job-specific and include concrete constraints from the description when possible (e.g., power, thickness, IP rating, drop height, materials).
- Keep it concise and conversational, like an interviewer speaking.
"""
            
            response = self.client.chat.completions.create(
                model="meta-llama/llama-4-maverick-17b-128e-instruct",
                messages=[
                    {"role": "system", "content": "You are an expert technical interviewer. Respond with only the question text."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=80,
                temperature=0.6
            )
            
            question_text = response.choices[0].message.content
            # Sanitize to enforce single concise question
            try:
                import re
                qt = question_text.strip()
                # Strip common labels/prefixes
                qt = re.sub(r"^\*\*?\s*question\s*:\s*\*\*?\s*", "", qt, flags=re.IGNORECASE)
                qt = re.sub(r"^question\s*:\s*", "", qt, flags=re.IGNORECASE)
                qt = re.sub(r"^here'?s\s+.*?:\s*", "", qt, flags=re.IGNORECASE)
                # Cut at headings if present
                for header in ["Whiteboard", "Follow-up", "Follow up", "Evaluation", "Evaluation Criteria", "Discussion"]:
                    idx = qt.lower().find(header.lower())
                    if idx != -1:
                        qt = qt[:idx].strip()
                # Keep only the first sentence
                parts = re.split(r"(?<=[.!?])\s+", qt)
                if parts:
                    qt = parts[0].strip()
                question_text = qt
            except Exception:
                pass
            
            return {
                "question_text": question_text,
                "initial_diagram": None,
                "scenario": f"{difficulty.title()} {domain.replace('_', ' ').title()} Question",
                "evaluation_criteria": [
                    "Problem understanding",
                    "System design approach", 
                    "Technical depth",
                    "Communication clarity"
                ]
            }
            
        except Exception as e:
            print(f"❌ Groq question generation error: {e}")
            return {
                "question_text": f"Let's discuss how you would design a scalable system for {form_data.get('company', 'a major tech company') if form_data else 'a major tech company'}. What would be your approach?",
                "initial_diagram": None,
                "scenario": "Fallback Question",
                "evaluation_criteria": ["Problem solving", "System thinking"]
            }
