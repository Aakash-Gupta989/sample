"""
Interview Blueprint System - Two-Phase Architecture
Phase 1: Pre-Interview Setup (The Blueprint)
Phase 2: Live Interview Session (The Execution)
"""

import json
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum

class QuestionType(Enum):
    INTRODUCTION_JOB = "introduction_job"
    INTRODUCTION_RESUME = "introduction_resume"  
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"

class NextAction(Enum):
    MOVE_ON = "MOVE_ON"
    ASK_FOLLOW_UP = "ASK_FOLLOW_UP"
    DRILL_DOWN = "DRILL_DOWN"
    CONCLUDE_TOPIC = "CONCLUDE_TOPIC"

@dataclass
class QuestionObject:
    """Individual question in the interview blueprint"""
    id: str
    question_text: str
    question_type: QuestionType
    intent: str  # What this question is trying to assess
    context: str  # Background context for the question
    expected_indicators: List[str]  # What to look for in a good answer
    max_follow_ups: int = 2
    time_allocation: int = 3  # minutes

@dataclass
class InterviewBlueprint:
    """Complete interview plan generated in Phase 1"""
    session_id: str
    candidate_name: str
    position: str
    company: str
    created_at: datetime
    
    # Synthesized data from Phase 1
    key_technical_skills: List[str]
    key_behavioral_competencies: List[str]
    relevant_projects: List[str]
    
    # The complete interview flow
    introduction_questions: List[QuestionObject]  # 6 questions
    technical_questions: List[QuestionObject]     # 4 questions  
    behavioral_questions: List[QuestionObject]    # 3 questions
    
    # ALL fields with defaults must come at the very end
    interview_type: str = 'technical_behavioral'
    current_section: str = "introduction"  # introduction, technical, behavioral, completed
    current_question_index: int = 0
    follow_up_count: int = 0
    interviewer_directives: List[str] = field(default_factory=list)

@dataclass
class FollowUpDecision:
    """Response from the Follow-up Engine"""
    next_action: NextAction
    follow_up_question: Optional[str] = None
    reasoning: Optional[str] = None

class DataSynthesizer:
    """Phase 1: Synthesizes raw inputs into structured data"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
    
    def synthesize_inputs(self, resume_text: str, job_description: str, 
                         position: str, company: str) -> Dict[str, Any]:
        """
        Synthesize raw inputs into structured data using the unified pre-processing prompt
        """
        synthesis_prompt = f"""You are a meticulous data extraction AI, acting as an interview preparation strategist. Your task is to extract specific, verifiable details from a resume and JD to build a targeted interview plan. **You must not summarize, generalize, or rephrase the candidate's project descriptions.**

**Your Goal:** Extract verbatim project details and link them directly to the job's requirements to create a list of sharp, evidence-based question topics.

**Inputs:**
- Job Description: {job_description}
- Candidate's Resume: {resume_text}

**Instructions:**
1.  **Extract Verbatim Projects:** From the resume, extract the top 5 `highlighted_projects`. Copy the project description or key achievement bullet point as close to verbatim as possible. Do not invent a generic "project_name".
2.  **Map Skills to Projects:** For each project, list the specific skills the candidate demonstrated **in that project**.
3.  **Generate Evidence-Based Question Areas:** Create a list of 5 `potential_question_areas`. Each item must be a specific directive for an interviewer, quoting a detail from the resume and connecting it to a JD requirement.

**Output Format:** You MUST respond ONLY with a single, valid JSON object.

