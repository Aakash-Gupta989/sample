"""
Company Q&A Handler - Separate AI for handling post-interview company questions
"""

import json
import re
from typing import Dict, Any, Optional
from .interview_blueprint import blueprint_storage


class CompanyQnAHandler:
    """
    Dedicated AI handler for company/role questions after the main interview completes.
    This is completely separate from the AI Conductor and has its own specialized prompt.
    """
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
        # Track company Q&A sessions: session_id -> {question_count, company, position, status}
        self.company_sessions: Dict[str, Dict[str, Any]] = {}
        
    def start_company_qna(self, session_id: str) -> Dict[str, Any]:
        """
        Start the company Q&A phase after interview completion.
        
        Returns:
            {
                'status': 'success',
                'message': str,  # The initial company question
                'next_action': 'company_qna_active',
                'questions_remaining': int
            }
        """
        try:
            # Get company and position info from blueprint
            blueprint = blueprint_storage.get_blueprint(session_id)
            if not blueprint:
                return {
                    'status': 'error',
                    'message': 'Session not found'
                }
            
            company = getattr(blueprint, 'company', 'the company')
            position = getattr(blueprint, 'position', 'this role')
            
            # Initialize company Q&A session
            self.company_sessions[session_id] = {
                'question_count': 0,
                'company': company,
                'position': position,
                'status': 'active',
                'max_questions': 3
            }
            
            # Generate the initial company question using AI
            initial_question = self._generate_company_question(session_id, is_initial=True)
            
            return {
                'status': 'success',
                'message': initial_question,
                'next_action': 'company_qna_active',
                'questions_remaining': 3
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to start company Q&A: {str(e)}'
            }
    
    def process_company_response(self, session_id: str, user_response: str) -> Dict[str, Any]:
        """
        Process user's response in company Q&A mode.
        
        Returns:
            {
                'status': 'success' | 'completed' | 'error',
                'message': str,
                'next_action': str,
                'questions_remaining': int
            }
        """
        try:
            if session_id not in self.company_sessions:
                return {
                    'status': 'error',
                    'message': 'Company Q&A session not found'
                }
            
            session = self.company_sessions[session_id]
            
            # Check if user wants to end the Q&A
            if self._user_wants_to_end(user_response):
                # User doesn't want to ask more questions
                del self.company_sessions[session_id]
                return {
                    'status': 'completed',
                    'message': 'Thank you! Your detailed feedback will be ready shortly.',
                    'next_action': 'interview_complete',
                    'questions_remaining': 0
                }
            
            # Increment question count
            session['question_count'] += 1
            
            # Check if we've reached the maximum questions
            if session['question_count'] >= session['max_questions']:
                # Maximum questions reached
                response = self._generate_ai_response(session_id, user_response, is_final=True)
                del self.company_sessions[session_id]
                return {
                    'status': 'completed',
                    'message': response,
                    'next_action': 'interview_complete',
                    'questions_remaining': 0
                }
            
            # Generate AI response and ask if they have more questions
            response = self._generate_ai_response(session_id, user_response, is_final=False)
            
            return {
                'status': 'success',
                'message': response,
                'next_action': 'company_qna_active',
                'questions_remaining': session['max_questions'] - session['question_count']
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to process company response: {str(e)}'
            }
    
    def _generate_company_question(self, session_id: str, is_initial: bool = True) -> str:
        """Generate the initial company question using AI."""
        session = self.company_sessions[session_id]
        company = session['company']
        position = session['position']
        
        if is_initial:
            return f"Thank you for the detailed discussion today. That concludes our interview. Do you have any questions for me or about {company}?"
        else:
            # This shouldn't be called in the current flow, but just in case
            return f"Do you have any other questions about {company} or the {position} role?"
    
    def _generate_ai_response(self, session_id: str, user_question: str, is_final: bool = False) -> str:
        """Generate AI response to user's company question using LLM."""
        session = self.company_sessions[session_id]
        company = session['company']
        position = session['position']
        
        # Create the system prompt for Company Q&A AI
        system_prompt = f"""You are a helpful interviewer at {company} answering candidate questions about the company and the {position} role.

🚨 CRITICAL: DETECT COMPLETION SIGNALS 🚨
Before answering, check if the candidate is indicating they're DONE with questions:

COMPLETION SIGNALS (End conversation immediately):
- "I don't have any more questions" / "No more questions" / "No further questions"
- "That's all" / "That's it" / "That's enough" / "That covers it" / "I think that covers it"
- "I'm good" / "I'm good for now" / "I'm all set" / "I'm satisfied" / "I'm fine"
- "Thank you" (as conclusion) / "Thanks" (as conclusion) / "Thank you for the information"
- "I think I'm done" / "I'm finished" / "That's everything" / "Nothing else"
- Short responses: "OK", "Alright", "Good", "Great", "Perfect"
- Any polite wrap-up language indicating satisfaction

⚠️ WHEN IN DOUBT, ASSUME COMPLETION! Better to end early than annoy with unwanted questions.

RESPONSE RULES:
1. IF COMPLETION DETECTED: Respond ONLY with: "Thank you! Your detailed feedback will be ready shortly."
2. IF NOT COMPLETION: Answer the question + "Do you have any other questions?"

CONTEXT:
- Company: {company}
- Position: {position}
- Question limit: 3 maximum
- {"🔴 FINAL QUESTION - BE EXTRA SENSITIVE!" if is_final else ""}

ANSWER GUIDELINES (only if NOT completion):
- Provide specific, actionable information
- Keep responses concise (2-4 sentences)
- Be encouraging and positive
- Draw from industry knowledge"""

        user_prompt = f"Candidate asked: '{user_question}'"
        
        try:
            # Call the LLM
            print(f"🤖 Calling LLM for company Q&A response...")
            print(f"   Company: {company}, Position: {position}")
            print(f"   User question: {user_question}")
            
            # Use the same LLM client method as AI Conductor
            full_prompt = f"{system_prompt}\n\nUser Question: {user_prompt}\n\nResponse:"
            
            ai_response = self.llm_client.generate_response(
                full_prompt, 
                temperature=0.7, 
                max_tokens=300
            ).strip()
            print(f"   Raw AI response: {ai_response}")
            
            # Ensure proper ending
            if is_final:
                if "feedback will be ready shortly" not in ai_response.lower():
                    ai_response += " Thank you! Your detailed feedback will be ready shortly."
            else:
                if "other questions" not in ai_response.lower():
                    ai_response += " Do you have any other questions?"
            
            print(f"   Final response: {ai_response}")
            return ai_response
            
        except Exception as e:
            print(f"❌ Error generating AI response: {e}")
            import traceback
            traceback.print_exc()
            # Fallback response
            if is_final:
                return f"Thank you for your question about {company}. Your detailed feedback will be ready shortly."
            else:
                return f"Great question! While specific details may vary, I'd be happy to help with general information about {company} and the {position} role. Do you have any other questions?"
    
    def _user_wants_to_end(self, user_response: str) -> bool:
        """Check if user wants to end the Q&A session."""
        response_lower = user_response.lower().strip()
        
        # Common phrases indicating user wants to end
        end_phrases = [
            "no", "nope", "no thanks", "no thank you", "that's all", "that's it",
            "nothing else", "no more", "no more questions", "i'm good", "i'm all set",
            "that covers it", "no further questions", "nothing more", "all good",
            "no other questions", "that's everything", "nothing additional"
        ]
        
        # Check for exact matches or if response is very short and negative
        if response_lower in end_phrases:
            return True
        
        # Check if response is short and contains "no"
        if len(response_lower.split()) <= 3 and "no" in response_lower:
            return True
        
        return False
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get the current status of a company Q&A session."""
        if session_id not in self.company_sessions:
            return {'status': 'not_found'}
        
        session = self.company_sessions[session_id]
        return {
            'status': 'active',
            'question_count': session['question_count'],
            'max_questions': session['max_questions'],
            'questions_remaining': session['max_questions'] - session['question_count'],
            'company': session['company'],
            'position': session['position']
        }
