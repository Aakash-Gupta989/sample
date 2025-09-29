"""
Intelligent Interview System for Mechanical Engineering Positions

This system provides AI-powered interview capabilities with:
- Resume and job description analysis
- Skill matching and gap identification  
- Dynamic question generation
- Adaptive interview flow
- Comprehensive assessment and feedback

Main Components:
- TwoPhaseInterviewConductor: New two-phase system for technical+behavioral interviews
- InterviewSystemAPI: Main interface for frontend integration

Usage:
    from interview_system import InterviewSystemAPI
    
    # Initialize with your LLM client
    api = InterviewSystemAPI(llm_client)
    
    # Start interview
    result = api.start_interview_flow(candidate_inputs)
    
    # Submit introduction
    response = api.submit_introduction(session_id, introduction)
    
    # Submit answers
    response = api.submit_answer(session_id, answer)
"""

from .main_interface import InterviewSystemAPI
from .two_phase_conductor import TwoPhaseInterviewConductor
from .interview_blueprint import DataSynthesizer, MasterPromptExecutor, InterviewBlueprint
from .followup_engine import FollowUpEngine, InterviewExecutor

__version__ = "2.0.0"
__author__ = "AI Interview System Team"

__all__ = [
    # Main API
    'InterviewSystemAPI',
    
    # Core Components
    'TwoPhaseInterviewConductor',
    'DataSynthesizer',
    'MasterPromptExecutor', 
    'FollowUpEngine',
    'InterviewExecutor',
    
    # Data Classes
    'InterviewBlueprint'
]