{{
  "jd_summary": {{
    "key_technical_skills": ["Mechanical enclosures", "FEA", "Casting", "Cross-functional communication"],
    "key_behavioral_competencies": ["Innovative", "Self-starter", "Work independently"]
  }},
  "resume_summary": {{
    "highlighted_projects": [
      {{
        "project_detail": "Designed and led development of IP68-rated enclosures for PCBA and display, taking the project from ideation to mass production (at John Deere).",
        "skills_used": ["Enclosure Design", "IP68", "Thermal Management", "Mass Production", "DFM"]
      }},
      {{
        "project_detail": "Engineered and designed aluminum alloy engine components, boosting efficiency by 15% and cutting costs by 20% (at Goodwill Motor).",
        "skills_used": ["FEA", "Solidworks", "GD&T", "Cost Reduction", "Component Design"]
      }},
      {{
        "project_detail": "Reduced Bill of Materials (BOM) by 36% through innovative design, FEA modeling, and process optimization (on VISION-ELECTRIC VEHICLE).",
        "skills_used": ["BOM Reduction", "FEA", "EV Design", "Process Optimization"]
      }}
    ]
  }},
  "potential_question_areas": [
    "Challenge the candidate on the specifics of their IP68 enclosure design from John Deere. Ask how they achieved the seal and what specific thermal challenges they faced with the PCBA.",
    "Drill down into the claim of 'boosting efficiency by 15%' on the Goodwill Motor engine components. Ask what specific design changes led to this result and how it was measured.",
    "Question the process behind the '36% BOM reduction' on the electric vehicle project. Ask them to walk through one specific optimization they made.",
    "Connect their experience coordinating with suppliers in China, India, and the USA (from John Deere) to the JD's requirement for 'cross-functional communication'. Ask about a specific miscommunication and how they resolved it.",
    "Probe their hands-on experience with 'casting', a key JD requirement, by asking how it applied to the 'aluminum alloy engine components' project."
  ]
}}"""
        
        try:
            response = self.llm_client.generate_response(synthesis_prompt, temperature=0.1)
            # Clean the response to extract JSON
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            
            synthesized_data = json.loads(response)
            print(f"✅ Data synthesis completed successfully")
            print(f"🔍 PREPROCESSING JSON OUTPUT:")
            print(json.dumps(synthesized_data, indent=2))
            
            # Convert new format to internal format for backward compatibility
            converted_data = self._convert_synthesis_format(synthesized_data)
            print(f"🔍 CONVERTED DATA:")
            print(json.dumps(converted_data, indent=2))
            return converted_data
            
        except Exception as e:
            print(f"❌ Data synthesis failed: {e}")
            # Fallback to basic extraction
            return {
                "key_technical_skills": ["Technical Skills", "Problem Solving", "System Design", "Engineering", "Analysis"],
                "key_behavioral_competencies": ["Leadership", "Communication", "Teamwork"],
                "relevant_projects": ["Project Experience", "Technical Implementation", "Problem Solving"],
                "candidate_strengths": ["Technical Background", "Experience", "Skills"],
                "areas_to_probe": ["Technical Depth", "Leadership Experience", "Problem Solving"],
                "resume_job_alignment": "Candidate appears to have relevant experience for the role"
            }
    
    def _convert_synthesis_format(self, new_format_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert the new unified pre-processing format to internal format
        """
        try:
            jd_summary = new_format_data.get("jd_summary", {})
            resume_summary = new_format_data.get("resume_summary", {})
            highlighted_projects = resume_summary.get("highlighted_projects", [])
            
            # Extract project details and create relevant projects list
            relevant_projects = [project.get("project_detail", project.get("project_name", f"Project {i+1}"))[:80] + "..." if len(project.get("project_detail", project.get("project_name", f"Project {i+1}"))) > 80 else project.get("project_detail", project.get("project_name", f"Project {i+1}"))
                               for i, project in enumerate(highlighted_projects[:3])]
            
            # Create candidate strengths from project skills
            candidate_strengths = []
            for project in highlighted_projects[:3]:
                skills = project.get("skills_used", [])
                candidate_strengths.extend(skills[:2])  # Take first 2 skills from each project
            candidate_strengths = list(set(candidate_strengths))[:3]  # Remove duplicates, limit to 3
            
            # Create areas to probe from technical skills and behavioral competencies
            technical_skills = jd_summary.get("key_technical_skills", [])
            behavioral_competencies = jd_summary.get("key_behavioral_competencies", [])
            areas_to_probe = (technical_skills[:2] + behavioral_competencies[:1])[:3]
            
            # Generate alignment assessment
            resume_job_alignment = f"Candidate has experience with {len(highlighted_projects)} relevant projects and skills that align with the role requirements"
            
            return {
                "key_technical_skills": jd_summary.get("key_technical_skills", [])[:5],
                "key_behavioral_competencies": jd_summary.get("key_behavioral_competencies", [])[:5],
                "relevant_projects": relevant_projects,
                "candidate_strengths": candidate_strengths if candidate_strengths else ["Technical Experience", "Project Management", "Problem Solving"],
                "areas_to_probe": areas_to_probe if areas_to_probe else ["Technical Depth", "Leadership", "Communication"],
                "resume_job_alignment": resume_job_alignment,
                "detailed_projects": highlighted_projects  # Keep the detailed project info for advanced use
            }
            
        except Exception as e:
            print(f"⚠️ Format conversion failed: {e}, using fallback")
            return {
                "key_technical_skills": ["Technical Skills", "Problem Solving", "System Design", "Engineering", "Analysis"],
                "key_behavioral_competencies": ["Leadership", "Communication", "Teamwork"],
                "relevant_projects": ["Project Experience", "Technical Implementation", "Problem Solving"],
                "candidate_strengths": ["Technical Background", "Experience", "Skills"],
                "areas_to_probe": ["Technical Depth", "Leadership Experience", "Problem Solving"],
                "resume_job_alignment": "Candidate appears to have relevant experience for the role"
            }

