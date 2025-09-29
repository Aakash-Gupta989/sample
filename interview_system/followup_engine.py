"""
Follow-up Engine - Phase 2: Live Interview Session
Handles dynamic follow-up questions based on candidate responses
"""

import json
from typing import Dict, Any, Optional
from .interview_blueprint import FollowUpDecision, NextAction, QuestionObject, QuestionType

class FollowUpEngine:
    """
    Phase 2: Dynamic follow-up question engine
    Decides whether to drill down or move on based on candidate responses
    """
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
    
    def evaluate_response(self, original_question: QuestionObject, 
                         candidate_answer: str, current_follow_up_count: int, 
                         interview_type: str = None, strategic_guidance: Dict = None) -> FollowUpDecision:
        """
        Evaluate candidate's response and decide on follow-up action
        
        Args:
            original_question: The QuestionObject that was asked
            candidate_answer: The candidate's response
            current_follow_up_count: How many follow-ups have been asked for this question
            interview_type: The type of interview (to determine which prompt to use)
            strategic_guidance: Optional guidance from answer quality assessment
            
        Returns:
            FollowUpDecision with next action and optional follow-up question
        """
        
        # Hard limit check - Force move on after 3 follow-ups regardless of LLM decision
        if current_follow_up_count >= 3:
            return FollowUpDecision(
                next_action=NextAction.MOVE_ON,
                reasoning="Maximum 3 follow-ups reached - automatically moving to next topic"
            )
        
        # Strategic guidance from answer quality assessment
        if strategic_guidance:
            recommended_action = strategic_guidance.get("recommended_action")
            print(f"🎯 Strategic recommendation: {recommended_action}")
            
            # Apply strategic guidance for certain clear cases
            if recommended_action == "CONCLUDE_TOPIC":
                return FollowUpDecision(
                    next_action=NextAction.MOVE_ON,
                    reasoning=f"Answer quality assessment suggests moving on: {strategic_guidance.get('strategy')}"
                )
            elif recommended_action == "DRILL_DOWN" and strategic_guidance.get("follow_up_style"):
                # Use strategic guidance to inform the follow-up
                return FollowUpDecision(
                    next_action=NextAction.ASK_FOLLOW_UP,
                    follow_up_question=strategic_guidance.get("follow_up_style"),
                    reasoning=f"Answer quality assessment suggests drilling down: {strategic_guidance.get('strategy')}"
                )
        
        # Use different prompts based on interview type
        if interview_type == "technical_behavioral":
            followup_prompt = self._get_technical_behavioral_followup_prompt(
                original_question, candidate_answer, current_follow_up_count
            )
        else:
            # Use the original prompt for other interview types
            followup_prompt = self._get_legacy_followup_prompt(
                original_question, candidate_answer, current_follow_up_count
            )
        
        try:
            response = self.llm_client.generate_response(followup_prompt, temperature=0.1, max_tokens=500)
            
            # Clean the response to extract JSON
            response = response.strip()
            print(f"🔍 Raw LLM response ({interview_type}): {response[:300]}...")
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            
            print(f"🔍 Cleaned response ({interview_type}): {response[:300]}...")
            decision_data = json.loads(response)
            
            # Handle both old and new formats
            if "next_action" in decision_data:
                # Map new actions to legacy actions
                llm_action = decision_data["next_action"]
                reasoning = decision_data.get("reasoning", "No reasoning provided")
                
                if llm_action == "DRILL_DOWN":
                    next_action = NextAction.ASK_FOLLOW_UP
                    follow_up_question = decision_data.get("follow_up_question")
                elif llm_action == "CONCLUDE_TOPIC":
                    next_action = NextAction.MOVE_ON
                    follow_up_question = None
                else:
                    # Handle legacy actions (ASK_FOLLOW_UP, MOVE_ON)
                    next_action = NextAction(llm_action)
                    follow_up_question = decision_data.get("follow_up_question") if next_action == NextAction.ASK_FOLLOW_UP else None
            elif "is_answer_sufficient" in decision_data:
                # Old format
                is_sufficient = decision_data.get("is_answer_sufficient", True)
                next_action = NextAction.MOVE_ON if is_sufficient else NextAction.ASK_FOLLOW_UP
                follow_up_question = decision_data.get("follow_up_question") if not is_sufficient else None
                reasoning = decision_data.get("reasoning", "No reasoning provided")
            else:
                # Fallback
                next_action = NextAction.MOVE_ON
                follow_up_question = None
                reasoning = "Invalid response format"
            
            # Enforce at least one follow-up on intro/technical if none asked yet
            if (
                next_action == NextAction.MOVE_ON
                and current_follow_up_count == 0
                and original_question.question_type in (QuestionType.INTRODUCTION_JOB, QuestionType.INTRODUCTION_RESUME, QuestionType.TECHNICAL)
            ):
                next_action = NextAction.ASK_FOLLOW_UP
                if not follow_up_question:
                    # Sensible generic probing follow-up
                    if original_question.question_type == QuestionType.TECHNICAL:
                        follow_up_question = "What key trade-offs or alternatives did you consider, and why was your approach the best in terms of performance and cost?"
                    else:
                        follow_up_question = "Great — could you share one concrete example with specific metrics that best illustrates your impact related to this role?"
                reasoning = "Policy: ask at least one probing follow-up for intro/technical questions"

            decision = FollowUpDecision(
                next_action=next_action,
                follow_up_question=follow_up_question,
                reasoning=reasoning
            )
            
            print(f"🔍 Follow-up decision: {next_action.value} - {reasoning}")
            return decision
            
        except Exception as e:
            print(f"❌ Follow-up engine failed: {e}")
            # Fallback decision logic
            return self._fallback_decision(original_question, candidate_answer, current_follow_up_count)
    
    def _get_technical_behavioral_followup_prompt(self, original_question: QuestionObject, 
                                                candidate_answer: str, current_follow_up_count: int) -> str:
        """Technical+Behavioral follow-up prompt (new version)"""
        intent_text = getattr(original_question, 'intent', '') or ""
        context_text = getattr(original_question, 'context', '') or ""
        return f"""You are an expert interviewer and subject matter expert... Your purpose is to analyze a candidate's answer and decide the most logical next step in the conversation.

**Inputs:**
- **Current Topic Goal:** "{intent_text}"
- **Original Question:** "{original_question.question_text}"
- **Candidate's Answer:** "{candidate_answer}"

**Instructions:**
1.  **Analyze the Answer:** Evaluate the answer's depth and accuracy against the `Current Topic Goal`.
2.  **Decide the Next Action:** Based on your analysis, choose one of three paths:
    - If the answer is incomplete or superficial, decide to **DRILL_DOWN** with a probing follow-up.
    - If the answer is sufficient and you've achieved the topic goal, decide to **CONCLUDE_TOPIC**.
3.  **Generate Follow-up (If Needed):** Only generate a question if the action is `DRILL_DOWN`.

**Output Format:** You MUST respond ONLY with a single, valid JSON object...
{{{{
  "reasoning": "The candidate has thoroughly explained their design process for the enclosure and their collaboration with the supplier. The goal for this topic has been met.",
  "next_action": "CONCLUDE_TOPIC",
  "follow_up_question": null
}}}}"""

    def _get_legacy_followup_prompt(self, original_question: QuestionObject, 
                                  candidate_answer: str, current_follow_up_count: int) -> str:
        """Legacy follow-up prompt updated to the same schema"""
        intent_text = getattr(original_question, 'intent', '') or ""
        context_text = getattr(original_question, 'context', '') or ""
        return f"""You are an expert interviewer and subject matter expert... Your purpose is to analyze a candidate's answer and decide the most logical next step in the conversation.

**Inputs:**
- **Current Topic Goal:** "{intent_text}"
- **Original Question:** "{original_question.question_text}"
- **Candidate's Answer:** "{candidate_answer}"

**Instructions:**
1.  **Analyze the Answer:** Evaluate the answer's depth and accuracy against the `Current Topic Goal`.
2.  **Decide the Next Action:** Based on your analysis, choose one of three paths:
    - If the answer is incomplete or superficial, decide to **DRILL_DOWN** with a probing follow-up.
    - If the answer is sufficient and you've achieved the topic goal, decide to **CONCLUDE_TOPIC**.
3.  **Generate Follow-up (If Needed):** Only generate a question if the action is `DRILL_DOWN`.

**Output Format:** You MUST respond ONLY with a single, valid JSON object...
{{{{
  "reasoning": "The candidate has thoroughly explained their design process for the enclosure and their collaboration with the supplier. The goal for this topic has been met.",
  "next_action": "CONCLUDE_TOPIC",
  "follow_up_question": null
}}}}"""

    
    def _fallback_decision(self, original_question: QuestionObject, 
                          candidate_answer: str, current_follow_up_count: int) -> FollowUpDecision:
        """
        Fallback decision logic if LLM call fails
        """
        # Simple heuristics for fallback
        answer_length = len(candidate_answer.split())
        
        # If answer is very short, ask for more detail
        if answer_length < 20 and current_follow_up_count == 0:
            follow_up_questions = {
                "technical": "Can you elaborate on your technical approach and the reasoning behind it?",
                "behavioral": "Can you provide more specific details about the situation and your actions?",
                "introduction_job": "Could you expand on that and provide more specific examples?",
                "introduction_resume": "Can you give me more details about your experience with that?"
            }
            
            return FollowUpDecision(
                next_action=NextAction.ASK_FOLLOW_UP,
                follow_up_question=follow_up_questions.get(original_question.question_type.value, 
                                                         "Could you provide more details about that?"),
                reasoning="Answer was brief, requesting more detail"
            )
        
        # If we've already asked one follow-up, move on
        if current_follow_up_count >= 1:
            return FollowUpDecision(
                next_action=NextAction.MOVE_ON,
                reasoning="Fallback: Moving on after one follow-up"
            )
        
        # Default to moving on
        return FollowUpDecision(
            next_action=NextAction.MOVE_ON,
            reasoning="Fallback: Default move on"
        )

