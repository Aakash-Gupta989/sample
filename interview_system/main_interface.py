"""
Main Interface for Intelligent Interview System
Provides the primary API for frontend integration
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

from .two_phase_conductor import TwoPhaseInterviewConductor, create_legacy_response_format
from .interview_blueprint import blueprint_storage
from .company_qna_handler import CompanyQnAHandler

class InterviewSystemAPI:
    """
    Main API class for the intelligent interview system
    This is the interface that the frontend will interact with
    """
    
    def __init__(self, llm_client):
        # Only using the new two-phase conductor now
        self.two_phase_conductor = TwoPhaseInterviewConductor(llm_client)
        self.active_sessions: Dict[str, Any] = {}
        # Company Q&A handler - separate AI for post-interview questions
        self.company_qna_handler = CompanyQnAHandler(llm_client)
    
    def start_interview_flow(self, candidate_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Start interview and immediately return the greeting message
        This is what your frontend should call
        
        Returns:
            {
                'session_id': str,
                'message': str,  # The greeting message to display
                'message_type': 'greeting',
                'next_action': 'collect_introduction',
                'prompt': str,  # The first question/prompt
                'status': 'greeting_shown',
                'interview_info': dict,
                'two_phase_system': bool  # True for technical+behavioral
            }
        """
        
        try:
            # Handle both camelCase (frontend) and snake_case (backend) formats
            interview_type = candidate_inputs.get('interview_type') or candidate_inputs.get('interviewType', 'technical_behavioral')
            
            # Normalize the interview type (same logic as backend/main.py)
            if interview_type:
                interview_type_normalized = interview_type.lower().strip()
                type_mapping = {
                    "technical": "technical_only",
                    "behavioral": "behavioral_only", 
                    "behavioral + technical": "technical_behavioral",
                    "behavioral+technical": "technical_behavioral",
                    "technical + behavioral": "technical_behavioral",
                    "technical+behavioral": "technical_behavioral",
                    "technical_only": "technical_only",
                    "behavioral_only": "behavioral_only",
                    "technical_behavioral": "technical_behavioral"
                }
                interview_type = type_mapping.get(interview_type_normalized, "technical_behavioral")
            
            # Route ALL interview types through the AI Conductor system
            print(f"🚀 Using NEW Two-Phase System for {interview_type} interview")
            
            # Update candidate_inputs with normalized interview_type
            candidate_inputs_normalized = candidate_inputs.copy()
            candidate_inputs_normalized['interview_type'] = interview_type
            
            # Use the new two-phase system for all interview types
            result = self.two_phase_conductor.create_interview_session(candidate_inputs_normalized)
            
            if result.get('status') == 'error':
                return result
            
            # Convert to the expected frontend format with Sarah as interviewer
            # Use the AI Conductor's type-specific greeting instead of hardcoded message
            return {
                'session_id': result['session_id'],
                'message': result['first_question'],  # This contains the type-specific greeting from AI Conductor
                'message_type': 'greeting',
                'next_action': 'collect_introduction',
                'prompt': result['first_question'],
                'status': 'greeting_shown',
                'interview_info': result.get('interview_info', {}),
                'two_phase_system': True  # Flag to indicate this is using the new system
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f"Failed to start interview: {str(e)}"
            }
    
    def submit_introduction(self, session_id: str, introduction_text: str) -> Dict[str, Any]:
        """
        Submit the candidate's introduction and get the first question using AI Conductor
        
        Returns:
            {
                'session_id': str,
                'message': str,  # The first question
                'message_type': 'question',
                'next_action': 'collect_answer',
                'status': 'question_ready'
            }
        """
        
        try:
            # All interview types now use the AI Conductor system
            ai_conductor_result = self.two_phase_conductor.process_candidate_response(
                session_id, introduction_text
            )
            # Convert to legacy response format for frontend compatibility
            return create_legacy_response_format(ai_conductor_result)
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f"Failed to process introduction: {str(e)}"
            }
    
    def get_next_question(self, session_id: str) -> Dict[str, Any]:
        """
        Get the current interview status - with AI Conductor, questions flow conversationally
        
        Returns:
            {
                'status': 'active' | 'completed' | 'error',
                'message': str,
                'session_info': dict
            }
        """
        
        try:
            # All interview types now use the AI Conductor system
            status_info = self.two_phase_conductor.get_interview_status(session_id)
            
            if status_info.get('status') == 'active':
                # Get the last AI message directly from storage
                last_ai_message = self.two_phase_conductor.last_ai_messages.get(
                    session_id,
                    "Interview is in progress. Continue the conversation."
                )
                
                # Return both legacy 'message' and structured 'question' so
                # the frontend can treat this as a proper question
                return {
                    'status': 'active',
                    'next_action': 'continue_conversation',
                    'message': last_ai_message,  # legacy/compat
                    'question': {
                        'id': f"conv_{session_id}",
                        'text': last_ai_message,
                        'question_type': 'conversational'
                    },
                    'session_info': status_info
                }
            else:
                return {
                    'status': 'completed',
                    'message': 'Interview has been completed successfully!'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f"Failed to get next question: {str(e)}"
            }
    
    def submit_answer(self, session_id: str, question_id: str, answer_text: str) -> Dict[str, Any]:
        """
        Submit an answer and get the AI Conductor's response
        
        Returns:
            {
                'status': 'success' | 'completed' | 'error',
                'message': str,  # AI Conductor's next utterance
                'next_action': str,
                'analysis': str,  # AI Conductor's analysis
                'conductor_action': str  # CHALLENGE, DEEPEN, or TRANSITION
            }
        """
        
        try:
            # All interview types now use the AI Conductor system
            ai_conductor_result = self.two_phase_conductor.process_candidate_response(
                session_id, answer_text
            )
            
            # Return the AI Conductor result directly (it's already in the right format)
            if ai_conductor_result.get('status') == 'error':
                return ai_conductor_result
            
            # Map AI Conductor response to frontend expectations
            if ai_conductor_result.get('next_action') == 'interview_complete':
                # Interview is complete - trigger company Q&A mode
                return {
                    'status': 'success',
                    'next_action': 'start_company_qna',
                    'message': ai_conductor_result.get('message', 'Interview completed'),
                    'analysis': ai_conductor_result.get('analysis', ''),
                    'conductor_action': ai_conductor_result.get('conductor_action', 'TRANSITION'),
                    'progress': ai_conductor_result.get('progress', {'percentage': 100, 'status': 'completed'})
                }
            else:
                return {
                    'status': 'success',
                    'next_action': 'continue_conversation',
                    'message': ai_conductor_result.get('question', 'Please continue.'),
                    'analysis': ai_conductor_result.get('analysis', ''),
                    'conductor_action': ai_conductor_result.get('conductor_action', 'CHALLENGE'),
                    'progress': ai_conductor_result.get('progress', {})
                }
                
        except Exception as e:
                return {
                    'status': 'error',
                    'message': f"Failed to submit answer: {str(e)}"
                }

    def start_company_qna(self, session_id: str) -> Dict[str, Any]:
        """
        Start the company Q&A phase after interview completion.
        
        Returns:
            {
                'status': 'success' | 'error',
                'message': str,
                'next_action': 'company_qna_active',
                'questions_remaining': int
            }
        """
        return self.company_qna_handler.start_company_qna(session_id)
    
    def submit_company_question(self, session_id: str, user_response: str) -> Dict[str, Any]:
        """
        Submit user's response/question in company Q&A mode.
        
        Returns:
            {
                'status': 'success' | 'completed' | 'error',
                'message': str,
                'next_action': str,
                'questions_remaining': int
            }
        """
        return self.company_qna_handler.process_company_response(session_id, user_response)
    
    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """Get information about a session including conversation status"""
        
        try:
            # All interview types now use the AI Conductor system
            status_info = self.two_phase_conductor.get_interview_status(session_id)
            blueprint_summary = self.two_phase_conductor.get_blueprint_summary(session_id)
            
            # Get the interview type from the blueprint
            blueprint = blueprint_storage.get_blueprint(session_id)
            interview_type = getattr(blueprint, 'interview_type', 'technical_behavioral') if blueprint else 'technical_behavioral'
            
            return {
                'session_id': session_id,
                'system_type': 'ai_conductor',
                'interview_type': interview_type,
                'status': status_info.get('status', 'active'),
                'progress': status_info.get('progress', {}),
                'conversation_length': status_info.get('conversation_length', 0),
                'blueprint_summary': blueprint_summary
            }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f"Failed to get session info: {str(e)}"
            }