class MasterPromptExecutor:
    """Phase 1: Executes the Master Prompt to create Interview Blueprint"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
    
    def create_interview_blueprint(self, synthesized_data: Dict[str, Any], 
                                 candidate_name: str, position: str, 
                                 company: str, interview_type: str = 'technical_behavioral') -> InterviewBlueprint:
        """
        Execute the Master Prompt to create complete interview blueprint using the new main system prompt
        """
        session_id = f"interview_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        
        # Get type-specific prompt based on interview type
        master_prompt = self._get_type_specific_prompt(interview_type, synthesized_data, position, company)

        try:
            raw_response = self.llm_client.generate_response(master_prompt, temperature=0.2, max_tokens=4000)
            # Log raw LLM output before any parsing
            print("--- RAW LLM BLUEPRINT OUTPUT ---")
            print(raw_response)
            print("---------------------------------")
            
            # Clean the response to extract JSON
            response = raw_response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            # Log cleaned (pre-JSON) output
            print("🔍 Cleaned LLM output (pre-JSON):")
            print(response)
            
            blueprint_data = json.loads(response)
            
            # Support multiple blueprint shapes:
            # 1) Top-level keys: { "interviewer_directives": [...], "interview_plan": { "interview_flow": [...] } }
            # 2) Strict top-level interview_plan that contains both topic_modules and interviewer_directives
            #    { "interview_plan": { "topic_modules": [...], "interviewer_directives": [...] } }
            # 3) Entire plan directly at top-level (no interview_plan wrapper)
            candidate_plan = blueprint_data.get("interview_plan", blueprint_data)
            interviewer_directives = blueprint_data.get("interviewer_directives", candidate_plan.get("interviewer_directives", []))
            interview_flow = candidate_plan.get("interview_flow")
            
            # Construct interview_flow from topic_modules if needed
            if not interview_flow and isinstance(candidate_plan, dict) and "topic_modules" in candidate_plan:
                interview_flow = []
                for idx, module in enumerate(candidate_plan.get("topic_modules", []), 1):
                    try:
                        opening_q = module.get("opening_question") or module.get("question") or ""
                        interview_flow.append({
                            "phase": module.get("topic_name", module.get("name", f"Technical Topic {idx}")),
                            "question_id": module.get("question_id", f"TECH_{idx:02d}"),
                            "question_text": opening_q,
                            "intent": module.get("intent", "Assess technical depth")
                        })
                    except Exception:
                        continue
            if interview_flow is None:
                interview_flow = []
            
            # Convert the new format to QuestionObject instances
            # Since the new format doesn't separate by type, we'll create a single flow
            all_questions = []
            for q in interview_flow:
                # Determine question type based on phase, topic_module, and interview type
                phase = q.get("phase", "").lower()
                topic_module = q.get("topic_module", "").lower()
                intent = q.get("intent", "").lower()
                
                # Check for introduction questions
                if "introduction" in phase or "opening" in phase:
                    question_type = QuestionType.INTRODUCTION_JOB
                # Check for behavioral indicators
                elif any(keyword in phase + " " + topic_module + " " + intent for keyword in [
                    "behavioral", "leadership", "teamwork", "collaboration", "communication", 
                    "conflict", "adaptability", "initiative", "ownership", "star", "experience",
                    "team", "management", "project management"
                ]):
                    question_type = QuestionType.BEHAVIORAL
                # Check for technical indicators  
                elif any(keyword in phase + " " + topic_module + " " + intent for keyword in [
                    "technical", "coding", "programming", "system", "design", "algorithm",
                    "problem", "case", "architecture", "performance", "optimization", "deep dive"
                ]):
                    question_type = QuestionType.TECHNICAL
                # Default based on interview type
                elif interview_type in ['behavioral_only', 'behavioral-only', 'behavioral']:
                    question_type = QuestionType.BEHAVIORAL
                elif interview_type in ['technical_only', 'technical-only', 'technical']:
                    question_type = QuestionType.TECHNICAL
                else:
                    # For combined interviews, default to technical
                    question_type = QuestionType.TECHNICAL
                
                question_obj = QuestionObject(
                    id=q.get("question_id", f"q_{len(all_questions)+1}"),
                    question_text=q.get("question_text", ""),
                    question_type=question_type,
                    intent=q.get("intent", ""),
                    context=q.get("phase", ""),
                    expected_indicators=q.get("possible_follow_ups", [])[:3],  # Use follow-ups as indicators
                    max_follow_ups=len(q.get("possible_follow_ups", [])),
                    time_allocation=self._extract_time_from_phase(q.get("phase", ""))
                )
                all_questions.append(question_obj)
            
            # For backward compatibility, separate into categories
            # But now we have a more flexible flow-based structure
            intro_questions = [q for q in all_questions if q.question_type == QuestionType.INTRODUCTION_JOB]
            tech_questions = [q for q in all_questions if q.question_type == QuestionType.TECHNICAL]
            behavioral_questions = [q for q in all_questions if q.question_type == QuestionType.BEHAVIORAL]
            
            # If no separation occurred, put everything in intro for the flow to work
            if not intro_questions and not tech_questions and not behavioral_questions:
                intro_questions = all_questions
            
            # Create the complete blueprint
            blueprint = InterviewBlueprint(
                session_id=session_id,
                candidate_name=candidate_name,
                position=position,
                company=company,
                created_at=datetime.now(),
                interview_type=interview_type,
                key_technical_skills=synthesized_data["key_technical_skills"],
                key_behavioral_competencies=synthesized_data["key_behavioral_competencies"],
                relevant_projects=synthesized_data["relevant_projects"],
                interviewer_directives=interviewer_directives,
                introduction_questions=intro_questions,
                technical_questions=tech_questions,
                behavioral_questions=behavioral_questions
            )
            
            print(f"✅ Interview blueprint created successfully with {len(intro_questions)} intro, {len(tech_questions)} technical, {len(behavioral_questions)} behavioral questions")
            return blueprint
            
        except Exception as e:
            print(f"❌ Master prompt execution failed: {e}")
            try:
                # Best-effort log of raw output if available
                print("--- RAW LLM BLUEPRINT OUTPUT (on error) ---")
                print(raw_response)
                print("-------------------------------------------")
            except Exception:
                pass
            # Create fallback blueprint
            return self._create_fallback_blueprint(session_id, candidate_name, position, company, synthesized_data, interview_type)
    
    def _extract_time_from_phase(self, phase: str) -> int:
        """Extract time allocation from phase description"""
        import re
        match = re.search(r'\((\d+)\s*mins?\)', phase)
        if match:
            return int(match.group(1))
        # Default time allocations based on phase type
        phase_lower = phase.lower()
        if "introduction" in phase_lower or "opening" in phase_lower:
            return 5
        elif "deep dive" in phase_lower:
            return 20
        elif "problem" in phase_lower or "case" in phase_lower:
            return 15
        elif "closing" in phase_lower:
            return 5
        else:
            return 10
    
    def _create_fallback_blueprint(self, session_id: str, candidate_name: str, 
                                 position: str, company: str, 
                                 synthesized_data: Dict[str, Any], interview_type: str = 'technical_behavioral') -> InterviewBlueprint:
        """Create a basic fallback blueprint using the new interview flow format"""
        
        # Create a simple fallback interview flow
        intro_questions = [
            QuestionObject(
                id="OPENER_01",
                question_text=f"Thanks for your time today. To start, could you walk me through your resume and highlight the experience you feel is most relevant for this {position} role at {company}?",
                question_type=QuestionType.INTRODUCTION_JOB,
                intent="Icebreaker and to understand the candidate's self-perception",
                context="Introduction & Opening (5 mins)",
                expected_indicators=["Clear communication", "Relevant experience", "Role understanding"],
                max_follow_ups=2,
                time_allocation=5
            )
        ]
        
        tech_questions = [
            QuestionObject(
                id="TB_01",
                question_text="Tell me about a challenging project from your background and how you approached solving the technical problems you encountered.",
                question_type=QuestionType.TECHNICAL,
                intent="Assess technical problem-solving and project experience",
                context="Technical Behavioral Deep Dive (20 mins)",
                expected_indicators=["Technical depth", "Problem-solving approach", "Project impact"],
                max_follow_ups=3,
                time_allocation=20
            ),
            QuestionObject(
                id="CASE_01",
                question_text=f"Let's do a quick problem-solving exercise. How would you approach designing a solution for a typical challenge in the {position} role?",
                question_type=QuestionType.TECHNICAL,
                intent="Assess problem-solving skills and domain knowledge in a live scenario",
                context="Problem-Solving / Case Study (15 mins)",
                expected_indicators=["Analytical thinking", "Domain knowledge", "Structured approach"],
                max_follow_ups=2,
                time_allocation=15
            )
        ]
        
        behavioral_questions = [
            QuestionObject(
                id="CLOSING_01",
                question_text="That's all my questions for you. Now, what questions do you have for me about the role, the team, or the culture here?",
                question_type=QuestionType.BEHAVIORAL,
                intent="Evaluate candidate's curiosity and engagement",
                context="Candidate Questions & Closing (5 mins)",
                expected_indicators=["Curiosity", "Engagement", "Thoughtful questions"],
                max_follow_ups=0,
                time_allocation=5
            )
        ]
        
        return InterviewBlueprint(
            session_id=session_id,
            candidate_name=candidate_name,
            position=position,
            company=company,
            created_at=datetime.now(),
            interview_type=interview_type,
            key_technical_skills=synthesized_data["key_technical_skills"],
            key_behavioral_competencies=synthesized_data["key_behavioral_competencies"],
            relevant_projects=synthesized_data["relevant_projects"],
            introduction_questions=intro_questions,
            technical_questions=tech_questions,
            behavioral_questions=behavioral_questions
        )
    
    def _get_type_specific_prompt(self, interview_type: str, synthesized_data: Dict[str, Any], 
                                position: str, company: str) -> str:
        """Generate type-specific prompts for different interview types"""
        
        if interview_type in ['technical_only', 'technical-only', 'technical']:
            return self._get_technical_only_prompt(synthesized_data, position, company)
        elif interview_type in ['behavioral_only', 'behavioral-only', 'behavioral']:
            return self._get_behavioral_only_prompt(synthesized_data, position, company)
        else:  # technical_behavioral (default)
            return self._get_technical_behavioral_prompt(synthesized_data, position, company)
    
    def _get_technical_only_prompt(self, synthesized_data: Dict[str, Any], position: str, company: str) -> str:
        """Create prompt for technical-only interviews (8-10 questions)"""
        return f"""# ROLE: You are a senior hiring manager and a top-tier technical expert in the candidate's field.

