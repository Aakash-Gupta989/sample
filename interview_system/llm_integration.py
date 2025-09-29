"""
LLM Integration for Groq API
Handles the actual LLM calls with proper error handling and fallbacks
"""

import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import requests
from datetime import datetime, timedelta

@dataclass
class LLMConfig:
    groq_api_key: str
    openai_api_key: str
    groq_model: str = "meta-llama/llama-4-maverick-17b-128e-instruct"
    openai_model: str = "gpt-4o"
    max_retries: int = 3
    timeout_seconds: int = 30

class LLMClient:
    """
    LLM client that uses Groq API with rate limiting
    """
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.groq_base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.last_api_call = None
        print(f"🔧 LLM Client initialized with model: {config.groq_model}")
    
    def _enforce_rate_limit(self, estimated_tokens: int):
        """Minimal rate limiting - just prevent immediate bursts"""
        current_time = datetime.now()
        
        # Only enforce a very minimal delay to prevent immediate bursts
        if self.last_api_call:
            time_since_last = (current_time - self.last_api_call).total_seconds()
            if time_since_last < 0.5:  # Only 0.5 second minimum interval
                wait_time = 0.5 - time_since_last
                print(f"⏱️  Brief pause: waiting {wait_time:.1f}s")
                time.sleep(wait_time)
        
        self.last_api_call = datetime.now()

    def generate_response(self, prompt: str, temperature: float = 0.1, max_tokens: int = 2000) -> str:
        """
        Generate response using Groq API with rate limiting
        
        Args:
            prompt: The input prompt
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens in response
            
        Returns:
            Generated response text
        """
        
        # Estimate tokens and enforce rate limiting
        estimated_tokens = len(prompt.split()) * 1.3 + max_tokens
        self._enforce_rate_limit(int(estimated_tokens))
        
        try:
            return self._call_groq(prompt, temperature, max_tokens)
        except Exception as e:
            print(f"Groq API failed: {e}")
            raise Exception("Groq API service failed")
    
    def _call_groq(self, prompt: str, temperature: float, max_tokens: int) -> str:
        """Call Groq API"""
        
        # Estimate token usage for debugging
        estimated_prompt_tokens = len(prompt.split()) * 1.3  # Rough estimate
        print(f"🔍 Groq API call - Estimated prompt tokens: {estimated_prompt_tokens:.0f}, Max response tokens: {max_tokens}")
        
        headers = {
            "Authorization": f"Bearer {self.config.groq_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.config.groq_model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert technical interviewer and engineering specialist. Provide accurate, detailed, and professional responses."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": 0.9,
            "stream": False
        }
        
        for attempt in range(self.config.max_retries):
            try:
                response = requests.post(
                    self.groq_base_url,
                    headers=headers,
                    json=payload,
                    timeout=self.config.timeout_seconds
                )
                
                if response.status_code == 200:
                    try:
                        result = response.json()
                        content = result["choices"][0]["message"]["content"].strip()
                        
                        # Validate that content is not malformed JSON if it looks like JSON
                        if content.startswith('{') or content.startswith('['):
                            try:
                                json.loads(content)  # Test if it's valid JSON
                            except json.JSONDecodeError as json_err:
                                print(f"⚠️  Malformed JSON detected: {json_err}")
                                print(f"Raw content: {content[:200]}...")
                                # Try to fix common JSON issues
                                content = self._fix_malformed_json(content)
                        
                        return content
                    except (KeyError, IndexError) as e:
                        print(f"❌ Unexpected response structure: {e}")
                        raise Exception(f"Invalid API response structure: {e}")
                    except json.JSONDecodeError as e:
                        print(f"❌ Failed to parse API response as JSON: {e}")
                        print(f"Raw response: {response.text[:500]}...")
                        raise Exception(f"Invalid JSON in API response: {e}")
                elif response.status_code == 429:
                    # Rate limit exceeded - wait much longer for coding questions
                    print(f"Groq API error 429: {response.text}")
                    if attempt < self.config.max_retries - 1:
                        # For rate limits, wait much longer - up to 2 minutes
                        wait_time = min(120, 15 * (2 ** attempt))  # 15s, 30s, 60s, then cap at 120s
                        print(f"Rate limited, waiting {wait_time} seconds before retry...")
                        time.sleep(wait_time)
                    else:
                        raise Exception(f"Groq API failed with status {response.status_code}")
                else:
                    print(f"Groq API error {response.status_code}: {response.text}")
                    if attempt < self.config.max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                    else:
                        raise Exception(f"Groq API failed with status {response.status_code}")
                        
            except requests.exceptions.Timeout:
                print(f"Groq API timeout on attempt {attempt + 1}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise Exception("Groq API timeout")
            except Exception as e:
                print(f"Groq API error on attempt {attempt + 1}: {e}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                        raise e
    
    def _fix_malformed_json(self, content: str) -> str:
        """Attempt to fix common JSON formatting issues"""
        try:
            # Common fixes for malformed JSON
            fixed_content = content
            
            # Remove trailing commas before closing braces/brackets
            import re
            fixed_content = re.sub(r',\s*}', '}', fixed_content)
            fixed_content = re.sub(r',\s*]', ']', fixed_content)
            
            # Fix unescaped quotes in strings (basic attempt)
            # This is a simplified fix - more complex cases may still fail
            
            # Try to parse the fixed content
            json.loads(fixed_content)
            print(f"✅ Successfully fixed malformed JSON")
            return fixed_content
            
        except Exception as fix_error:
            print(f"❌ Could not fix malformed JSON: {fix_error}")
            # Return original content - let the calling code handle it
            return content
    
    # OpenAI methods removed - using Groq only
    
    def analyze_with_vision(self, prompt: str, image_data: str) -> str:
        """
        Analyze images using GPT-4o vision capabilities
        
        Args:
            prompt: Text prompt for analysis
            image_data: Base64 encoded image data
            
        Returns:
            Analysis result
        """
        
        headers = {
            "Authorization": f"Bearer {self.config.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 2000
        }
        
        try:
            response = requests.post(
                self.openai_base_url,
                headers=headers,
                json=payload,
                timeout=self.config.timeout_seconds
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"].strip()
            else:
                raise Exception(f"Vision API failed with status {response.status_code}")
                
        except Exception as e:
            print(f"Vision analysis failed: {e}")
            raise e

class InterviewLLMPrompts:
    """
    Specialized prompts for different interview system components
    """
    
    @staticmethod
    def get_interviewer_greeting_prompt(interviewer_name: str, interviewer_title: str, 
                                      company: str, candidate_name: str, position: str,
                                      interview_type: str, duration: int) -> str:
        """Generate greeting prompt for AI interviewer"""
        
        return f"""
You are {interviewer_name}, a {interviewer_title} at {company}. 
You are conducting a {interview_type.replace('_', ' ')} interview for {candidate_name} 
who is applying for the {position} position.

Generate a warm, professional greeting that:
1. Introduces yourself and your role
2. Welcomes the candidate
3. Explains the interview format ({interview_type}, ~{duration} minutes)
4. Sets a positive, encouraging tone
5. Asks them to introduce themselves

Keep it natural and conversational, like a real senior engineer would speak.
Limit to 3-4 sentences maximum.
"""
    
    @staticmethod
    def get_response_evaluation_prompt(interviewer_name: str, question: str, 
                                     expected_points: List[str], candidate_response: str,
                                     evaluation_criteria: List[str]) -> str:
        """Generate prompt for evaluating candidate responses"""
        
        return f"""
You are {interviewer_name}, an experienced engineering interviewer.

QUESTION ASKED: {question}

EXPECTED KEY POINTS:
{chr(10).join(f"- {point}" for point in expected_points)}

CANDIDATE'S RESPONSE: "{candidate_response}"

EVALUATION CRITERIA:
{chr(10).join(f"- {criteria}" for criteria in evaluation_criteria)}

Evaluate the response and provide:

EVALUATION: [2-3 sentence assessment of response quality, technical accuracy, and completeness]
FOLLOW_UP_NEEDED: [Yes/No - whether a follow-up question would add value]
FOLLOW_UP_QUESTION: [If Yes above, provide one focused follow-up question]
NEXT_ACTION: [continue/follow_up/next_question]

Be constructive and encouraging while being honest about gaps or areas for improvement.
"""
    
    @staticmethod
    def get_adaptive_question_prompt(interviewer_name: str, conversation_context: str,
                                   interview_phase: str, candidate_level: str) -> str:
        """Generate adaptive follow-up question"""
        
        return f"""
You are {interviewer_name} conducting an interview.

CONVERSATION SO FAR: {conversation_context}
CURRENT PHASE: {interview_phase}
CANDIDATE LEVEL: {candidate_level}

Based on the conversation, generate ONE thoughtful follow-up question that:
1. Builds naturally on what was just discussed
2. Explores deeper understanding or practical application
3. Is appropriate for a {candidate_level} level candidate
4. Maintains good interview flow

Provide ONLY the question, no additional text or explanation.
"""

# Example usage for frontend integration
def create_llm_client(groq_api_key: str, openai_api_key: str = "") -> LLMClient:
    """
    Factory function to create configured LLM client
    
    Usage in your frontend:
        llm_client = create_llm_client(groq_key, openai_key)
        interview_api = InterviewSystemAPI(llm_client)
    """
    
    config = LLMConfig(
        groq_api_key=groq_api_key,
        openai_api_key=openai_api_key
    )
    
    return LLMClient(config)

# Mock client for testing (same as in interview_conductor.py)
class MockLLMClient:
    """Mock LLM client for testing without API keys"""
    
    def generate_response(self, prompt: str, use_gpt4: bool = False, 
                         temperature: float = 0.1, max_tokens: int = 2000) -> str:
        """Generate mock responses for testing"""
        
        prompt_lower = prompt.lower()
        
        # Two-phase system: Data synthesis mock (new unified format)
        if "extract the key requirements, skills, behavioral competencies" in prompt_lower:
            return json.dumps({
                "jd_summary": {
                    "key_technical_skills": [
                        "Python",
                        "System Design", 
                        "Microservices Architecture",
                        "Cloud Platforms (AWS/GCP)",
                        "API Development",
                        "Database Design",
                        "DevOps/CI-CD"
                    ],
                    "key_behavioral_competencies": [
                        "Technical Leadership",
                        "Cross-functional Collaboration", 
                        "Mentoring and Coaching",
                        "Strategic Thinking",
                        "High-level of Ownership"
                    ]
                },
                "resume_summary": {
                    "highlighted_projects": [
                        {
                            "project_name": "Distributed Systems Platform at Google",
                            "skills_used": ["Python", "Microservices", "Kubernetes"],
                            "quantifiable_result": "Built platform handling 1M+ requests per day with 99.9% uptime"
                        },
                        {
                            "project_name": "Microservices Migration Leadership",
                            "skills_used": ["System Architecture", "Team Leadership", "DevOps"],
                            "quantifiable_result": "Led team of 5 engineers, improved deployment speed by 10x"
                        },
                        {
                            "project_name": "Scalable API Development",
                            "skills_used": ["API Design", "Database Optimization", "Performance Tuning"],
                            "quantifiable_result": "Reduced API response time by 60% and increased throughput by 3x"
                        },
                        {
                            "project_name": "Cloud Infrastructure Modernization",
                            "skills_used": ["AWS", "Infrastructure as Code", "Monitoring"],
                            "quantifiable_result": "Migrated legacy systems to cloud, reduced infrastructure costs by 40%"
                        },
                        {
                            "project_name": "Junior Engineer Mentoring Program",
                            "skills_used": ["Mentoring", "Technical Training", "Code Reviews"],
                            "quantifiable_result": "Mentored 8 junior engineers, 100% promotion rate within 18 months"
                        }
                    ]
                }
            })
        
        # Two-phase system: Master prompt mock (new interview plan format)
        if "create a complete, personalized, and challenging 45-minute interview blueprint" in prompt_lower:
            return json.dumps({
                "interview_plan": {
                    "job_title": "Senior Software Engineer",
                    "company_name": "TechCorp",
                    "candidate_focus": "Based on the inputs, the interview should probe deeply into their experience with Python and System Design on the Distributed Systems Platform at Google and assess their ability for Technical Leadership.",
                    "interview_flow": [
                        {
                            "phase": "Introduction & Opening (5 mins)",
                            "question_id": "OPENER_01",
                            "question_text": "Thanks for your time today. To start, could you walk me through your resume and highlight the experience you feel is most relevant for this role at TechCorp?",
                            "intent": "Icebreaker and to understand the candidate's self-perception."
                        },
                        {
                            "phase": "Technical Behavioral Deep Dive (20 mins)",
                            "question_id": "TB_01",
                            "question_text": "The job description emphasizes 'Technical Leadership'. On your resume, you mentioned your work on 'Distributed Systems Platform at Google'. Could you tell me about a time during that project when you had to demonstrate technical leadership under pressure?",
                            "based_on_resume": "Distributed Systems Platform at Google",
                            "based_on_jd": "Technical Leadership",
                            "possible_follow_ups": [
                                "What was the most significant technical trade-off you had to make?",
                                "How did you measure the success of your leadership approach?",
                                "If you could lead that project again, what would you do differently?"
                            ]
                        },
                        {
                            "phase": "Technical Behavioral Deep Dive (20 mins)",
                            "question_id": "TB_02",
                            "question_text": "I see you led a 'Microservices Migration' project. The role requires 'Cross-functional Collaboration'. Can you describe a specific situation where you had to collaborate across different teams during this migration?",
                            "based_on_resume": "Microservices Migration Leadership",
                            "based_on_jd": "Cross-functional Collaboration",
                            "possible_follow_ups": [
                                "What was the biggest challenge in aligning different teams?",
                                "How did you handle conflicting priorities between teams?",
                                "What communication strategies proved most effective?"
                            ]
                        },
                        {
                            "phase": "Problem-Solving / Case Study (15 mins)",
                            "question_id": "CASE_01",
                            "question_text": "Let's do a system design exercise. Imagine TechCorp wants to build a real-time notification system that can handle 10 million users. Walk me through how you would architect this system, considering scalability, reliability, and cost.",
                            "intent": "Assess system design skills and technical problem-solving in a live scenario."
                        },
                        {
                            "phase": "Candidate Questions & Closing (5 mins)",
                            "question_id": "CLOSING_01",
                            "question_text": "That's all my questions for you. Now, what questions do you have for me about the role, the team, or the culture here?",
                            "intent": "Evaluate candidate's curiosity and engagement."
                        }
                    ]
                }
            })
        
        # Two-phase system: Follow-up engine mock (new technical behavioral format)
        if "your purpose is to analyze a candidate's answer to a deep technical or domain-specific question" in prompt_lower:
            # New technical behavioral follow-up format
            if "brief" in prompt_lower or len(prompt) < 500:
                return json.dumps({
                    "is_answer_sufficient": False,
                    "reasoning": "The solution lacks technical depth and doesn't address edge cases or complexity analysis.",
                    "next_action": "ASK_FOLLOW_UP",
                    "follow_up_question": "This works, but what is the time complexity? Can you refactor it to be more efficient?"
                })
            else:
                return json.dumps({
                    "is_answer_sufficient": True,
                    "reasoning": "The solution is technically sound with good explanation of approach and complexity.",
                    "next_action": "MOVE_ON",
                    "follow_up_question": None
                })
        
        # Legacy follow-up engine mock for other interview types
        if "analyze the candidate's response and decide" in prompt_lower:
            # Simple mock logic for follow-up decisions
            if "brief" in prompt_lower or len(prompt) < 500:
                return json.dumps({
                    "next_action": "ASK_FOLLOW_UP",
                    "follow_up_question": "Could you provide more specific details about your experience with that?",
                    "reasoning": "Answer was brief, requesting more detail"
                })
            else:
                return json.dumps({
                    "next_action": "MOVE_ON",
                    "reasoning": "Sufficient detail provided, moving to next question"
                })
        
        # Resume analysis mock
        if "analyze this resume" in prompt_lower:
            return json.dumps({
                "candidate_name": "John Doe",
                "experience_level": "mid_level", 
                "total_years_experience": 4.0,
                "technical_skills": [
                    {
                        "skill_name": "SolidWorks",
                        "proficiency_level": "advanced",
                        "years_experience": 3.0,
                        "context": ["Product design", "Assembly modeling"]
                    },
                    {
                        "skill_name": "GD&T",
                        "proficiency_level": "intermediate", 
                        "years_experience": 2.0,
                        "context": ["Drawing creation", "Tolerance analysis"]
                    }
                ],
                "soft_skills": ["communication", "problem_solving", "teamwork"],
                "education": {
                    "degree": "BS Mechanical Engineering",
                    "field": "Mechanical Engineering", 
                    "institution": "State University",
                    "graduation_year": "2020"
                },
                "projects": [
                    {
                        "title": "Automotive Component Design",
                        "description": "Designed brake system components",
                        "technologies_used": ["SolidWorks", "FEA"],
                        "duration": "6 months",
                        "impact": "Reduced weight by 15%"
                    }
                ],
                "leadership_experience": ["Led junior engineer mentoring"],
                "problem_solving_examples": ["Cost reduction project saving $200K"],
                "domain_expertise": ["automotive", "manufacturing"],
                "communication_indicators": ["Technical presentations", "Documentation"],
                "learning_agility_indicators": ["New CAD software adoption"]
            })
        
        # Job description analysis mock
        elif "analyze this job description" in prompt_lower:
            return json.dumps({
                "job_title": "Mechanical Design Engineer",
                "company_name": "TechCorp",
                "department": "Engineering",
                "seniority_level": "mid",
                "industry": "Automotive",
                "team_size": 8,
                "reports_to": "Senior Engineering Manager",
                "requirements": [
                    {
                        "skill_name": "SolidWorks",
                        "category": "technical",
                        "requirement_type": "must_have",
                        "proficiency_level": "advanced",
                        "years_required": 3.0,
                        "description": "3D CAD modeling and assembly design"
                    },
                    {
                        "skill_name": "GD&T",
                        "category": "technical", 
                        "requirement_type": "must_have",
                        "proficiency_level": "intermediate",
                        "years_required": 2.0,
                        "description": "Geometric dimensioning and tolerancing"
                    },
                    {
                        "skill_name": "FEA",
                        "category": "technical",
                        "requirement_type": "preferred", 
                        "proficiency_level": "intermediate",
                        "years_required": 1.0,
                        "description": "Finite element analysis"
                    }
                ],
                "responsibilities": [
                    "Design mechanical components and assemblies",
                    "Create detailed drawings and specifications", 
                    "Collaborate with cross-functional teams",
                    "Support manufacturing and testing"
                ],
                "key_challenges": [
                    "Complex multi-part assemblies",
                    "Tight tolerance requirements",
                    "Cost optimization"
                ],
                "growth_opportunities": [
                    "Lead designer role",
                    "Advanced analysis training",
                    "Cross-functional project leadership"
                ]
            })
        
        # Greeting generation
        elif "generate a warm, professional greeting" in prompt_lower:
            return "Hello! I'm Sarah, a Principal Engineer here at TechCorp. I've been with the company for 8 years, primarily working on automotive systems and thermal management solutions. Today I'll be conducting your technical and behavioral interview for the Mechanical Design Engineer position, which should take about 60 minutes. I'm excited to learn about your background and experience. Could you please start by introducing yourself and telling me what interests you about this role?"
        
        # Response evaluation
        elif "evaluate the response" in prompt_lower:
            return """EVALUATION: The candidate demonstrated good understanding of CAD workflow fundamentals and showed awareness of design intent and manufacturability considerations. The response was well-structured and covered the key aspects of the modeling process.
FOLLOW_UP_NEEDED: Yes
FOLLOW_UP_QUESTION: Can you tell me about a specific challenging assembly you've worked on and how you managed the complexity?
NEXT_ACTION: follow_up"""
        
        # Adaptive questions
        elif "generate one thoughtful follow-up" in prompt_lower:
            return "That's interesting about your cost reduction project. Can you walk me through your specific approach to identifying and implementing those cost savings?"
        
        # Interview summary
        elif "generate a comprehensive interview summary" in prompt_lower:
            return """OVERALL_ASSESSMENT: Good Candidate
TECHNICAL_STRENGTHS: Strong SolidWorks proficiency, good understanding of design fundamentals, practical manufacturing knowledge
AREAS_FOR_IMPROVEMENT: Could develop deeper FEA skills, expand knowledge of advanced materials
BEHAVIORAL_ASSESSMENT: Excellent communication skills, shows strong problem-solving approach, good team collaboration
RECOMMENDATION: Hire with conditions
REASONING: Candidate has solid foundation and relevant experience. With some additional training in advanced analysis tools, would be a strong contributor to the team."""
        
        # Default response
        else:
            return "This is a mock response for testing purposes. The candidate shows good technical understanding and communication skills."
    
    def analyze_with_vision(self, prompt: str, image_data: str) -> str:
        """Mock vision analysis"""
        return "Mock vision analysis: The image appears to show technical drawings or engineering diagrams. The candidate demonstrates good visual communication skills."
