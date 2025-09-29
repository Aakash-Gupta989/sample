"""
Two-Phase Interview Conductor with AI Conductor System
Orchestrates the complete two-phase interview system for Technical + Behavioral interviews
"""


from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
import json

from .interview_blueprint import (
    DataSynthesizer, MasterPromptExecutor, InterviewBlueprint, 
    blueprint_storage, QuestionType, QuestionObject
)
from .ai_conductor import AIConductor, ConductorAction, ConductorDecision

class TwoPhaseInterviewConductor:
    """
    Main orchestrator for the two-phase interview system with AI Conductor
    Handles both Phase 1 (Blueprint Creation) and Phase 2 (Live Execution with AI Conductor)
    """
    
    def __init__(self, llm_client):
        print("🔍 DEBUG: AI Conductor TwoPhaseInterviewConductor __init__ called!")
        self.llm_client = llm_client
        self.data_synthesizer = DataSynthesizer(llm_client)
        self.master_prompt_executor = MasterPromptExecutor(llm_client)
        self.ai_conductor = AIConductor(llm_client)
        
        # Session storage for conversation transcripts and last AI messages
        self.conversation_transcripts = {}
        self.last_ai_messages = {}  # Store the last AI message for each session
    
    def create_interview_session(self, candidate_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Phase 1: Create interview session with complete blueprint
        
        Args:
            candidate_inputs: Dict containing resume, job_description, position, company, candidate_name
            
        Returns:
            Dict with session_id and initial question
        """
        try:
            print(f"🚀 Starting Phase 1: Pre-Interview Setup")
            
            # Extract inputs
            resume_text = candidate_inputs.get('resume', '')
            job_description = candidate_inputs.get('job_description', '')
            position = candidate_inputs.get('position', 'Software Engineer')
            company = candidate_inputs.get('company', 'TechCorp')
            candidate_name = candidate_inputs.get('candidate_name', 'Candidate')
            interview_type = candidate_inputs.get('interview_type', 'technical_behavioral')
            print(f"🧾 Extracted interview_type from inputs: {interview_type}")
            
            # Step 1: Data Synthesis
            print(f"📊 Step 1: Synthesizing data...")
            synthesized_data = self.data_synthesizer.synthesize_inputs(
                resume_text, job_description, position, company
            )
            
            # Step 2: Master Prompt Execution
            print(f"🎯 Step 2: Creating interview blueprint...")
            blueprint = self.master_prompt_executor.create_interview_blueprint(
                synthesized_data, candidate_name, position, company, interview_type
            )
            
            # Step 3: Store Blueprint and Initialize Conversation
            print(f"💾 Step 3: Storing blueprint and initializing conversation...")
            session_id = blueprint_storage.store_blueprint(blueprint)
            
            # Initialize conversation transcript for this session
            self.conversation_transcripts[session_id] = []
            
            # Get the introduction message from AI Conductor (convert everything to strings)
            serializable_blueprint_intro = {
                'candidate_name': str(blueprint.candidate_name),
                'position': str(blueprint.position),
                'company': str(blueprint.company),
                'key_technical_skills': [str(skill) for skill in (blueprint.key_technical_skills or [])],
                'key_behavioral_competencies': [str(comp) for comp in (blueprint.key_behavioral_competencies or [])],
                'relevant_projects': [str(proj) for proj in (blueprint.relevant_projects or [])],
                'interviewer_directives': [str(directive) for directive in getattr(blueprint, 'interviewer_directives', [])]
            }
            print(f"🗣️ Calling AI Conductor get_interview_introduction with type={interview_type}")
            introduction_message = self.ai_conductor.get_interview_introduction(serializable_blueprint_intro, interview_type)
            
            # Add the introduction to the conversation transcript and store as last message
            self.conversation_transcripts[session_id].append(f"Sarah: {introduction_message}")
            self.last_ai_messages[session_id] = introduction_message
            
            print(f"✅ Phase 1 Complete! Session created: {session_id}")
            
            # Build a lightweight interview_flow summary for visibility in API response
            def _q_to_flow_item(q: QuestionObject) -> Dict[str, Any]:
                try:
                    return {
                        'phase': str(q.context or ''),
                        'question_id': str(q.id or ''),
                        'question_text': str(q.question_text or ''),
                        'intent': str(q.intent or '')
                    }
                except Exception:
                    return {
                        'phase': '', 'question_id': '', 'question_text': '', 'intent': ''
                    }
            interview_flow_summary: List[Dict[str, Any]] = []
            try:
                interview_flow_summary = (
                    [_q_to_flow_item(q) for q in (blueprint.introduction_questions or [])] +
                    [_q_to_flow_item(q) for q in (blueprint.technical_questions or [])] +
                    [_q_to_flow_item(q) for q in (blueprint.behavioral_questions or [])]
                )
            except Exception:
                interview_flow_summary = []

            return {
                'session_id': session_id,
                'status': 'ready',
                'phase': 'introduction',
                'first_question': introduction_message,
                'question_type': 'introduction',
                'interview_info': {
                    'candidate_name': candidate_name,
                    'position': position,
                    'company': company,
                    'interviewer_directives': blueprint.interviewer_directives,
                    'key_focus_areas': {
                        'technical_skills': blueprint.key_technical_skills,
                        'behavioral_competencies': blueprint.key_behavioral_competencies,
                        'relevant_projects': blueprint.relevant_projects
                    },
                    'blueprint': {
                        'interview_plan': {
                            'job_title': position,
                            'company_name': company,
                            'interview_flow': interview_flow_summary
                        }
                    }
                }
            }
            
        except Exception as e:
            print(f"❌ Phase 1 failed: {e}")
            return {
                'status': 'error',
                'message': f'Failed to create interview session: {str(e)}'
            }
    
    def process_candidate_response(self, session_id: str, candidate_answer: str) -> Dict[str, Any]:
        """
        Phase 2: Process candidate response using Three-Layered Architecture
        
        Layer 1: Code-based concession detection (failsafe)
        Layer 2: AI Conductor for nuanced conversation
        Layer 3: Code-based frustration counter (prevents repetitive loops)
        
        Args:
            session_id: The interview session ID
            candidate_answer: The candidate's response
            
        Returns:
            Dict with next action, question (if any), and status
        """
        try:
            print(f"🎤 Processing response for session: {session_id}")
            print(f"🔍 DEBUG: Starting Three-Layer System")
            
            # Get the blueprint
            blueprint = blueprint_storage.get_blueprint(session_id)
            if not blueprint:
                return {
                    'status': 'error',
                    'message': 'Interview session not found'
                }
            
            # Initialize session state if needed
            if session_id not in self.conversation_transcripts:
                self.conversation_transcripts[session_id] = []
            
            # Initialize session tracking for three-layer system
            if not hasattr(self, 'session_state'):
                self.session_state = {}
            if session_id not in self.session_state:
                # Get interview type from blueprint
                blueprint = blueprint_storage.get_blueprint(session_id)
                stored_interview_type = getattr(blueprint, 'interview_type', 'technical_behavioral') if blueprint else 'technical_behavioral'
                print(f"🔍 DEBUG: Initializing session state with interview_type: {stored_interview_type}")
                print(f"🔍 DEBUG: Blueprint interview_type attribute: {getattr(blueprint, 'interview_type', 'NOT_FOUND') if blueprint else 'NO_BLUEPRINT'}")
                
                self.session_state[session_id] = {
                    'current_topic_id': 'intro',
                    'follow_up_count': 0,
                    'visited_topics': {'intro'},  # Mark introduction as visited
                    'last_action': None,
                    'interview_type': stored_interview_type
                }
            
            
            session_state = self.session_state[session_id]
            conversation_transcript = self.conversation_transcripts[session_id]
            
            # Add candidate's answer to transcript
            conversation_transcript.append(f"Candidate: {candidate_answer}")
            
            # LAYER 1: Code-based concession detection (failsafe)
            print(f"🔍 Layer 1: Checking for concessions...")
            if self._detect_concession_failsafe(candidate_answer):
                print(f"✅ Layer 1: Concession detected - taking control")
                return self._handle_concession_pivot(session_id, blueprint, conversation_transcript, session_state)
            
            # LAYER 3: Frustration counter check (before AI Conductor)
            print(f"🔍 Layer 3: Checking frustration counter...")
            if self._should_force_transition(session_state):
                print(f"✅ Layer 3: Forcing transition due to repetitive follow-ups")
                return self._force_topic_transition(session_id, blueprint, conversation_transcript, session_state)
            
            # LAYER 2: AI Conductor for nuanced conversation
            print(f"🔍 Layer 2: AI Conductor analyzing response...")
            try:
                # Reorder technical skills to prioritize non-enclosure topics for better transitions
                original_skills = blueprint.key_technical_skills or []
                enclosure_skills = [s for s in original_skills if "enclosure" in s.lower()]
                other_skills = [s for s in original_skills if "enclosure" not in s.lower()]
                reordered_skills = other_skills + enclosure_skills
                
                serializable_blueprint = {
                    'candidate_name': str(blueprint.candidate_name),
                    'position': str(blueprint.position),
                    'company': str(blueprint.company),
                    'key_technical_skills': [str(skill) for skill in reordered_skills],
                    'key_behavioral_competencies': [str(comp) for comp in (blueprint.key_behavioral_competencies or [])],
                    'relevant_projects': [str(proj) for proj in (blueprint.relevant_projects or [])],
                    'interviewer_directives': [str(directive) for directive in getattr(blueprint, 'interviewer_directives', [])]
                }
                # Test JSON serialization
                json.dumps(serializable_blueprint)
                print(f"✅ Blueprint serialization successful")
            except Exception as e:
                print(f"❌ Blueprint serialization failed: {e}")
                # Create minimal fallback
                serializable_blueprint = {
                    'candidate_name': 'Candidate',
                    'position': 'Engineer',
                    'company': 'Company',
                    'key_technical_skills': ['Technical Skills'],
                    'key_behavioral_competencies': ['Leadership'],
                    'relevant_projects': ['Project Experience'],
                    'interviewer_directives': ['Assess candidate experience']
                }
            
            conductor_decision = self.ai_conductor.conduct_next_turn(
                interview_plan=serializable_blueprint,
                conversation_transcript=conversation_transcript,
                candidate_last_answer=candidate_answer,
                interview_type=session_state.get('interview_type', 'technical_behavioral')
            )
            print(f"🎯 AI Conductor decision: {conductor_decision.chosen_action.value}")
            
            # CRITICAL FIX: Handle TRANSITION and CONCEDE_AND_PIVOT with code-based topic selection
            if conductor_decision.chosen_action.value == 'TRANSITION':
                print(f"🎯 AI Conductor requested TRANSITION - validating transition need")
                
                # Check if we should actually transition or continue on current topic
                follow_up_count = session_state.get('follow_up_count', 0)
                current_topic_id = session_state.get('current_topic_id', 'intro')
                
                # Only transition if we've had sufficient exploration (at least 2 follow-ups) or if forced
                if follow_up_count >= 2 or current_topic_id == 'intro':
                    print(f"🎯 Transition approved - {follow_up_count} follow-ups on {current_topic_id}")
                    return self._handle_ai_conductor_transition(session_id, blueprint, conversation_transcript, session_state, conductor_decision)
                else:
                    print(f"🎯 Transition denied - only {follow_up_count} follow-ups on {current_topic_id}, continuing topic")
                    # Convert TRANSITION to DEEPEN to continue exploring current topic
                    conductor_decision.chosen_action = ConductorAction.DEEPEN
            
            elif conductor_decision.chosen_action.value == 'CONCEDE_AND_PIVOT':
                print(f"🎯 AI Conductor detected CONCEDE_AND_PIVOT - using deterministic topic selection")
                return self._handle_concession_pivot(session_id, blueprint, conversation_transcript, session_state)
            
            # Update session state based on AI Conductor decision
            self._update_session_state(session_state, conductor_decision)
            
            # Add AI Conductor's response to transcript and store as last message
            conversation_transcript.append(f"Sarah: {conductor_decision.next_utterance}")
            self.last_ai_messages[session_id] = conductor_decision.next_utterance
            
            # Update conversation transcript in storage
            self.conversation_transcripts[session_id] = conversation_transcript
            
            # Determine if interview is complete
            is_complete = self._is_interview_complete(conductor_decision, conversation_transcript)
            
            if is_complete:
                print(f"🎉 Interview completed!")
                # Provide a clear closing message instead of echoing the last probe
                try:
                    company_name = str(getattr(blueprint, 'company', 'the company') or 'the company')
                except Exception:
                    company_name = 'the company'
                closing_message = (
                    f"Thank you for the detailed discussion today. That concludes our interview. "
                    f"Do you have any questions for me or about {company_name}?"
                )
                return {
                    'status': 'success',
                    'next_action': 'interview_complete',
                    'message': closing_message,
                    'analysis': conductor_decision.analysis_of_last_answer,
                    'conductor_action': 'TRANSITION',
                    'progress': {'percentage': 100, 'status': 'completed'}
                }
            
            # Calculate progress
            progress = self._calculate_progress(conversation_transcript, blueprint)
            
            print(f"📈 Progress: {progress['percentage']}% complete")
            print(f"🎯 Conductor action: {conductor_decision.chosen_action.value}")
            
            return {
                'status': 'success',
                'next_action': 'continue_conversation',
                'question': conductor_decision.next_utterance,
                'question_type': 'conversational',
                'analysis': conductor_decision.analysis_of_last_answer,
                'conductor_action': conductor_decision.chosen_action.value,
                'progress': progress
            }
            
        except Exception as e:
            print(f"❌ Response processing failed: {e}")
            print(f"🔍 DEBUG: Exception type: {type(e)}")
            import traceback
            print(f"🔍 DEBUG: Full traceback:")
            traceback.print_exc()
            return {
                'status': 'error',
                'message': f'Failed to process response: {str(e)}'
            }
    
    # Three-Layer System Helper Methods
    
    def _detect_concession_failsafe(self, candidate_answer: str) -> bool:
        """
        Layer 1: Code-based concession detection (100% reliable failsafe)
        Returns True if the answer contains a clear concession phrase.
        """
        if not candidate_answer:
            return False
        answer_lower = candidate_answer.lower().strip()
        concession_phrases = [
            # Core concessions
            "i don't know", "i do not know", "dont know", "don't know",
            "not sure", "i'm not sure", "im not sure",
            # Recall/remember variants
            "can't recall", "cannot recall", "cant recall",
            "can't remember", "cannot remember", "cant remember",
            "don't remember", "do not remember", "dont remember",
            # Idea variants
            "no idea", "i have no idea", "have no idea"
        ]
        detected = any(phrase in answer_lower for phrase in concession_phrases)
        if detected:
            print(f"🔍 Layer 1: Concession phrase detected in: '{candidate_answer[:50]}...'")
        return detected
    
    def _should_force_transition(self, session_state: Dict[str, Any]) -> bool:
        """
        Layer 3: Frustration counter - force transition after 3 follow-ups on same topic
        """
        follow_up_count = session_state.get('follow_up_count', 0)
        last_action = session_state.get('last_action')
        
        # Force transition if we've had 3+ follow-ups and last action was CHALLENGE or DEEPEN
        if follow_up_count >= 3 and last_action in ['CHALLENGE', 'DEEPEN']:
            print(f"🔍 Layer 3: Forcing transition - {follow_up_count} follow-ups on current topic")
            return True
        return False
    
    def _handle_concession_pivot(self, session_id: str, blueprint: InterviewBlueprint, 
                                conversation_transcript: List[str], session_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Layer 1: Handle concession by pivoting to next topic
        """
        # Select and immediately mark the next topic as visited (atomic)
        next_topic = self._get_next_unvisited_topic(blueprint, session_state)
        
        if next_topic:
            # Construct graceful transition message
            transition_message = f"No problem, that's completely understandable. Let's move on to a different area then. {next_topic}"
            
            # Reset session state for new topic
            session_state['follow_up_count'] = 0
            session_state['last_action'] = 'CONCEDE_AND_PIVOT'
            
            # Add to transcript and store as last message
            conversation_transcript.append(f"Sarah: {transition_message}")
            self.last_ai_messages[session_id] = transition_message
            self.conversation_transcripts[session_id] = conversation_transcript
            
            progress = self._calculate_progress(conversation_transcript, blueprint)
            
            print(f"✅ Layer 1: Pivoted to next topic")
            
            return {
                'status': 'success',
                'next_action': 'continue_conversation',
                'question': transition_message,
                'question_type': 'conversational',
                'analysis': 'Candidate conceded - pivoted to next topic area',
                'conductor_action': 'CONCEDE_AND_PIVOT',
                'progress': progress
            }
        else:
            # No more topics - complete interview
            completion_message = "Thank you for your time today. That covers all the areas I wanted to discuss. Do you have any questions for me about the role or the company?"
            conversation_transcript.append(f"Sarah: {completion_message}")
            self.conversation_transcripts[session_id] = conversation_transcript
            
            return {
                'status': 'success',
                'next_action': 'interview_complete',
                'message': completion_message,
                'analysis': 'All topics covered - interview complete',
                'conductor_action': 'CONCEDE_AND_PIVOT',
                'progress': {'percentage': 100, 'status': 'completed'}
            }
    
    def _force_topic_transition(self, session_id: str, blueprint: InterviewBlueprint,
                               conversation_transcript: List[str], session_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Layer 3: Force transition to next topic due to repetitive follow-ups
        """
        # Select and immediately mark the next topic as visited (atomic)
        next_topic_question = self._get_next_unvisited_topic(blueprint, session_state)
        
        if next_topic_question:
            # Construct transition message with the actual next question
            transition_message = f"I think we've covered this area well. Let me shift our focus to another important aspect. {next_topic_question}"
            
            # Reset session state for new topic
            session_state['follow_up_count'] = 0
            session_state['last_action'] = 'TRANSITION'
            
            # Add to transcript and store as last message
            conversation_transcript.append(f"Sarah: {transition_message}")
            self.last_ai_messages[session_id] = transition_message
            self.conversation_transcripts[session_id] = conversation_transcript
            
            progress = self._calculate_progress(conversation_transcript, blueprint)
            
            print(f"✅ Layer 3: Forced transition to prevent repetitive loop")
            
            return {
                'status': 'success',
                'next_action': 'continue_conversation',
                'question': transition_message,
                'question_type': 'conversational',
                'analysis': 'Forced transition to prevent repetitive questioning',
                'conductor_action': 'TRANSITION',
                'progress': progress
            }
        else:
            # No more topics - complete interview
            completion_message = "I believe we've covered all the key areas comprehensively. Thank you for the detailed discussion. Do you have any questions for me?"
            conversation_transcript.append(f"Sarah: {completion_message}")
            self.conversation_transcripts[session_id] = conversation_transcript
            
            return {
                'status': 'success',
                'next_action': 'interview_complete',
                'message': completion_message,
                'analysis': 'All topics exhausted - interview complete',
                'conductor_action': 'TRANSITION',
                'progress': {'percentage': 100, 'status': 'completed'}
            }
    
    def _find_next_topic(self, blueprint: InterviewBlueprint, session_state: Dict[str, Any]) -> Optional[str]:
        """
        Find the next logical topic to transition to based on blueprint and session state
        """
        visited_topics = session_state.get('visited_topics', set())
        
        # Create ordered list of all possible topics with their IDs
        # Prioritize diverse topic types for better transitions
        all_topics = []
        
        # First, add the most different technical skills (prioritize non-enclosure topics first)
        if blueprint.key_technical_skills:
            # Separate enclosure and non-enclosure skills with new sequential IDs
            enclosure_skills = []
            other_skills = []
            
            for i, skill in enumerate(blueprint.key_technical_skills[:4]):  # Get top 4
                if "enclosure" in skill.lower():
                    enclosure_skills.append(skill)
                else:
                    other_skills.append(skill)
            
            # Add non-enclosure skills first (for diversity), then enclosure skills
            diverse_skills = other_skills + enclosure_skills
            # Add the diverse technical skills with sequential topic IDs
            for i, skill in enumerate(diverse_skills[:2]):  # Limit to 2
                topic_id = f"tech_{i}"
                question = f"Can you tell me about your experience with {skill}?"
                all_topics.append((topic_id, question))
        
        # Add project-based topics (these provide good variety)
        if blueprint.relevant_projects:
            for i, project in enumerate(blueprint.relevant_projects[:2]):  # Limit to top 2
                topic_id = f"project_{i}"
                project_preview = project[:80] + "..." if len(project) > 80 else project
                all_topics.append((topic_id, f"I'd like to hear more about this project: {project_preview}"))
        
        # Add behavioral topics (good for variety)
        if blueprint.key_behavioral_competencies:
            for i, competency in enumerate(blueprint.key_behavioral_competencies[:2]):  # Limit to top 2
                topic_id = f"behavioral_{i}"
                all_topics.append((topic_id, f"Can you give me an example of when you demonstrated {competency.lower()}?"))
        
        # Find the first unvisited topic
        for topic_id, topic_question in all_topics:
            if topic_id not in visited_topics:
                return topic_question
        
        return None
    
    def _update_session_state(self, session_state: Dict[str, Any], conductor_decision: ConductorDecision):
        """
        Update session state based on AI Conductor decision
        """
        action = conductor_decision.chosen_action.value
        session_state['last_action'] = action
        
        if action in ['CHALLENGE', 'DEEPEN']:
            # Increment follow-up counter for same topic
            session_state['follow_up_count'] += 1
        elif action == 'TRANSITION':
            # Reset for new topic - topic ID will be updated by the calling method
            session_state['follow_up_count'] = 0
        elif action == 'CONCEDE_AND_PIVOT':
            # AI detected concession - reset for new topic - topic ID will be updated by the calling method
            session_state['follow_up_count'] = 0
    
    def _handle_ai_conductor_transition(self, session_id: str, blueprint: InterviewBlueprint, conversation_transcript: List[str], session_state: Dict[str, Any], conductor_decision: ConductorDecision) -> Dict[str, Any]:
        """
        Handle AI Conductor TRANSITION with code-based topic selection.
        This is the DEFINITIVE solution to the topic repetition problem.
        """
        print(f"🎯 Code-based topic selection taking control")
        
        # Step 1: Extract the AI's transition phrase (everything before any question)
        ai_transition_phrase = conductor_decision.next_utterance
        
        # If the AI included a question, extract just the transition part
        # Look for common question starters to separate transition from question
        question_starters = ["Can you tell me", "Could you", "What", "How", "Describe", "Walk me through", "Tell me about"]
        for starter in question_starters:
            if starter in ai_transition_phrase:
                # Split at the question starter and keep only the transition part
                parts = ai_transition_phrase.split(starter, 1)
                if len(parts) > 1:
                    ai_transition_phrase = parts[0].strip()
                    # Add a connecting phrase if needed
                    if not ai_transition_phrase.endswith('.'):
                        ai_transition_phrase += "."
                break
        
        # Step 2: Code-based topic selection (100% reliable)
        next_topic_question = self._get_next_unvisited_topic(blueprint, session_state)
        
        if not next_topic_question:
            # All topics covered - complete the interview
            final_message = f"{ai_transition_phrase} I think we've covered all the key areas comprehensively. Thank you for sharing your detailed insights and experience with me today!"
            conversation_transcript.append(f"Sarah: {final_message}")
            self.last_ai_messages[session_id] = final_message
            self.conversation_transcripts[session_id] = conversation_transcript
            
            return {
                'status': 'success',
                'next_action': 'interview_complete',
                'message': final_message,
                'analysis': conductor_decision.analysis_of_last_answer,
                'conductor_action': 'TRANSITION',
                'progress': {'percentage': 100, 'status': 'completed'}
            }
        
        # Step 3: Combine AI's transition phrase with code-selected question
        complete_message = f"{ai_transition_phrase} {next_topic_question}"
        
        # Step 4: Update session state for new topic
        session_state['follow_up_count'] = 0
        session_state['last_action'] = 'TRANSITION'
        
        # Step 5: Add to transcript and store as last message
        conversation_transcript.append(f"Sarah: {complete_message}")
        self.last_ai_messages[session_id] = complete_message
        self.conversation_transcripts[session_id] = conversation_transcript
        
        # Calculate progress
        progress = self._calculate_progress(conversation_transcript, blueprint)
        
        print(f"✅ Code-based transition complete - moved to new topic")
        print(f"📈 Progress: {progress['percentage']}% complete")
        
        return {
            'status': 'success',
            'next_action': 'continue_conversation',
            'question': complete_message,
            'question_type': 'conversational',
            'analysis': conductor_decision.analysis_of_last_answer,
            'conductor_action': 'TRANSITION',
            'progress': progress
        }
    
    def _get_next_unvisited_topic(self, blueprint: InterviewBlueprint, session_state: Dict[str, Any]) -> Optional[str]:
        """
        DEFINITIVE SOLUTION: Code-based deterministic topic selection.
        Uses the actual interview plan questions generated by the LLM blueprint.
        This prevents topic repetition by maintaining a strict checklist.
        """
        visited_topics = session_state.get('visited_topics', set())
        current_topic_id = session_state.get('current_topic_id', 'intro')
        interview_type = session_state.get('interview_type', 'technical_behavioral')
        
        print(f"🔍 DETERMINISTIC TOPIC SELECTION:")
        print(f"   Interview type: {interview_type}")
        print(f"   Current topic: {current_topic_id}")
        print(f"   Visited topics: {visited_topics}")
        
        # Build the complete topic list from the actual blueprint questions
        # This ensures we use the LLM-generated interview plan, not hardcoded logic
        all_topics = []
        
        # Add technical questions (if applicable for this interview type)
        if interview_type in ['technical_only', 'technical-only', 'technical', 'technical_behavioral']:
            for i, question_obj in enumerate(blueprint.technical_questions):
                topic_id = f"tech_{i}"
                topic_name = f"Technical: {question_obj.intent}"
                all_topics.append((topic_id, question_obj.question_text, topic_name))
        
        # Add behavioral questions (if applicable for this interview type)  
        if interview_type in ['behavioral_only', 'behavioral-only', 'behavioral', 'technical_behavioral']:
            for i, question_obj in enumerate(blueprint.behavioral_questions):
                topic_id = f"behavioral_{i}"
                topic_name = f"Behavioral: {question_obj.intent}"
                all_topics.append((topic_id, question_obj.question_text, topic_name))
        
        print(f"   Available topics: {[(topic_id, topic_name) for topic_id, _, topic_name in all_topics]}")
        
        # CRITICAL FIX: Find the first unvisited topic and mark it as visited IMMEDIATELY
        for topic_id, topic_question, topic_name in all_topics:
            if topic_id not in visited_topics:
                # STEP 1: Mark this topic as visited BEFORE returning the question
                # This is the key fix that prevents repetition
                visited_topics.add(topic_id)
                session_state['visited_topics'] = visited_topics
                session_state['current_topic_id'] = topic_id
                
                print(f"🎯 SELECTED NEXT TOPIC: {topic_id} ({topic_name})")
                print(f"🎯 UPDATED VISITED TOPICS: {visited_topics}")
                
                # STEP 2: Return the question text
                return topic_question
        
        # No unvisited topics found - interview should complete
        print(f"🎯 ALL TOPICS COVERED - Interview ready for completion")
        print(f"🎯 Final state - Visited: {visited_topics}, Available: {len(all_topics)} topics")
        return None
    
    def _is_interview_complete(self, conductor_decision: ConductorDecision, conversation_transcript: List[str]) -> bool:
        """
        Determine if the interview should be completed based on conductor decision and conversation length
        """
        # Check if conductor explicitly indicates completion
        if "thank you" in conductor_decision.next_utterance.lower() and "complete" in conductor_decision.next_utterance.lower():
            return True
        
        if "that concludes" in conductor_decision.next_utterance.lower():
            return True
            
        # Check conversation length - if we have substantial conversation (20+ exchanges), consider completion
        if len(conversation_transcript) >= 20:
            return True
            
        return False
    
    def _calculate_progress(self, conversation_transcript: List[str], blueprint: InterviewBlueprint) -> Dict[str, Any]:
        """
        Calculate interview progress based on conversation transcript and blueprint
        """
        total_exchanges = len(conversation_transcript)
        interview_type = getattr(blueprint, 'interview_type', 'technical_behavioral')
        
        # Adjust expected exchange counts based on interview type
        if interview_type in ['technical_only', 'technical-only', 'technical']:
            # Technical-only: 8-10 questions, expect ~16-20 exchanges
            intro_threshold = 3
            exploration_threshold = 10
            deep_dive_threshold = 16
        elif interview_type in ['behavioral_only', 'behavioral-only', 'behavioral']:
            # Behavioral-only: 6-8 questions, expect ~12-16 exchanges
            intro_threshold = 3
            exploration_threshold = 8
            deep_dive_threshold = 14
        else:  # technical_behavioral (default)
            # Combined: expect ~18-24 exchanges
            intro_threshold = 4
            exploration_threshold = 12
            deep_dive_threshold = 18
        
        # Calculate progress based on adjusted thresholds
        if total_exchanges <= intro_threshold:
            percentage = 25
            status = "introduction"
        elif total_exchanges <= exploration_threshold:
            percentage = 50
            status = "exploration"
        elif total_exchanges <= deep_dive_threshold:
            percentage = 75
            status = "deep_dive"
        else:
            percentage = 90
            status = "completion"
        
        return {
            'percentage': percentage,
            'status': status,
            'exchanges': total_exchanges,
            'phase': 'conversational_interview'
            }
    
    def get_interview_status(self, session_id: str) -> Dict[str, Any]:
        """
        Get current interview status and progress
        """
        try:
            blueprint = blueprint_storage.get_blueprint(session_id)
            if not blueprint:
                return {
                    'status': 'error',
                    'message': 'Interview session not found'
                }
            
            # Get conversation transcript
            conversation_transcript = self.conversation_transcripts.get(session_id, [])
            
            # Calculate progress
            progress = self._calculate_progress(conversation_transcript, blueprint)
            
            return {
                'status': 'active',
                'progress': progress,
                'conversation_length': len(conversation_transcript),
                'session_info': {
                    'candidate_name': blueprint.candidate_name,
                    'position': blueprint.position,
                    'company': blueprint.company
                }
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to get status: {str(e)}'
            }
    
    def complete_interview(self, session_id: str) -> Dict[str, Any]:
        """
        Complete the interview and clean up resources
        """
        try:
            blueprint = blueprint_storage.get_blueprint(session_id)
            if not blueprint:
                return {
                    'status': 'error',
                    'message': 'Interview session not found'
                }
            
            # Get conversation transcript
            conversation_transcript = self.conversation_transcripts.get(session_id, [])
            
            # Generate completion summary
            completion_summary = {
                'session_id': session_id,
                'status': 'completed',
                'completion_time': datetime.now().isoformat(),
                'interview_summary': {
                    'candidate_name': blueprint.candidate_name,
                    'position': blueprint.position,
                    'company': blueprint.company,
                    'duration': str(datetime.now() - blueprint.created_at),
                    'conversation_exchanges': len(conversation_transcript),
                    'interviewer_directives': blueprint.interviewer_directives,
                    'focus_areas_covered': {
                        'technical_skills': blueprint.key_technical_skills,
                        'behavioral_competencies': blueprint.key_behavioral_competencies,
                        'relevant_projects': blueprint.relevant_projects
                    }
                },
                'conversation_transcript': conversation_transcript,
                'message': 'Interview completed successfully! Thank you for your time and detailed responses.'
            }
            
            # Clean up conversation transcript from memory
            if session_id in self.conversation_transcripts:
                del self.conversation_transcripts[session_id]
            
            print(f"✅ Interview completed for session: {session_id}")
            
            return completion_summary
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to complete interview: {str(e)}'
            }
    
    def get_blueprint_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a summary of the interview blueprint and conversation for debugging/analysis
        """
        blueprint = blueprint_storage.get_blueprint(session_id)
        if not blueprint:
            return None
        
        conversation_transcript = self.conversation_transcripts.get(session_id, [])
        
        return {
            'session_id': session_id,
            'candidate_name': blueprint.candidate_name,
            'position': blueprint.position,
            'company': blueprint.company,
            'created_at': blueprint.created_at.isoformat(),
            'interviewer_directives': blueprint.interviewer_directives,
            'key_technical_skills': blueprint.key_technical_skills,
            'key_behavioral_competencies': blueprint.key_behavioral_competencies,
            'relevant_projects': blueprint.relevant_projects,
            'conversation_length': len(conversation_transcript),
            'conversation_preview': conversation_transcript[:4] if conversation_transcript else []
        }

# Utility functions for backward compatibility and integration

def is_technical_behavioral_interview(interview_type: str) -> bool:
    """Check if this is an interview type that should use the two-phase system"""
    return interview_type in [
        'technical_behavioral', 'behavioral-technical', 'technical-behavioral',  # Combined
        'technical_only', 'technical-only', 'technical',  # Technical only
        'behavioral_only', 'behavioral-only', 'behavioral'  # Behavioral only
    ]

def create_legacy_response_format(ai_conductor_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert AI Conductor system response to legacy format for frontend compatibility
    """
    if ai_conductor_result.get('status') == 'error':
        return ai_conductor_result
    
    if ai_conductor_result.get('next_action') == 'interview_complete':
        return {
            'status': 'completed',
            'message': ai_conductor_result.get('message', 'Interview completed'),
            'next_action': 'interview_complete'
        }
    
    # AI Conductor system uses conversational flow - map to legacy format
    action = ai_conductor_result.get('next_action', 'continue_conversation')
    conductor_action = ai_conductor_result.get('conductor_action', 'CHALLENGE')
    
    # Map conductor actions to legacy actions
    if action == 'continue_conversation':
        if conductor_action in ['CHALLENGE', 'DEEPEN']:
            legacy_next_action = 'needs_followup'
        elif conductor_action == 'CONCEDE_AND_PIVOT':
            legacy_next_action = 'ready_for_questions'
        else:  # TRANSITION
            legacy_next_action = 'ready_for_questions'
    else:
        legacy_next_action = action

    legacy_response = {
        'status': 'success',
        'next_action': legacy_next_action,
        'follow_up_question': ai_conductor_result.get('question') if legacy_next_action == 'needs_followup' else None,
        'question_type': ai_conductor_result.get('question_type', 'conversational'),
        'analysis_notes': f"AI Conductor ({conductor_action}): {ai_conductor_result.get('analysis', 'Processing response')}",
        'interview_phase': 'conversational',
        'progress': ai_conductor_result.get('progress', {}),
        'conductor_action': conductor_action
    }
    
    return legacy_response