## GOAL
Your task is to create a complete and challenging **technical-only** interview plan. The plan must exclusively assess the candidate's technical depth, problem-solving abilities, and hands-on skills.

## CRITICAL RULE
You MUST ONLY generate `topic_modules` based on the `key_technical_skills` from the synthesized data. You are **FORBIDDEN** from creating topics based on the `key_behavioral_competencies` (e.g., "teamwork," "self-starter," "communication"). The interview must remain 100% technical.

## CONTEXT
- **Synthesized Data JSON:** {json.dumps(synthesized_data, indent=2)}
- **Job Title:** {position}
- **Company Name:** {company}

## INSTRUCTIONS
1.  **Create Technical Topic Modules:** Generate 4-5 distinct `topic_modules` based ONLY on the candidate's technical skills and project experience (e.g., "FEA Validation & Analysis," "Casting & DFM," "System Design Challenge").
2.  **Generate Probing Questions:** For each topic, create a sharp `opening_question` that requires the candidate to provide specific, evidence-based technical details.

## OUTPUT FORMAT
You MUST respond ONLY with a single, valid JSON object for the interview plan.

{{
  "interviewer_directives": [
    "Primary Goal: Probe for understanding of trade-offs and technical decision-making",
    "Secondary Goal: Assess problem-solving process, not just the final answer",
    "Focus: Technical depth over breadth, hands-on experience validation"
  ],
  "interview_plan": {{
    "job_title": "{position}",
    "company_name": "{company}",
    "interview_flow": [
      {{
        "phase": "Technical Introduction",
        "question_id": "TECH_INTRO_01",
        "question_text": "Walk me through your technical background and the projects you're most proud of for this {position} role at {company}.",
        "intent": "Technical background assessment"
      }}
    ]
  }}
}}"""
    
    def _get_behavioral_only_prompt(self, synthesized_data: Dict[str, Any], position: str, company: str) -> str:
        """Create prompt for behavioral-only interviews (6-8 questions)"""
        return f"""# ROLE: You are an expert behavioral interviewer and senior hiring manager representing the values of {company}.

