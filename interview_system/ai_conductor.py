import json
import ast
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum

class ConductorAction(Enum):
    CHALLENGE = "CHALLENGE"
    DEEPEN = "DEEPEN" 
    TRANSITION = "TRANSITION"
    CONCEDE_AND_PIVOT = "CONCEDE_AND_PIVOT"

@dataclass
class ConductorDecision:
    analysis_of_last_answer: str
    chosen_action: ConductorAction
    next_utterance: str

class AIConductor:
    """
    The AI Conductor is the central intelligence that manages the entire interview conversation.
    It has full context of the interview plan and conversation history to make strategic decisions.
    """
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
    
    # Removed Python-side concession detection to avoid forcibly stopping the flow
    
    def _extract_json(self, text: str) -> str:
        """
        Robust JSON extraction from LLM output with comprehensive error handling.
        - Strips code fences like ```json ... ```
        - Trims leading/trailing whitespace
        - Extracts substring from first '{' to last '}' if needed
        - Fixes common JSON formatting issues (double braces, quotes, etc.)
        - Handles multiple malformed JSON patterns
        - Final fallback: regex-extract the first balanced JSON object
        """
        if not text:
            return text
        cleaned = text.strip()
        
        # Strip code fences
        if cleaned.startswith("```"):
            # Remove starting fence
            if cleaned.startswith("```json"):
                cleaned = cleaned[len("```json"):]
            else:
                cleaned = cleaned[len("```"):]
            # Remove ending fence if present
            if cleaned.endswith("```"):
                cleaned = cleaned[: -len("```")]
        cleaned = cleaned.strip()
        
        # Extract JSON braces if extra text remains
        start = cleaned.find('{')
        end = cleaned.rfind('}')
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start:end+1]
        
        # Fix common malformed JSON issues
        
        # 1. Replace double braces {{ }} with single { }
        if cleaned.startswith('{{'):
            cleaned = cleaned[1:]
        if cleaned.endswith('}}'):
            cleaned = cleaned[:-1]
            
        # 2. Fix multiple consecutive opening/closing braces
        import re
        cleaned = re.sub(r'\{\{+', '{', cleaned)  # {{{{ -> {
        cleaned = re.sub(r'\}\}+', '}', cleaned)  # }}}} -> }
        
        # 3. Fix common quote issues
        cleaned = re.sub(r'"\s*:\s*"([^"]*)"', r'": "\1"', cleaned)  # Fix spacing around colons
        
        # 4. Ensure proper JSON structure
        cleaned = cleaned.strip()
        if not cleaned.startswith('{'):
            cleaned = '{' + cleaned
        if not cleaned.endswith('}'):
            cleaned = cleaned + '}'
        
        # 5. Final fallback: try to extract balanced JSON with regex
        try:
            # Test if current cleaned version is valid JSON
            import json
            json.loads(cleaned)
            return cleaned
        except:
            # If still invalid, try regex extraction of balanced braces
            import re
            brace_pattern = r'\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\})*)*\}))*\}'
            matches = re.findall(brace_pattern, text)
            if matches:
                # Return the first balanced JSON object found
                return matches[0]
            
        return cleaned
    
    def conduct_next_turn(self, interview_plan: Dict[str, Any], conversation_transcript: List[str], candidate_last_answer: str, interview_type: str = 'technical_behavioral') -> ConductorDecision:
        """
        The main method that analyzes the full context and decides what to say next.
        
        Args:
            interview_plan: The complete interview blueprint JSON
            conversation_transcript: Full conversation history as list of strings
            candidate_last_answer: The candidate's most recent response
            
        Returns:
            ConductorDecision with the next action and utterance
        """
        
        # Build the full conversation transcript text
        full_transcript = "\n".join(conversation_transcript)
        if candidate_last_answer:
            full_transcript += f"\nCandidate: {candidate_last_answer}"
        
        # Removed early return enforcement for concessions
        
        # Create the AI Conductor prompt
        conductor_prompt = self._build_conductor_prompt(interview_plan, full_transcript, interview_type)
        
        try:
            # Make the single LLM call with full context
            response = self.llm_client.generate_response(conductor_prompt, temperature=0.1, max_tokens=800)
            
            # Parse the response with robust error handling
            sanitized = self._extract_json(response)
            print(f"🔍 Sanitized JSON: {sanitized[:200]}...")
            
            try:
                response_data = json.loads(sanitized)
                print(f"✅ JSON parsed successfully")
            except json.JSONDecodeError as e:
                print(f"⚠️  JSON decode error: {e}")
                try:
                    # Strategy 1: Try ast.literal_eval for single-quoted JSON
                    import ast
                    response_data = ast.literal_eval(sanitized)
                    print(f"✅ Parsed with ast.literal_eval")
                except Exception as ast_error:
                    print(f"⚠️  ast.literal_eval failed: {ast_error}")
                    # Strategy 2: Manual regex extraction of key fields
                    import re
                    analysis_match = re.search(r'"analysis_of_last_answer":\s*"([^"]*)"', sanitized)
                    action_match = re.search(r'"chosen_action":\s*"([^"]*)"', sanitized)
                    utterance_match = re.search(r'"next_utterance":\s*"([^"]*)"', sanitized)
                    
                    if analysis_match and action_match and utterance_match:
                        response_data = {
                            "analysis_of_last_answer": analysis_match.group(1),
                            "chosen_action": action_match.group(1),
                            "next_utterance": utterance_match.group(1)
                        }
                        print(f"✅ Extracted fields with regex")
                    else:
                        print(f"❌ Regex extraction failed")
                        raise ValueError("Could not extract required JSON fields")
            
            return ConductorDecision(
                analysis_of_last_answer=response_data.get("analysis_of_last_answer", "No analysis provided"),
                chosen_action=ConductorAction(response_data.get("chosen_action", "CHALLENGE")),
                next_utterance=response_data.get("next_utterance", "Could you provide more details?")
            )
            
        except Exception as e:
            print(f"❌ AI Conductor failed: {e}")
            # Fallback decision
            return ConductorDecision(
                analysis_of_last_answer=f"Error in conductor analysis: {str(e)}",
                chosen_action=ConductorAction.CHALLENGE,
                next_utterance="Could you elaborate on that point with more specific details?"
            )
    
    def _build_conductor_prompt(self, interview_plan: Dict[str, Any], full_transcript: str, interview_type: str = 'technical_behavioral') -> str:
        """
        Builds the complete AI Conductor prompt with full context.
        """
        
        # Convert interview plan to JSON string for injection
        interview_plan_json = json.dumps(interview_plan, indent=2)
        
        # Get type-specific prompt introduction
        print(f"🧭 Conductor prompt build - interview_type={interview_type}")
        if interview_type in ['technical_only', 'technical-only', 'technical']:
            print("🧭 Using TECHNICAL-ONLY conductor prompt branch")
            prompt_intro = f'''# ROLE: You are "Sarah," an expert technical interviewer. Your goal is to conduct a rigorous technical interview, assessing for factual accuracy, logical consistency, and depth of knowledge.'''
        elif interview_type in ['behavioral_only', 'behavioral-only', 'behavioral']:
            print("🧭 Using BEHAVIORAL-ONLY conductor prompt branch")
            prompt_intro = f'''# ROLE: You are "Sarah," an expert behavioral interviewer. Your goal is to explore the candidate's past experiences by ensuring they provide complete, structured answers using the STAR method.'''
        else:  # technical_behavioral (default)
            print("🧭 Using TECH+BEHAVIORAL conductor prompt branch (default)")
            prompt_intro = f'''You are "Sarah," an expert Principal Engineer and a world-class interviewer. Your goal is to conduct an insightful technical and behavioral interview based on the provided strategic plan. You must be persistent in seeking specific evidence, strategic in your topic transitions, and maintain a professional, conversational tone.'''
        
        # Create type-specific prompt body
        if interview_type in ['technical_only', 'technical-only', 'technical']:
            prompt = prompt_intro + f'''

## CONTEXT
- **The Interview Plan:** {interview_plan_json}
- **The Conversation History:** {full_transcript}
- **Topic Coverage Status:** [TOPIC_COVERAGE_JSON]

## TASK
Analyze the candidate's last answer and choose the most effective next action based on the logic below.

### Decision Logic
- **CONCEDE_AND_PIVOT:** If the candidate says "I don't know" or similar, you MUST gracefully move on.
- **CHALLENGE:** If the answer is factually incorrect, logically flawed, or superficial.
- **DEEPEN:** If the answer is correct but could be explored for more depth (e.g., ask about scalability, trade-offs, or edge cases).
- **TRANSITION:** If the topic is sufficiently covered, choose the next topic based on the `topic_coverage_status` with the following priority:
    1.  **Priority 1: New Topics.** Your first priority is to select a key topic from the interview plan that is marked as `"NOT_COVERED"`.
    2.  **Priority 2: Deeper Dive.** If all key topics are at least `"COVERED_GENERALLY"`, you may revisit a topic with that status, but you MUST acknowledge the previous discussion before asking a more specific, advanced question.

## OUTPUT FORMAT
You MUST respond ONLY with a single, valid JSON object.

### Example
{{{{
  "analysis_of_last_answer": "The candidate has thoroughly explained their general experience with FEA. The topic is now 'COVERED_GENERALLY'. The next unvisited topic is 'Casting'.",
  "concession_detected": false,
  "chosen_action": "TRANSITION",
  "next_utterance": "That's a very clear explanation of your FEA process. Let's move on to another key skill. Can you tell me about your experience with designing components for casting?"
}}}}'''
        elif interview_type in ['behavioral_only', 'behavioral-only', 'behavioral']:
            prompt = prompt_intro + f'''

## CONTEXT
- **The Interview Plan:** {interview_plan_json}
- **The Conversation History:** {full_transcript}
- **Topic Coverage Status:** [TOPIC_COVERAGE_JSON]

## TASK
Analyze the candidate's last answer and choose the most effective next action: `CHALLENGE`, `DEEPEN`, `TRANSITION`, or `CONCEDE_AND_PIVOT`.

### Decision Logic
- **CONCEDE_AND_PIVOT:** If the candidate cannot recall an example, you MUST gracefully move on.
- **CHALLENGE:** If the answer is missing a key part of the STAR method (e.g., they only described the situation, or said "we" instead of "I," or didn't provide a result).
- **DEEPEN:** If the answer is a good STAR story, but a part could be explored for more detail (e.g., "What was the specific outcome of your action?").
- **TRANSITION:** If the topic is sufficiently covered, move to the next logical topic based on the `topic_coverage_status`.

## OUTPUT FORMAT
You MUST respond ONLY with a single, valid JSON object.

### Example
{{{{
  "analysis_of_last_answer": "The candidate described the situation and the team's actions well, but they used 'we' throughout the entire story and didn't specify their personal contribution.",
  "concession_detected": false,
  "chosen_action": "CHALLENGE",
  "next_utterance": "Thanks for walking me through the team's approach. Could you clarify what your specific role was in that project? What were the actions that you personally took?"
}}}}'''
        else:
            # Use the original format for behavioral-only and technical+behavioral
            prompt = prompt_intro + f'''

**Your State:**
1.  **The Interview Plan:** This is your strategic guide, containing the key `topic_modules` and `interviewer_directives` you must cover.
    ```json
    {interview_plan_json}
    ```
2.  **The Conversation History:** This is the full transcript of the interview so far.
    ```text
    {full_transcript}
    ```

**Your Task:**
Based on the full context, you must analyze the candidate's **very last answer** and determine the single most effective next step by following these steps in order:

**Step 1: Check for Concession.**
First, analyze the candidate's last answer. Are they explicitly stating they don't know the answer or cannot provide the requested detail (e.g., "I don't know," "I can't recall," "I am not sure")? If so, you MUST choose the `CONCEDE_AND_PIVOT` action.

**Step 2: Choose Your Action.**
If no concession is detected, analyze the answer's quality and choose one of the following actions:

* **`CHALLENGE`**: If the answer was weak, generic, evasive, or did not fully answer your question, your `next_utterance` should be a rephrased question or a direct probe that forces them to provide the specific evidence you asked for.
* **`DEEPEN`**: If the answer was good but the topic is not yet fully explored, your `next_utterance` should be a logical follow-up question to go one level deeper on the same topic.
* **`TRANSITION`**: If the current topic has been covered sufficiently, your `next_utterance` should be a smooth transition phrase followed by the opening question for the *next logical topic* from the interview plan. 

**CRITICAL TRANSITION RULE**: Before choosing your next topic, review the conversation history. If the conversation has already covered a topic extensively (e.g., if you've been discussing "enclosure design" for multiple turns), you MUST choose a DIFFERENT topic from the interview plan. For example:
- If you've discussed enclosures → transition to FEA, casting, or projects
- If you've discussed FEA → transition to casting, projects, or behavioral topics
- Always choose variety over repetition.

**Output Format:** You MUST respond ONLY with a single, valid JSON object.

**Example Format for a Concession:**
{{{{
  "analysis_of_last_answer": "The candidate explicitly stated 'I don't know' when asked for a specific line from their Dockerfile. Continuing to ask is pointless and makes for a bad experience.",
  "chosen_action": "CONCEDE_AND_PIVOT",
  "next_utterance": "No problem, that's completely fair. Let's switch gears then. The job description also mentions experience with CI/CD pipelines. Can you tell me about your role in developing and maintaining automation frameworks at Pursuit Software?"
}}}}'''

        return prompt
    
    def get_interview_introduction(self, interview_plan: Dict[str, Any], interview_type: str = 'technical_behavioral') -> str:
        """
        Extracts the introduction message from the interview plan with type-specific messaging.
        """
        try:
            print(f"🗣️ Building interview introduction - interview_type={interview_type}")
            # Look for introduction in the interview flow
            interview_flow = interview_plan.get("interview_plan", {}).get("interview_flow", [])
            
            for item in interview_flow:
                if item.get("phase", "").lower() == "introduction":
                    print("🗣️ Found introduction in interview_flow; returning flow intro")
                    return item.get("question_text", "Hi, I'm Sarah. Let's begin the interview.")
            
            # Fallback introduction with type-specific messaging
            job_title = interview_plan.get("interview_plan", {}).get("job_title", "role")
            company = interview_plan.get("company", "the company")
            candidate_name = interview_plan.get("candidate_name", "")
            
            # Create type-specific introduction
            if interview_type in ['technical_only', 'technical-only', 'technical']:
                interview_description = "technical interview focusing exclusively on your technical expertise, problem-solving skills, and project experience"
            elif interview_type in ['behavioral_only', 'behavioral-only', 'behavioral']:
                interview_description = "behavioral interview focusing exclusively on your professional experiences, soft skills, and leadership capabilities"
            else:  # technical_behavioral (default)
                interview_description = "comprehensive technical and behavioral interview to explore your experience and background"
            
            greeting = f"Hi {candidate_name}, I'm thrilled to meet you today! I'm Sarah, a Principal Engineer at {company}. I'm looking forward to a {interview_description} for the {job_title}."
            
            if interview_type in ['technical_only', 'technical-only', 'technical']:
                greeting += " This will be a technical interview, so I'll be asking questions to understand your technical expertise and problem-solving approach."
            elif interview_type in ['behavioral_only', 'behavioral-only', 'behavioral']:
                greeting += " This will be a behavioral interview, so I'll be asking questions about your professional experiences and how you handle various situations."
            else:
                greeting += " This will be a technical and behavioral interview, so I'll be asking questions to understand both your technical expertise and past experiences."
            
            greeting += " Can you start by telling me a bit about yourself and what excites you about this position?"
            print(f"🗣️ Introduction built (preview): {greeting[:140]}...")
            
            return greeting
            
        except Exception as e:
            print(f"❌ Error getting introduction: {e}")
            return "Hi, I'm Sarah. Let's begin the interview. Could you start by telling me about yourself?"