class InterviewExecutor:
    """
    Phase 2: Executes the interview blueprint with dynamic follow-ups
    """
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.followup_engine = FollowUpEngine(llm_client)
    
    def get_current_question(self, blueprint) -> Optional[QuestionObject]:
        """
        Get the current question based on interview state
        """
        if blueprint.current_section == "introduction":
            questions = blueprint.introduction_questions
        elif blueprint.current_section == "technical":
            questions = blueprint.technical_questions
        elif blueprint.current_section == "behavioral":
            questions = blueprint.behavioral_questions
        else:
            return None
        
        if blueprint.current_question_index < len(questions):
            return questions[blueprint.current_question_index]
        else:
            # Section complete, transition to next section
            return self._transition_to_next_section(blueprint)
    
    def _transition_to_next_section(self, blueprint) -> Optional[QuestionObject]:
        """
        Transition to the next section of the interview
        """
        if blueprint.current_section == "introduction":
            blueprint.current_section = "technical"
            blueprint.current_question_index = 0
            blueprint.follow_up_count = 0
            print(f"🔄 Transitioning to TECHNICAL phase")
            return blueprint.technical_questions[0] if blueprint.technical_questions else None
            
        elif blueprint.current_section == "technical":
            blueprint.current_section = "behavioral"
            blueprint.current_question_index = 0
            blueprint.follow_up_count = 0
            print(f"🔄 Transitioning to BEHAVIORAL phase")
            return blueprint.behavioral_questions[0] if blueprint.behavioral_questions else None
            
        elif blueprint.current_section == "behavioral":
            blueprint.current_section = "completed"
            print(f"🎉 Interview completed!")
            return None
        
        return None
    
    def process_response(self, blueprint, candidate_answer: str, quality_assessment=None, strategic_guidance=None) -> Dict[str, Any]:
        """
        Process candidate response and determine next action
        
        Args:
            blueprint: Interview blueprint
            candidate_answer: Candidate's response
            quality_assessment: Optional answer quality assessment from micro-prompt
            strategic_guidance: Optional strategic guidance based on quality
        
        Returns:
            Dict with next_action, question (if any), and status information
        """
        current_question = self.get_current_question(blueprint)
        
        if not current_question:
            return {
                "next_action": "interview_complete",
                "status": "completed",
                "message": "Interview has been completed successfully!"
            }
        
        # Determine interview type - for technical+behavioral, we pass "technical_behavioral"
        # For other types, we pass None to use legacy behavior
        interview_type = "technical_behavioral"  # Since this is only used by the two-phase system
        
        # Get follow-up decision from the engine (enhanced with strategic guidance)
        decision = self.followup_engine.evaluate_response(
            current_question, 
            candidate_answer, 
            blueprint.follow_up_count,
            interview_type,
            strategic_guidance
        )
        
        if decision.next_action == NextAction.ASK_FOLLOW_UP:
            # Ask follow-up question
            blueprint.follow_up_count += 1
            
            return {
                "next_action": "ask_follow_up",
                "question": decision.follow_up_question,
                "question_type": current_question.question_type.value,
                "section": blueprint.current_section,
                "follow_up_count": blueprint.follow_up_count,
                "reasoning": decision.reasoning,
                "status": "active"
            }
        
        else:  # MOVE_ON
            # Move to next primary question
            blueprint.current_question_index += 1
            blueprint.follow_up_count = 0
            
            next_question = self.get_current_question(blueprint)
            
            if next_question:
                return {
                    "next_action": "next_question",
                    "question": next_question.question_text,
                    "question_type": next_question.question_type.value,
                    "question_intent": next_question.intent,
                    "question_context": next_question.context,
                    "section": blueprint.current_section,
                    "question_index": blueprint.current_question_index,
                    "status": "active"
                }
            else:
                return {
                    "next_action": "interview_complete",
                    "status": "completed",
                    "message": "Interview has been completed successfully!"
                }
    
    def get_interview_status(self, blueprint) -> Dict[str, Any]:
        """
        Get current interview status and progress
        """
        total_questions = (len(blueprint.introduction_questions) + 
                          len(blueprint.technical_questions) + 
                          len(blueprint.behavioral_questions))
        
        completed_questions = 0
        if blueprint.current_section == "technical":
            completed_questions = len(blueprint.introduction_questions)
        elif blueprint.current_section == "behavioral":
            completed_questions = (len(blueprint.introduction_questions) + 
                                 len(blueprint.technical_questions))
        elif blueprint.current_section == "completed":
            completed_questions = total_questions
        
        completed_questions += blueprint.current_question_index
        
        return {
            "session_id": blueprint.session_id,
            "current_section": blueprint.current_section,
            "current_question_index": blueprint.current_question_index,
            "follow_up_count": blueprint.follow_up_count,
            "progress": {
                "completed_questions": completed_questions,
                "total_questions": total_questions,
                "percentage": int((completed_questions / total_questions) * 100) if total_questions > 0 else 0
            },
            "sections": {
                "introduction": {
                    "total": len(blueprint.introduction_questions),
                    "completed": len(blueprint.introduction_questions) if blueprint.current_section != "introduction" else blueprint.current_question_index
                },
                "technical": {
                    "total": len(blueprint.technical_questions),
                    "completed": len(blueprint.technical_questions) if blueprint.current_section == "behavioral" or blueprint.current_section == "completed" else (blueprint.current_question_index if blueprint.current_section == "technical" else 0)
                },
                "behavioral": {
                    "total": len(blueprint.behavioral_questions),
                    "completed": blueprint.current_question_index if blueprint.current_section == "behavioral" else (len(blueprint.behavioral_questions) if blueprint.current_section == "completed" else 0)
                }
            }
        }