## GOAL
Your task is to create a complete, personalized, and insightful behavioral interview plan. The plan must focus exclusively on assessing competencies like teamwork, leadership, problem-solving, and communication using the STAR method.

## CONTEXT
- **Synthesized Data JSON:** {json.dumps(synthesized_data, indent=2)}
- **Job Title:** {position}
- **Company Name:** {company}

## INSTRUCTIONS
1.  **Create Behavioral Topic Modules:** Generate 4-5 distinct `topic_modules`. Each topic MUST be a core behavioral competency derived from the `key_behavioral_competencies` in the synthesized data (e.g., "Teamwork & Collaboration," "Ownership & Initiative," "Handling Conflict," "Adaptability").
2.  **Generate STAR-based Questions:** For each topic, create an `opening_question` that prompts the candidate to tell a specific story from a project on their resume. The question should be framed to elicit a STAR (Situation, Task, Action, Result) response.
3.  **Create Interviewer Directives:** Generate 2-3 `interviewer_directives` focused on what to look for (e.g., "Probe for personal contribution ('I' vs 'we')," "Ensure the candidate describes a measurable result").

## OUTPUT FORMAT
You MUST respond ONLY with a single, valid JSON object for the interview plan.

{{
  "interviewer_directives": [
    "Primary Goal: Probe for personal contribution ('I' vs 'we')",
    "Secondary Goal: Ensure the candidate describes a measurable result",
    "Focus: Complete STAR stories with specific behavioral evidence"
  ],
  "interview_plan": {{
    "job_title": "{position}",
    "company_name": "{company}",
    "interview_flow": [
      {{
        "phase": "Behavioral Introduction",
        "question_id": "BEH_INTRO_01",
        "question_text": "Tell me about your professional background and what draws you to this {position} role at {company}.",
        "intent": "Behavioral background assessment"
      }}
    ]
  }}
}}"""
    
    def _get_technical_behavioral_prompt(self, synthesized_data: Dict[str, Any], position: str, company: str) -> str:
        """Create prompt for combined technical+behavioral interviews (original system)"""
        return f"""You are a senior hiring manager and a distinguished subject matter expert in the field of {position}. Your task is to create a complete interview blueprint based on the evidence provided.

**!! CRITICAL RULE FOR QUESTION FRAMING !!**
You MUST differentiate between the candidate's experience (from the resume) and the job's requirements (from the JD). Frame questions about the candidate's past experience using ONLY information found in their resume. Frame hypothetical questions to see how they would handle requirements from the JD that are NOT in their resume.

**Inputs:**
- Synthesized Data JSON: {json.dumps(synthesized_data, indent=2)}
- Job Title: {position}
- Company Name: {company}

**Instructions:**
1.  **Generate Interviewer Directives:** Based on the inputs, first create a short list of 2-3 strategic goals for this specific interview. This will guide the tone and focus.
2.  **Use the Strategic Plan:** You MUST build your questions directly from the highly specific topics listed in the `potential_question_areas` array.
3.  **Prioritize Depth:** Your plan should focus on going deep on 2-3 key projects rather than asking many superficial questions.

**Output Format:** You MUST respond ONLY with a single, valid JSON object including the new `interviewer_directives` key.

{{
  "interviewer_directives": [
    "Primary Goal: Validate the quantifiable achievements on the resume (e.g., '15% efficiency boost', '36% BOM reduction'). Ask for specific data and methods.",
    "Secondary Goal: Assess hands-on knowledge of core skills from the JD (casting, thermal FEA) by grounding questions in their past projects.",
    "Behavioral Focus: Probe for examples of being a 'self-starter' and working 'independently' as mentioned in the JD."
  ],
  "interview_plan": {{
    "job_title": "{position}",
    "company_name": "{company}",
    "interview_flow": [
      {{
        "phase": "Introduction & Opening (5 mins)",
        "question_id": "OPENER_01",
        "question_text": "Thanks for your time today. To start, could you walk me through your resume and highlight the experience you feel is most relevant for this role at {company}?",
        "intent": "Icebreaker and to understand the candidate's self-perception."
      }},
      {{
        "phase": "Project Deep Dive 1: Enclosure Design",
        "question_id": "PROJ_01",
        "question_text": "Your resume mentions you led the development of IP68-rated enclosures at John Deere from ideation to mass production. Can you walk me through the most significant technical challenge you faced in achieving that IP68 rating?",
        "based_on_resume": "IP68-rated enclosures project",
        "based_on_jd": "Mechanical enclosures for custom electronics",
        "intent": "Assess deep knowledge of environmental sealing and design for manufacturing."
      }},
      {{
        "phase": "Problem-Solving / Case Study (15 mins)",
        "question_id": "CASE_01",
        "question_text": "Generate a domain-specific hypothetical scenario aligned with `potential_question_areas` and the JD. Ensure the framing respects the Critical Rule.",
        "intent": "Assess problem-solving skills and domain knowledge in a live scenario."
      }},
      {{
        "phase": "Candidate Questions & Closing (5 mins)",
        "question_id": "CLOSING_01",
        "question_text": "That's all my questions for you. Now, what questions do you have for me about the role, the team, or the culture here?",
        "intent": "Evaluate candidate's curiosity and engagement."
      }}
    ]
  }}
}}"""

class BlueprintStorage:
    """Storage system for interview blueprints"""
    
    def __init__(self):
        self.blueprints: Dict[str, InterviewBlueprint] = {}
    
    def store_blueprint(self, blueprint: InterviewBlueprint) -> str:
        """Store blueprint and return session_id"""
        self.blueprints[blueprint.session_id] = blueprint
        print(f"📁 Blueprint stored for session: {blueprint.session_id}")
        return blueprint.session_id
    
    def get_blueprint(self, session_id: str) -> Optional[InterviewBlueprint]:
        """Retrieve blueprint by session_id"""
        return self.blueprints.get(session_id)
    
    def update_blueprint(self, session_id: str, blueprint: InterviewBlueprint):
        """Update existing blueprint"""
        self.blueprints[session_id] = blueprint
    
    def delete_blueprint(self, session_id: str):
        """Delete blueprint after interview completion"""
        if session_id in self.blueprints:
            del self.blueprints[session_id]
            print(f"🗑️ Blueprint deleted for session: {session_id}")

# Global storage instance
blueprint_storage = BlueprintStorage()
