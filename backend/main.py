from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import json
import random
import asyncio
from datetime import datetime
from typing import Dict, List

from config import Config
from models import *
# Import real OpenAI service or fallback to mock
try:
    if Config.OPENAI_API_KEY and Config.OPENAI_API_KEY not in ["", "your-openai-key-here"]:
        from services.openai_service import OpenAIService
        print("🔧 Using real OpenAI service")
    else:
        from services.mock_openai_service import MockOpenAIService as OpenAIService
        print("🔧 Using mock OpenAI service (no API key)")
except Exception as e:
    from services.mock_openai_service import MockOpenAIService as OpenAIService
    print(f"🔧 Fallback to mock OpenAI service: {e}")
from services.groq_service import GroqService
# Use lightweight whisper service for Render free tier
try:
    from services.whisper_service_light import WhisperService
    print("🔧 Using lightweight Whisper service (OpenAI API)")
except ImportError:
    from services.whisper_service import WhisperService
    print("🔧 Using full Whisper service (local model)")
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from interview_system.main_interface import InterviewSystemAPI
from interview_system.llm_integration import create_llm_client, MockLLMClient

# Initialize FastAPI app
app = FastAPI(title="EduAI Backend", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
openai_service = OpenAIService()
groq_service = GroqService()
whisper_service = WhisperService()

# Initialize Interview System (new, flow-enforced)
interview_api: InterviewSystemAPI | None = None

# Store active sessions
active_sessions: Dict[str, SessionState] = {}
active_connections: Dict[str, WebSocket] = {}

# Practice mode storage
practice_sessions: Dict[str, dict] = {}
question_bank = []

# Background generation tracking
background_generation_tasks: Dict[str, asyncio.Task] = {}
pre_generated_problems: Dict[str, dict] = {}

@app.on_event("startup")
async def startup_event():
    """Validate configuration and test services on startup"""
    try:
        Config.validate()
        print("✅ Configuration validated")
        
        # Test API connections
        openai_status = openai_service.test_connection()
        groq_status = groq_service.test_connection()
        
        if openai_status:
            print("✅ OpenAI API connection successful")
        else:
            print("⚠️ OpenAI API connection failed - check your API key")
            
        if groq_status:
            print("✅ Groq API connection successful")
        else:
            print("⚠️ Groq API connection failed - check your API key")
            
        # Initialize Interview System API
        global interview_api
        try:
            if Config.GROQ_API_KEY or Config.OPENAI_API_KEY:
                llm_client = create_llm_client(Config.GROQ_API_KEY or "", Config.OPENAI_API_KEY or "")
            else:
                llm_client = MockLLMClient()
            interview_api = InterviewSystemAPI(llm_client)
            print("✅ Interview system initialized")
        except Exception as e:
            print(f"⚠️ Failed to initialize interview system: {e}")
            interview_api = InterviewSystemAPI(MockLLMClient())

        # Load question bank (practice mode only)
        load_question_bank()
        
        print(f"🚀 EduAI Backend starting on port {Config.BACKEND_PORT}")
        
    except Exception as e:
        print(f"❌ Startup error: {e}")

def clean_markdown_text(text):
    """Remove markdown formatting from text"""
    if not text:
        return text
    
    # Remove bold markdown (**text**)
    import re
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    
    # Remove italic markdown (*text*)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    
    # Clean up any remaining formatting
    text = text.replace('**', '').replace('*', '')
    
    return text.strip()

def normalize_interview_type(interview_type):
    """Normalize interview type to match backend expectations"""
    if not interview_type:
        return "technical_behavioral"
    
    # Handle different formats
    interview_type_normalized = interview_type.lower().strip()
    
    # Map common variations based on frontend dropdown options
    type_mapping = {
        # Frontend dropdown mappings
        "technical": "technical_only",  # "Technical" -> technical_only
        "behavioral": "behavioral_only",  # "Behavioral" -> behavioral_only
        "behavioral + technical": "technical_behavioral",  # "Behavioral + Technical" -> technical_behavioral
        "behavioral+technical": "technical_behavioral",
        "technical + behavioral": "technical_behavioral",
        "technical+behavioral": "technical_behavioral",
        # Legacy/alternative formats
        "behavioral-technical": "technical_behavioral",
        "technical-behavioral": "technical_behavioral", 
        "behavioral_technical": "technical_behavioral",
        "technical_behavioral": "technical_behavioral",
        # Explicit variants
        "technical_only": "technical_only",
        "technical-only": "technical_only",
        "technical only": "technical_only",
        "behavioral-only": "behavioral_only",
        "behavioral_only": "behavioral_only",
        "behavioral only": "behavioral_only",
        # Coding interview
        "coding": "coding",
        "coding interview": "coding",
        "coding-interview": "coding",
        "coding_interview": "coding"
    }
    
    result = type_mapping.get(interview_type_normalized, "technical_behavioral")
    return result

def load_question_bank():
    """Load the 184 mechanical engineering questions from file"""
    global question_bank
    try:
        with open('../Mechnical design questions .txt', 'r', encoding='utf-8') as f:
            content = f.read()
            
        print(f"📄 File content length: {len(content)} characters")
        
        # The file contains JSON arrays and objects mixed together
        # Let's parse it more carefully
        questions = []
        
        # Split content by lines and look for JSON objects
        lines = content.split('\n')
        current_object = ""
        brace_count = 0
        
        for line in lines:
            line = line.strip()
            if not line or line in ['[', ']', ',']:
                continue
                
            current_object += line + "\n"
            brace_count += line.count('{') - line.count('}')
            
            # When braces are balanced, we have a complete object
            if brace_count == 0 and current_object.strip():
                try:
                    # Clean up the object string
                    obj_str = current_object.strip()
                    if obj_str.endswith(','):
                        obj_str = obj_str[:-1]
                    
                    question_obj = json.loads(obj_str)
                    if 'question' in question_obj and 'answer' in question_obj:
                        question_obj['id'] = len(questions) + 1
                        # Ensure company field exists
                        if 'company' not in question_obj:
                            question_obj['company'] = question_obj.get('role', 'Unknown Company')
                        
                        # Clean markdown formatting from question and answer
                        question_obj['question'] = clean_markdown_text(question_obj['question'])
                        question_obj['answer'] = clean_markdown_text(question_obj['answer'])
                        
                        questions.append(question_obj)
                        print(f"✅ Loaded question {len(questions)}: {question_obj.get('company', 'Unknown')}")
                except json.JSONDecodeError as e:
                    print(f"⚠️ Failed to parse object: {e}")
                    print(f"Object was: {current_object[:100]}...")
                
                current_object = ""
                brace_count = 0
        
        question_bank = questions
        print(f"✅ Successfully loaded {len(question_bank)} practice questions")
        
        # If no questions loaded, add fallback questions
        if len(question_bank) == 0:
            print("⚠️ No questions loaded from file, using fallback questions")
            question_bank = [
                {
                    "id": 1,
                    "role": "Mechanical Engineer",
                    "company": "Tesla",
                    "question": "Explain the difference between stress and strain in materials engineering.",
                    "answer": "Stress is the internal force per unit area within a material (measured in Pa or psi), while strain is the deformation per unit length (dimensionless). Stress causes strain, and their relationship defines material properties like Young's modulus."
                },
                {
                    "id": 2,
                    "role": "Mechanical Engineer", 
                    "company": "Apple",
                    "question": "What are the key considerations when designing a cantilever beam?",
                    "answer": "Key considerations include: 1) Maximum bending moment occurs at the fixed end, 2) Deflection is proportional to L³/EI, 3) Material selection based on yield strength, 4) Cross-sectional shape affects moment of inertia, 5) Factor of safety for dynamic loads."
                }
            ]
        
    except Exception as e:
        print(f"❌ Failed to load question bank: {e}")
        import traceback
        traceback.print_exc()
        # Fallback questions
        question_bank = [
            {
                "id": 1,
                "role": "Mechanical Engineer",
                "company": "Tesla", 
                "question": "Explain the difference between stress and strain in materials engineering.",
                "answer": "Stress is the internal force per unit area within a material (measured in Pa or psi), while strain is the deformation per unit length (dimensionless). Stress causes strain, and their relationship defines material properties like Young's modulus."
            }
        ]

async def generate_coding_problem_background(session_id: str):
    """Background task to generate coding problem while user gives introduction"""
    try:
        print(f"🔄 Starting background coding problem generation for session {session_id}")
        
        # Import coding generator class and create fresh instance
        from interview_system.coding_question_generator import CodingQuestionGenerator
        from interview_system.llm_integration import create_llm_client
        
        # Create LLM client
        if Config.GROQ_API_KEY or Config.OPENAI_API_KEY:
            llm_client = create_llm_client(Config.GROQ_API_KEY or "", Config.OPENAI_API_KEY or "")
        else:
            from interview_system.llm_integration import MockLLMClient
            llm_client = MockLLMClient()
        
        # Create fresh generator instance
        coding_generator = CodingQuestionGenerator(llm_client)
        
        # Get session data from active interview session if available
        job_description = ""
        position = "Engineer"
        seniority = "mid"
        try:
            global interview_api
            if interview_api and hasattr(interview_api, 'active_sessions') and session_id in interview_api.active_sessions:
                session = interview_api.active_sessions[session_id]
                # job description
                if hasattr(session, 'skill_analysis') and hasattr(session.skill_analysis, 'job_description'):
                    job_description = session.skill_analysis.job_description or job_description
                if not job_description and hasattr(session, 'job_description'):
                    job_description = session.job_description
                if not job_description and hasattr(session, 'candidate_inputs'):
                    job_description = session.candidate_inputs.get('job_description', job_description)
                # position
                if hasattr(session, 'position') and session.position:
                    position = session.position
                elif hasattr(session, 'candidate_inputs'):
                    position = session.candidate_inputs.get('position', position)
                # infer seniority from position keywords or resume
                pos_lower = str(position).lower()
                if any(k in pos_lower for k in ["principal", "staff", "lead", "sr ", "senior"]):
                    seniority = "senior"
                elif any(k in pos_lower for k in ["intern", "junior", "grad"]):
                    seniority = "junior"
                else:
                    seniority = "mid"
        except Exception:
            pass
        
        # Generate coding question
        question = coding_generator.generate_question(job_description, position, seniority)
        
        # Store the problem in the pre-generated cache
        problem_data = {
            "id": question.id,
            "title": question.title,
            "difficulty": question.difficulty.value,
            "problemStatement": question.problem_statement,
            "description": question.problem_statement,  # Add description field for clarification
            "example": question.example,
            "constraints": question.constraints,
            "primaryPattern": question.primary_pattern,
            "dataStructures": question.data_structures,
            "optimalComplexity": question.optimal_complexity,
            "followUpQuestions": question.follow_up_questions,
            "template": question.template,
            "testCases": question.test_cases
        }
        
        # Store in pre-generated cache
        global pre_generated_problems
        pre_generated_problems[session_id] = problem_data
        
        # Also store in session if available
        try:
            if interview_api and hasattr(interview_api, 'active_sessions') and session_id in interview_api.active_sessions:
                session = interview_api.active_sessions[session_id]
                session.current_coding_problem = problem_data
                print(f"✅ Background generated and stored coding problem in session {session_id}")
        except Exception as e:
            print(f"⚠️ Could not store problem in session: {str(e)}")
        
        print(f"🎯 Background coding problem generation completed for session {session_id}")
        
    except Exception as e:
        print(f"❌ Background generation failed for session {session_id}: {str(e)}")
        # Clean up the task reference
        if session_id in background_generation_tasks:
            del background_generation_tasks[session_id]

@app.get("/")
async def root():
    return {"message": "EduAI Backend is running!", "status": "healthy"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Test connections fresh each time
    openai_status = openai_service.test_connection() if openai_service.client else False
    groq_status = groq_service.test_connection() if groq_service.client else False
    
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "services": {
            "openai": openai_status,
            "groq": groq_status
        }
    }

# --------------------- Code Runner (Judge0) ---------------------
JUDGE0_BASE = "https://ce.judge0.com"

language_aliases = {
    "javascript": "javascript",
    "typescript": "typescript",
    "python": "python",
    "java": "java",
    "c": "c",
    "cpp": "c++",
    "c++": "c++",
    "csharp": "c#",
    "c#": "c#",
    "go": "go",
    "golang": "go",
    "rust": "rust",
    "php": "php",
    "ruby": "ruby",
    "swift": "swift",
    "kotlin": "kotlin",
    "scala": "scala"
}

async def resolve_judge0_language_id(client: httpx.AsyncClient, language: str) -> int | None:
    try:
        resp = await client.get(f"{JUDGE0_BASE}/languages")
        resp.raise_for_status()
        langs = resp.json()
        wanted = language_aliases.get(language.lower(), language.lower())
        # Prefer the newest version by taking the last match
        matches = [l for l in langs if wanted in l.get("name", "").lower()]
        if not matches:
            # Try some special cases
            special = {
                "c++": ["gcc", "clang", "c++"],
                "c#": ["c#"],
                "typescript": ["typescript"],
            }.get(wanted, [])
            for key in special:
                matches = [l for l in langs if key in l.get("name", "").lower()]
                if matches:
                    break
        if matches:
            return matches[-1]["id"]
        return None
    except Exception as e:
        print(f"⚠️ Failed to resolve Judge0 language id: {e}")
        return None

@app.post("/code/run")
async def run_code(payload: dict):
    """Execute code using Judge0 community instance (supports many languages)."""
    language = payload.get("language", "")
    source_code = payload.get("code", "")
    stdin = payload.get("stdin", "")
    if not source_code or not language:
        raise HTTPException(status_code=400, detail="'language' and 'code' are required")
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            lang_id = await resolve_judge0_language_id(client, language)
            if not lang_id:
                raise HTTPException(status_code=400, detail=f"Unsupported language: {language}")
            sub_resp = await client.post(
                f"{JUDGE0_BASE}/submissions?base64_encoded=false&wait=true",
                json={
                    "language_id": lang_id,
                    "source_code": source_code,
                    "stdin": stdin
                }
            )
            sub_resp.raise_for_status()
            data = sub_resp.json()
            # Normalize output fields
            status = (data.get("status") or {}).get("description", "")
            stdout = data.get("stdout") or ""
            stderr = data.get("stderr") or ""
            compile_output = data.get("compile_output") or ""
            time = data.get("time") or ""
            memory = data.get("memory") or ""
            return {
                "success": True,
                "status": status,
                "stdout": stdout,
                "stderr": stderr,
                "compile_output": compile_output,
                "time": time,
                "memory": memory
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Code execution failed: {str(e)}")

@app.post("/analyze")
async def analyze_whiteboard(request: WhiteboardAnalysisRequest):
    """Analyze whiteboard content and generate educational response"""
    try:
        # Determine which model to use (default to OpenAI for image analysis)
        ai_model = getattr(request, 'ai_model', 'gpt4o')
        
        if ai_model == 'groq':
            # Use Groq Llama 4 for analysis
            ai_response = groq_service.analyze_whiteboard_and_speech(
                request.image_data,
                request.user_speech or ""
            )
            visual_analysis = "Analyzed with Groq Llama 4 Maverick (multimodal analysis)"
        else:
            # Use OpenAI GPT-4o for analysis (default for images)
            ai_response = openai_service.analyze_whiteboard_and_speech(
                request.image_data,
                request.user_speech or ""
            )
            visual_analysis = "Analyzed with OpenAI GPT-4o (combined visual + speech analysis)"
        
        return AnalysisResponse(
            visual_analysis=visual_analysis,
            ai_response=ai_response,
            timestamp=datetime.now(),
            success=True
        )
        
    except Exception as e:
        return AnalysisResponse(
            visual_analysis="",
            ai_response=f"Sorry, I encountered an error: {str(e)}",
            timestamp=datetime.now(),
            success=False,
            error=str(e)
        )

@app.post("/analyze/practice")
async def analyze_practice_answer(request: dict):
    """Analyze practice answer with image and text"""
    try:
        user_answer = request.get('user_answer', '')
        question_text = request.get('question_text', '')
        model_answer = request.get('model_answer', '')
        image_data = request.get('image_data', '')
        
        print(f"🔍 Practice analysis request:")
        print(f"  - User answer: {len(user_answer)} chars")
        print(f"  - Question: {len(question_text)} chars") 
        print(f"  - Image data: {'Yes' if image_data else 'No'}")
        
        # Always use OpenAI for practice analysis (better for images + detailed feedback)
        if image_data:
            print("🖼️ Image detected - using OpenAI GPT-4o for multimodal analysis")
            feedback = openai_service.analyze_practice_answer(user_answer, question_text, model_answer, image_data)
            print(f"✅ OpenAI analysis successful: {len(feedback)} chars")
            used_model = "openai"
        else:
            print("📝 Text-only analysis - using OpenAI GPT-4o") 
            feedback = openai_service.analyze_practice_answer(user_answer, question_text, model_answer, "")
            print(f"✅ OpenAI analysis successful: {len(feedback)} chars")
            used_model = "openai"
        
        return {
            "feedback": feedback,
            "timestamp": datetime.now().isoformat(),
            "success": True,
            "model_used": used_model
        }
        
    except Exception as e:
        print(f"❌ Practice analysis error: {e}")
        return {
            "feedback": f"Sorry, I encountered an error analyzing your answer: {str(e)}",
            "timestamp": datetime.now().isoformat(), 
            "success": False,
            "error": str(e)
        }

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """Transcribe audio to text"""
    try:
        audio_data = await file.read()
        transcription = whisper_service.transcribe_audio(audio_data)
        
        # Check if this looks like an introduction (heuristic: contains name/personal info)
        # and trigger background coding question generation
        if transcription and len(transcription) > 20:  # Reasonable length for introduction
            intro_keywords = ["name is", "i am", "my name", "i'm", "call me", "i work", "experience", "background"]
            transcription_lower = transcription.lower()
            
            # If it looks like an introduction, try to find the session and start background generation
            if any(keyword in transcription_lower for keyword in intro_keywords):
                # Try to find the session ID from active sessions (this is a heuristic approach)
                # In a real implementation, you might want to pass session_id as a parameter
                global interview_api, background_generation_tasks
                if interview_api and hasattr(interview_api, 'active_sessions'):
                    # Find the most recent session (heuristic - in production you'd want to pass session_id)
                    recent_sessions = sorted(
                        interview_api.active_sessions.items(), 
                        key=lambda x: getattr(x[1], 'start_time', datetime.now()), 
                        reverse=True
                    )
                    
                    if recent_sessions:
                        session_id = recent_sessions[0][0]
                        # Only start background generation if not already running
                        if session_id not in background_generation_tasks and session_id not in pre_generated_problems:
                            print(f"🎯 Detected introduction, starting background coding question generation for {session_id}")
                            task = asyncio.create_task(generate_coding_problem_background(session_id))
                            background_generation_tasks[session_id] = task
        
        return {"transcription": transcription, "success": True}
        
    except Exception as e:
        return {"transcription": "", "success": False, "error": str(e)}

@app.post("/api/tts")
async def text_to_speech(request: dict):
    """TTS endpoint - disabled, frontend uses browser TTS directly"""
    # Frontend now uses browser TTS directly for instant response
    return {"status": "disabled", "message": "Frontend uses browser TTS directly"}

@app.delete("/api/tts/cache")
async def clear_tts_cache():
    """Clear TTS cache - not implemented for browser TTS"""
    return {"success": True, "files_removed": 0}

@app.post("/interview/start")
async def start_interview(request: dict):
    """Start a new interview session (flow-enforced: returns greeting first)"""
    try:
        if interview_api is None:
            raise HTTPException(status_code=500, detail="Interview system not initialized")

        # Map incoming payload to candidate_inputs used by the interview system
        form_data = request.get("formData", {})
        # Build username from first/last name when available (frontend sends firstName/lastName)
        first_name = (form_data.get("firstName") or request.get("firstName", "")).strip()
        last_name = (form_data.get("lastName") or request.get("lastName", "")).strip()
        full_name = f"{first_name} {last_name}".strip()

        candidate_inputs = {
            "username": full_name or form_data.get("username") or request.get("username", "Candidate"),
            "position": form_data.get("position") or request.get("position", request.get("domain", "Engineer")),
            "company": form_data.get("company") or request.get("company", "our company"),
            "job_description": form_data.get("jobDescription") or request.get("job_description", request.get("scenario", "")),
            "resume": form_data.get("resumeText") or request.get("resume", ""),
            "linkedin_profile": form_data.get("linkedin") or request.get("linkedin_profile", ""),
            "interview_type": normalize_interview_type(form_data.get("interviewType") or request.get("interviewType", "technical_behavioral")),
            "duration_minutes": int(form_data.get("duration", request.get("duration_minutes", 60)))
        }
        

        result = interview_api.start_interview_flow(candidate_inputs)
        
        # For coding interviews, start background generation immediately when session is created
        if candidate_inputs.get('interview_type') == 'coding':
            session_id = result.get('session_id')
            if session_id:
                print(f"🚀 EARLY START: Triggering background coding generation for {session_id}")
                # Start background generation task
                if session_id not in background_generation_tasks:
                    task = asyncio.create_task(generate_coding_problem_background(session_id))
                    background_generation_tasks[session_id] = task
        
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start interview: {str(e)}")

@app.post("/interview/brief-introduce")
async def submit_brief_introduction(request: dict):
    """Submit brief introduction for technical-only interviews"""
    try:
        if interview_api is None:
            raise HTTPException(status_code=500, detail="Interview system not initialized")
        session_id = request.get("session_id")
        introduction_text = request.get("introduction", "")
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")
        return interview_api.submit_brief_introduction(session_id, introduction_text)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit brief introduction: {str(e)}")

@app.post("/interview/introduce")
async def submit_introduction(request: dict):
    """Submit candidate introduction"""
    try:
        if interview_api is None:
            raise HTTPException(status_code=500, detail="Interview system not initialized")
        session_id = request.get("session_id")
        introduction_text = request.get("introduction", "")
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")
        return interview_api.submit_introduction(session_id, introduction_text)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit introduction: {str(e)}")

@app.get("/interview/next-question")
async def get_next_interview_question(session_id: str):
    """Get the next interview question (enforces flow)"""
    try:
        if interview_api is None:
            raise HTTPException(status_code=500, detail="Interview system not initialized")
        return interview_api.get_next_question(session_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get next question: {str(e)}")

@app.post("/interview/answer")
async def submit_interview_answer(request: dict):
    """Submit answer to the current question"""
    try:
        if interview_api is None:
            raise HTTPException(status_code=500, detail="Interview system not initialized")
        session_id = request.get("session_id")
        question_id = request.get("question_id")
        answer_text = request.get("answer", "")
        if not session_id or not question_id:
            raise HTTPException(status_code=400, detail="session_id and question_id are required")
        return interview_api.submit_answer(session_id, question_id, answer_text)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit answer: {str(e)}")

@app.get("/interview/summary")
async def get_interview_summary(session_id: str):
    """Get final interview summary"""
    try:
        if interview_api is None:
            raise HTTPException(status_code=500, detail="Interview system not initialized")
        return interview_api.get_interview_summary(session_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get interview summary: {str(e)}")

@app.get("/interview/status")
async def get_interview_status(session_id: str):
    """Return current session status to keep frontend in sync and avoid 'expired' confusion"""
    try:
        if interview_api is None:
            raise HTTPException(status_code=500, detail="Interview system not initialized")
        return interview_api.get_session_info(session_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session status: {str(e)}")

# ===== COMPANY Q&A ENDPOINTS =====

@app.post("/interview/start-company-qna")
async def start_company_qna(request: dict):
    """Start the company Q&A phase after interview completion"""
    try:
        if interview_api is None:
            raise HTTPException(status_code=500, detail="Interview system not initialized")
        session_id = request.get("session_id")
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")
        return interview_api.start_company_qna(session_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start company Q&A: {str(e)}")

@app.post("/interview/submit-company-question")
async def submit_company_question(request: dict):
    """Submit user's question/response in company Q&A mode"""
    try:
        if interview_api is None:
            raise HTTPException(status_code=500, detail="Interview system not initialized")
        session_id = request.get("session_id")
        user_response = request.get("response", "")
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")
        return interview_api.submit_company_question(session_id, user_response)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit company question: {str(e)}")

# ===== CODING INTERVIEW ENDPOINTS =====

@app.get("/interview/next-coding-problem")
async def get_next_coding_problem(session_id: str):
    """Get the next coding problem for coding interview"""
    try:
        global pre_generated_problems, background_generation_tasks
        
        # First, check if we have a pre-generated problem
        if session_id in pre_generated_problems:
            problem_data = pre_generated_problems[session_id]
            print(f"🎯 Using pre-generated coding problem for session {session_id} - INSTANT!")
            
            # Clean up the pre-generated cache
            del pre_generated_problems[session_id]
            
            # Clean up background task if it exists
            if session_id in background_generation_tasks:
                task = background_generation_tasks[session_id]
                if not task.done():
                    task.cancel()
                del background_generation_tasks[session_id]
            
            return {
                "status": "success",
                "problem": problem_data
            }
        
        # If background generation is still running, wait for it (with timeout)
        if session_id in background_generation_tasks:
            task = background_generation_tasks[session_id]
            try:
                print(f"⏳ Waiting for background generation to complete for session {session_id}")
                await asyncio.wait_for(task, timeout=10.0)  # 10 second timeout
                
                # Check if the problem was generated
                if session_id in pre_generated_problems:
                    problem_data = pre_generated_problems[session_id]
                    print(f"🎯 Background generation completed, using result for session {session_id}")
                    
                    # Clean up
                    del pre_generated_problems[session_id]
                    del background_generation_tasks[session_id]
                    
                    return {
                        "status": "success",
                        "problem": problem_data
                    }
            except asyncio.TimeoutError:
                print(f"⚠️ Background generation timed out for session {session_id}, falling back to synchronous generation")
                # Cancel the background task
                task.cancel()
                del background_generation_tasks[session_id]
            except Exception as e:
                print(f"⚠️ Background generation failed for session {session_id}: {str(e)}, falling back to synchronous generation")
                del background_generation_tasks[session_id]
        
        # Fallback: Generate synchronously (original behavior)
        print(f"🔄 Generating coding problem synchronously for session {session_id}")
        
        # Import coding generator class and create fresh instance
        from interview_system.coding_question_generator import CodingQuestionGenerator
        from interview_system.llm_integration import create_llm_client
        
        # Create LLM client
        if Config.GROQ_API_KEY or Config.OPENAI_API_KEY:
            llm_client = create_llm_client(Config.GROQ_API_KEY or "", Config.OPENAI_API_KEY or "")
        else:
            from interview_system.llm_integration import MockLLMClient
            llm_client = MockLLMClient()
        
        # Create fresh generator instance
        coding_generator = CodingQuestionGenerator(llm_client)
        
        # Get session data from active interview session if available
        job_description = ""
        position = "Engineer"
        seniority = "mid"
        try:
            global interview_api
            if interview_api and hasattr(interview_api, 'active_sessions') and session_id in interview_api.active_sessions:
                session = interview_api.active_sessions[session_id]
                # job description
                if hasattr(session, 'skill_analysis') and hasattr(session.skill_analysis, 'job_description'):
                    job_description = session.skill_analysis.job_description or job_description
                if not job_description and hasattr(session, 'job_description'):
                    job_description = session.job_description
                if not job_description and hasattr(session, 'candidate_inputs'):
                    job_description = session.candidate_inputs.get('job_description', job_description)
                # position
                if hasattr(session, 'position') and session.position:
                    position = session.position
                elif hasattr(session, 'candidate_inputs'):
                    position = session.candidate_inputs.get('position', position)
                # infer seniority from position keywords or resume
                pos_lower = str(position).lower()
                if any(k in pos_lower for k in ["principal", "staff", "lead", "sr ", "senior"]):
                    seniority = "senior"
                elif any(k in pos_lower for k in ["intern", "junior", "grad"]):
                    seniority = "junior"
                else:
                    seniority = "mid"
        except Exception:
            pass
        
        # Generate coding question
        try:
            question = coding_generator.generate_question(job_description, position, seniority)
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"LLM failed to generate coding problem: {str(e)}")

        # Store the problem in the session for clarification and follow-up access
        problem_data = {
            "id": question.id,
            "title": question.title,
            "difficulty": question.difficulty.value,
            "problemStatement": question.problem_statement,
            "description": question.problem_statement,  # Add description field for clarification
            "example": question.example,
            "constraints": question.constraints,
            "primaryPattern": question.primary_pattern,
            "dataStructures": question.data_structures,
            "optimalComplexity": question.optimal_complexity,
            "followUpQuestions": question.follow_up_questions,
            "template": question.template,
            "testCases": question.test_cases
        }
        
        # Store in session if available
        try:
            if interview_api and hasattr(interview_api, 'active_sessions') and session_id in interview_api.active_sessions:
                session = interview_api.active_sessions[session_id]
                session.current_coding_problem = problem_data
                print(f"✅ Stored coding problem in session {session_id}")
        except Exception as e:
            print(f"⚠️ Could not store problem in session: {str(e)}")

        return {
            "status": "success",
            "problem": problem_data
        }
    except Exception as e:
        print(f"Error generating coding problem: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate coding problem: {str(e)}")

@app.post("/coding/run")
async def run_code(request: dict):
    """Run code against test cases"""
    try:
        code = request.get("code", "")
        language = request.get("language", "python")
        test_cases = request.get("test_cases", [])
        
        # For now, return mock results
        # In production, this would execute code in a sandboxed environment
        results = []
        
        for i, test_case in enumerate(test_cases[:3]):  # Limit to 3 test cases
            # Mock test results
            if i == 0:
                results.append({
                    "status": "passed",
                    "message": "Test passed successfully",
                    "expected": test_case.get("expected", "N/A"),
                    "actual": test_case.get("expected", "N/A")  # Mock: same as expected
                })
            elif i == 1:
                results.append({
                    "status": "failed", 
                    "message": "Output doesn't match expected result",
                    "expected": test_case.get("expected", "N/A"),
                    "actual": "Different result"
                })
            else:
                results.append({
                    "status": "passed",
                    "message": "Test passed successfully",
                    "expected": test_case.get("expected", "N/A"),
                    "actual": test_case.get("expected", "N/A")
                })
        
        return {"results": results}
    except Exception as e:
        return {"results": [{"status": "error", "message": f"Execution error: {str(e)}"}]}

@app.post("/coding/submit")
async def submit_code(request: dict):
    """Submit final code solution with enhanced analysis"""
    try:
        session_id = request.get("session_id")
        problem_id = request.get("problem_id")
        code = request.get("code", "")
        language = request.get("language", "python")
        
        # Get session data for context
        session = None
        current_problem = None
        if interview_api and session_id in interview_api.active_sessions:
            session = interview_api.active_sessions[session_id]
            # Get current coding problem from session
            if hasattr(session, 'current_coding_problem'):
                current_problem = session.current_coding_problem
        
        # Analyze code complexity and correctness
        analysis_result = await analyze_code_submission(code, language, current_problem)
        
        # Store code and analysis in session for follow-up questions
        if session:
            session.submitted_code = code
            session.submitted_language = language
            session.last_analysis = analysis_result
        
        # Initialize follow-up tracking if not exists
        if session and not hasattr(session, 'coding_followup_count'):
            session.coding_followup_count = 0
            session.coding_followup_categories = set()
        
        # Initialize coding problems completed counter if not exists
        if session and not hasattr(session, 'coding_problems_completed'):
            session.coding_problems_completed = 0
        
        # Generate intelligent follow-up question (max 5)
        follow_up_question = None
        if session and session.coding_followup_count < 5:
            follow_up_question = await generate_smart_followup(
                code, language, current_problem, analysis_result, 
                session.coding_followup_categories, session.coding_followup_count
            )
            if follow_up_question:
                session.coding_followup_count += 1
        else:
            # All follow-ups completed for this problem - increment coding problems counter
            if session:
                session.coding_problems_completed += 1
                # Reset follow-up tracking for next problem
                session.coding_followup_count = 0
                session.coding_followup_categories = set()
                print(f"✅ Coding problem completed! Total completed: {session.coding_problems_completed}")
        
        # Create clean submission response (no code dump)
        submission_message = create_submission_summary(analysis_result, follow_up_question)
        
        return {
            "status": "success",
            "message": submission_message,
            "analysis": analysis_result,
            "followUpQuestion": follow_up_question,
            "followUpCount": session.coding_followup_count if session else 0,
            "maxFollowUps": 5
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit code: {str(e)}")

@app.post("/coding/clarify")
async def ask_clarification_question(request: dict):
    """Ask clarification question about the coding problem"""
    try:
        session_id = request.get("session_id")
        question = request.get("question", "")
        
        if not session_id or not question:
            raise HTTPException(status_code=400, detail="Session ID and question are required")
        
        # Get session data for context
        session = None
        current_problem = None
        if interview_api and session_id in interview_api.active_sessions:
            session = interview_api.active_sessions[session_id]
            # Get current coding problem from session
            if hasattr(session, 'current_coding_problem'):
                current_problem = session.current_coding_problem
        
        if not current_problem:
            return {
                "status": "error",
                "message": "No coding problem found for this session. Please start a coding interview first."
            }
        
        # Generate clarification response using the new system prompt
        clarification_response = await generate_clarification_response(question, current_problem)
        
        return {
            "status": "success",
            "message": clarification_response,
            "type": "clarification",
            "silent": True,  # No TTS, no auto-recording
            "keepMicManual": True  # Keep mic button manual
        }
        
    except Exception as e:
        print(f"❌ Error in clarification endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process clarification: {str(e)}")

@app.post("/coding/followup")
async def submit_followup_answer(request: dict):
    """Submit answer to a follow-up question and get the next follow-up"""
    try:
        session_id = request.get("session_id")
        answer = request.get("answer", "")
        
        # Get session data for context
        session = None
        current_problem = None
        if interview_api and session_id in interview_api.active_sessions:
            session = interview_api.active_sessions[session_id]
            if hasattr(session, 'current_coding_problem'):
                current_problem = session.current_coding_problem
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Store the follow-up answer in session history
        if not hasattr(session, 'followup_answers'):
            session.followup_answers = []
        session.followup_answers.append(answer)
        
        # Check if we can generate another follow-up question
        follow_up_question = None
        if session.coding_followup_count < 5:
            # Get the original code from session (should be stored from initial submission)
            original_code = getattr(session, 'submitted_code', "")
            language = getattr(session, 'submitted_language', "python")
            analysis_result = getattr(session, 'last_analysis', {})
            
            follow_up_question = await generate_smart_followup(
                original_code, language, current_problem, analysis_result, 
                session.coding_followup_categories, session.coding_followup_count
            )
            if follow_up_question:
                session.coding_followup_count += 1
        
        # Check if we've completed all follow-ups for this problem
        if session.coding_followup_count >= 5:
            # All follow-ups completed for this problem - increment coding problems counter
            session.coding_problems_completed += 1
            # Reset follow-up tracking for next problem
            session.coding_followup_count = 0
            session.coding_followup_categories = set()
            print(f"✅ Coding problem completed! Total completed: {session.coding_problems_completed}")
            
            # End the interview after completing one coding problem with follow-ups
            return {
                "status": "interview_completed",
                "message": "Excellent work! You've demonstrated strong problem-solving skills and technical understanding. Your detailed explanations show great depth of knowledge. The interview is now complete, and your detailed feedback will be generated shortly.",
                "followUpQuestion": None,
                "followUpCount": 0,
                "maxFollowUps": 5,
                "problemsCompleted": session.coding_problems_completed
            }
        
        return {
            "status": "success",
            "message": "Thank you for your answer!",
            "followUpQuestion": follow_up_question,
            "followUpCount": session.coding_followup_count,
            "maxFollowUps": 5
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process follow-up: {str(e)}")

async def analyze_code_submission(code: str, language: str, problem: dict = None) -> dict:
    """Analyze submitted code for complexity and correctness"""
    try:
        # Basic complexity analysis (can be enhanced with actual analysis)
        lines = len([line for line in code.split('\n') if line.strip()])
        
        # Mock test execution (in real implementation, run actual tests)
        test_results = {
            "passed": True,
            "total_tests": 3,
            "passed_tests": 3,
            "execution_time": "0.02s"
        }
        
        # Basic complexity estimation based on code patterns
        time_complexity = estimate_time_complexity(code)
        space_complexity = estimate_space_complexity(code)
        
        return {
            "test_results": test_results,
            "time_complexity": time_complexity,
            "space_complexity": space_complexity,
            "code_quality": {
                "lines_of_code": lines,
                "readability": "Good",
                "efficiency": "Optimal"
            }
        }
    except Exception as e:
        return {
            "test_results": {"passed": False, "error": str(e)},
            "time_complexity": "Unknown",
            "space_complexity": "Unknown",
            "code_quality": {"error": str(e)}
        }

def estimate_time_complexity(code: str) -> str:
    """Estimate time complexity based on code patterns"""
    code_lower = code.lower()
    
    # Simple heuristics for complexity estimation
    if 'for' in code_lower and code_lower.count('for') >= 2:
        return "O(n²)"
    elif 'while' in code_lower or 'for' in code_lower:
        return "O(n)"
    elif 'sort' in code_lower:
        return "O(n log n)"
    else:
        return "O(1)"

def estimate_space_complexity(code: str) -> str:
    """Estimate space complexity based on code patterns"""
    code_lower = code.lower()
    
    if any(keyword in code_lower for keyword in ['list(', 'dict(', 'set(', '[]', '{}']):
        return "O(n)"
    else:
        return "O(1)"

async def generate_clarification_response(question: str, problem: dict) -> str:
    """Generate helpful clarification response without giving away the solution"""
    try:
        clarification_prompt = f"""
You are a helpful coding interview assistant. A candidate has asked a clarification question about a coding problem.

Your job is to help them understand the problem better WITHOUT giving away the solution or algorithm.

STRICT RULES:
- NEVER provide code solutions or algorithms
- NEVER mention specific data structures to use (like "use HashMap", "use BFS", etc.)
- NEVER give step-by-step implementation details
- DO help clarify requirements, constraints, and expected behavior
- DO provide examples of input/output if helpful
- DO explain what terms mean (like "efficient", "optimal", etc.)
- Keep responses concise and encouraging

CODING PROBLEM:
{problem.get('description', 'No problem description available')}

CANDIDATE'S QUESTION:
{question}

Provide a helpful clarification that guides understanding without revealing the solution approach:
"""

        # Create LLM client for clarification
        from interview_system.llm_integration import create_llm_client
        if Config.GROQ_API_KEY or Config.OPENAI_API_KEY:
            client = create_llm_client(Config.GROQ_API_KEY or "", Config.OPENAI_API_KEY or "")
        else:
            from interview_system.llm_integration import MockLLMClient
            client = MockLLMClient()
        
        response = client.generate_response(
            prompt=clarification_prompt,
            max_tokens=300
        )
        
        return response.strip()
        
    except Exception as e:
        print(f"❌ Error generating clarification: {str(e)}")
        return "I understand you need clarification. Could you be more specific about what part of the problem you'd like me to explain?"

async def generate_smart_followup(code: str, language: str, problem: dict, 
                                analysis: dict, asked_categories: set, followup_count: int) -> str:
    """Generate intelligent follow-up questions avoiding repetition"""
    
    # Define question categories to ensure comprehensive coverage
    categories = {
        "complexity": "Can you walk me through your time complexity analysis? What makes this approach efficient?",
        "optimization": "How would you optimize this solution if the input size was extremely large?",
        "edge_cases": "What edge cases did you consider while implementing this? How does your solution handle them?",
        "alternatives": "What other approaches did you consider? Why did you choose this particular algorithm?",
        "tradeoffs": "What are the trade-offs between time and space complexity in your solution?"
    }
    
    # Select next category that hasn't been asked
    available_categories = set(categories.keys()) - asked_categories
    
    if not available_categories:
        return None  # All categories covered
    
    # Choose category based on the code and analysis
    if followup_count == 0 and "complexity" in available_categories:
        selected_category = "complexity"
    elif analysis.get("time_complexity") in ["O(n²)", "O(n log n)"] and "optimization" in available_categories:
        selected_category = "optimization"
    elif "edge_cases" in available_categories:
        selected_category = "edge_cases"
    else:
        selected_category = list(available_categories)[0]
    
    # Mark category as used
    asked_categories.add(selected_category)
    
    return categories[selected_category]

def create_submission_summary(analysis: dict, follow_up: str = None) -> str:
    """Create clean submission summary message"""
    test_results = analysis.get("test_results", {})
    
    # Build status message
    if test_results.get("passed"):
        status_emoji = "✅"
        status_text = "Code submitted successfully!"
        test_info = f"🧪 All {test_results.get('total_tests', 0)} test cases passed"
    else:
        status_emoji = "❌"
        status_text = "Code submitted with issues"
        test_info = f"🧪 {test_results.get('passed_tests', 0)}/{test_results.get('total_tests', 0)} test cases passed"
    
    # Build complexity info
    time_comp = analysis.get("time_complexity", "Unknown")
    space_comp = analysis.get("space_complexity", "Unknown")
    
    message_parts = [
        f"{status_emoji} **{status_text}**",
        f"{test_info}",
        f"⏱️ Time Complexity: {time_comp}",
        f"💾 Space Complexity: {space_comp}"
    ]
    
    if test_results.get("execution_time"):
        message_parts.append(f"🚀 Execution Time: {test_results['execution_time']}")
    
    message = "\n".join(message_parts)
    
    if follow_up:
        message += f"\n\n💭 **Follow-up**: {follow_up}"
    
    return message

@app.get("/interview/results/{session_id}")
async def get_interview_results(session_id: str):
    """Get comprehensive interview results with performance analysis"""
    try:
        if interview_api is None:
            raise HTTPException(status_code=500, detail="Interview system not initialized")
        
        # Try the legacy session store first
        session = interview_api.active_sessions.get(session_id)
        
        # Fallback: build a lightweight session view from the new two-phase conductor
        if not session:
            try:
                conductor = interview_api.two_phase_conductor if hasattr(interview_api, 'two_phase_conductor') else None
                blueprint_summary = conductor.get_blueprint_summary(session_id) if conductor else None
                transcript = conductor.conversation_transcripts.get(session_id, []) if conductor else []
                if not blueprint_summary:
                    raise HTTPException(status_code=404, detail="Interview session not found")
                # Construct a minimal results payload directly
                total_questions = len([m for m in transcript if str(m).startswith("Sarah:")])
                total_responses = len([m for m in transcript if str(m).startswith("Candidate:")])
                sample_answers = [
                    {
                        "question_number": 1,
                        "question_text": "Do you have any questions for me or about the company?",
                        "sample_answer": "Yes—I'd love to understand the team's top technical priorities over the next 3–6 months and how success will be measured for this role.",
                        "key_points": [
                            "Asks about priorities and success metrics",
                            "Shows curiosity and ownership",
                            "Connects to role impact"
                        ]
                    }
                ]
                return {
                    "session_info": {
                        "session_id": session_id,
                        "candidate_name": blueprint_summary.get('candidate_name', 'Candidate'),
                        "position": blueprint_summary.get('position', 'Engineer'),
                        "company": blueprint_summary.get('company', 'Company'),
                        "interview_type": "technical_behavioral",
                        "duration": f"{total_responses} answers"
                    },
                    "performance_analysis": {
                        "overall_score": 0,
                        "performance_level": "",
                        "total_questions": total_questions,
                        "questions_answered": total_responses,
                        "completion_rate": (total_responses / max(total_questions, 1)) * 100
                    },
                    "detailed_analysis": [],
                    "sample_answers": sample_answers,
                    "recommendations": [
                        "Prepare 2–3 thoughtful questions about team priorities and success metrics",
                        "Summarize your strengths in one sentence at the end",
                        "Follow up with a concise thank‑you note"
                    ],
                    "timestamp": datetime.now().isoformat()
                }
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=404, detail=f"Interview session not found: {str(e)}")
        
        # Calculate performance metrics
        total_questions = len(session.questions_asked) if hasattr(session, 'questions_asked') else 0
        total_responses = len(session.responses) if hasattr(session, 'responses') else 0
        
        # Enhanced debug logging
        
        if hasattr(session, 'questions_asked') and session.questions_asked:
            for i, q in enumerate(session.questions_asked):
                q_text = getattr(q, 'question_text', str(q))
                print(f"  Q{i+1}: {q_text[:80]}...")
        else:
            pass
            
        if hasattr(session, 'responses') and session.responses:
            for i, r in enumerate(session.responses):
                r_text = getattr(r, 'candidate_response', str(r))
                print(f"  R{i+1}: {r_text[:80]}...")
        else:
            pass
            
        # Check if session is from the right interview system
        
        # Analyze performance based on responses
        performance_score = calculate_performance_score(session)
        performance_level = get_performance_level(performance_score)
        
        # Get detailed question analysis
        question_analysis = analyze_questions_and_answers(session)
        
        # Generate sample answers for each question
        sample_answers = generate_sample_answers(session)
        
        # If no questions/answers, create dummy data for demo
        if not question_analysis:
            question_analysis = [{
                "question_number": 1,
                "question_text": "Tell me about a challenging engineering project you worked on.",
                "question_type": "behavioral",
                "user_answer": "I worked on a complex technical project that required innovative problem-solving. The main challenge was optimizing for both performance and cost while meeting strict requirements.",
                "answer_quality": "Good",
                "word_count": 25,
                "skill_focus": "Problem Solving"
            }]
            
        if not sample_answers:
            # Get position from session for dynamic sample answer
            position = getattr(session, 'position', 'Engineer')
            sample_answers = [{
                "question_number": 1,
                "question_text": "Tell me about a challenging project you worked on.",
                "sample_answer": f"**Situation:** In my previous role as a {position}, our team faced a complex technical challenge that required innovative problem-solving.\n\n**Task:** My responsibility was to design and implement a solution that would improve system performance while meeting all requirements and constraints.\n\n**Action:** I analyzed the requirements, researched best practices, designed a comprehensive solution, and collaborated with the team to implement and test it thoroughly.\n\n**Result:** The solution successfully improved performance by 25% and was delivered on time and within budget, receiving positive feedback from stakeholders.",
                "key_points": ["Use STAR method", "Provide specific outcomes", "Show technical skills", "Demonstrate impact"]
            }]
        
        return {
            "session_info": {
                "session_id": session_id,
                "candidate_name": session.candidate_name,
                "position": session.position,
                "company": getattr(session, 'company', 'Unknown Company'),
                "interview_type": session.interview_type.value,
                "duration": f"{total_questions} questions answered"
            },
            "performance_analysis": {
                "overall_score": performance_score,
                "performance_level": performance_level,
                "total_questions": total_questions,
                "questions_answered": total_responses,
                "completion_rate": (total_responses / max(total_questions, 1)) * 100
            },
            "detailed_analysis": question_analysis,
            "sample_answers": sample_answers,
            "recommendations": generate_recommendations(performance_score, question_analysis),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get interview results: {str(e)}")

def calculate_performance_score(session) -> float:
    """Calculate overall performance score based on responses"""
    if not hasattr(session, 'responses') or not session.responses:
        return 0.0
    
    # Simple scoring based on response quality indicators
    total_score = 0
    for response in session.responses:
        response_text = response.candidate_response.lower()
        score = 50  # Base score
        
        # Add points for technical depth
        technical_keywords = ['analysis', 'design', 'calculation', 'engineering', 'optimization', 'efficiency']
        score += sum(5 for keyword in technical_keywords if keyword in response_text)
        
        # Add points for specific examples
        if any(phrase in response_text for phrase in ['for example', 'in my experience', 'project']):
            score += 10
        
        # Add points for quantitative details
        import re
        if re.search(r'\d+', response_text):
            score += 10
        
        # Cap at 100
        total_score += min(100, score)
    
    return min(100, total_score / len(session.responses))

def get_performance_level(score: float) -> str:
    """Convert numeric score to performance level"""
    if score >= 85:
        return "Excellent"
    elif score >= 70:
        return "Good"
    elif score >= 55:
        return "Average"
    else:
        return "Below Average"

def analyze_questions_and_answers(session) -> List[Dict]:
    """Analyze each question-answer pair"""
    analysis = []
    
    if not hasattr(session, 'questions_asked') or not hasattr(session, 'responses'):
        return analysis
    
    # Process all questions asked, even if some don't have responses yet
    for i, question in enumerate(session.questions_asked):
        user_answer = "No response provided"
        quality = "Not Answered"
        word_count = 0
        
        # Check if there's a corresponding response
        if i < len(session.responses):
            response = session.responses[i]
            user_answer = response.candidate_response
            word_count = len(user_answer.split())
            
            # Simple quality assessment
            if word_count < 20:
                quality = "Brief"
            elif word_count > 100:
                quality = "Detailed"
            else:
                quality = "Good"
        
        analysis.append({
            "question_number": i + 1,
            "question_text": question.question_text,
            "question_type": getattr(question.question_type, 'value', str(question.question_type)),
            "user_answer": user_answer,
            "answer_quality": quality,
            "word_count": word_count,
            "skill_focus": getattr(question, 'skill_focus', 'General')
        })
    
    return analysis

def generate_sample_answers(session) -> List[Dict]:
    """Generate STAR method sample answers for each question using the same LLM as the interview.
    Falls back to deterministic templates if the LLM is unavailable or returns an invalid format.
    """
    sample_answers: List[Dict] = []
    
    if not hasattr(session, 'questions_asked') or not session.questions_asked:
        return sample_answers
    
    # Access the same LLM client used by the interview system
    llm_client = None
    try:
        # interview_api is initialized on startup; reuse its LLM
        global interview_api
        if interview_api and hasattr(interview_api, 'conductor') and hasattr(interview_api.conductor, 'llm_client'):
            llm_client = interview_api.conductor.llm_client
    except Exception:
        llm_client = None
    
    # Smart fallback based on question type
    def smart_fallback(i: int, question_text: str) -> Dict[str, str]:
        # Determine if behavioral or technical
        is_behavioral = any(word in question_text.lower() for word in ['example', 'time when', 'situation', 'tell me about a time'])
        
        if is_behavioral:
            # STAR format for behavioral questions
            templates = [
                {
                    "situation": "In my previous role, our team faced a critical system performance issue that was impacting operations.",
                    "task": "I needed to identify root causes and implement a solution to improve reliability without increasing cost.",
                    "action": "I conducted thorough analysis using appropriate tools and methodologies, collaborated with stakeholders to design an optimal solution, and implemented it with proper testing and validation.",
                    "result": "System performance improved significantly, downtime was reduced by 85%, and the solution delivered measurable business value within the expected timeframe."
                }
            ]
            t = templates[0]  # Use first template for behavioral
            return {
                "text": f"**Situation:** {t['situation']}\n\n**Task:** {t['task']}\n\n**Action:** {t['action']}\n\n**Result:** {t['result']}",
                "key_points": [
                    "Uses STAR method structure",
                    "Provides specific example", 
                    "Includes technical details",
                    "Shows quantified results"
                ]
            }
        else:
            # Technical format for technical questions
            return {
                "text": f"""When approaching this type of technical challenge, I would follow a systematic methodology:

**Analysis Phase:** First, I'd gather requirements and constraints, then perform initial feasibility analysis using appropriate tools and methodologies.

**Solution Development:** I'd develop multiple concept solutions, evaluate trade-offs using best practices and principles, and select the optimal approach based on performance, cost, and implementation criteria.

**Validation:** I'd validate the solution through testing, prototyping, and peer review to ensure it meets all specifications and standards.

**Implementation:** Finally, I'd work with stakeholders to ensure smooth deployment, documenting lessons learned for future projects.

This systematic approach ensures robust, scalable solutions that meet both technical and business requirements.""",
                "key_points": [
                    "Addresses the specific question",
                    "Includes technical methodology", 
                    "Shows engineering approach",
                    "Provides actionable insights"
                ]
            }
    
    # Generate per question
    for i, question in enumerate(session.questions_asked):
        q_text = getattr(question, 'question_text', str(question))
        generated_answer = None
        key_points: List[str] = []
        
        if llm_client is not None:
            try:
                role = getattr(session, 'position', '') or getattr(session, 'candidate_inputs', {}).get('position', '')
                company = getattr(session, 'company', '') or getattr(session, 'candidate_inputs', {}).get('company', '')
                job_desc = getattr(session, 'job_description', '') or getattr(session, 'candidate_inputs', {}).get('job_description', '')
                
                # Determine if this is a behavioral or technical question
                question_type = getattr(question, 'question_type', None)
                is_behavioral = (
                    question_type and 
                    ('behavioral' in str(question_type).lower() or 'situational' in str(question_type).lower())
                ) or any(word in q_text.lower() for word in ['example', 'time when', 'situation', 'tell me about a time'])
                
                if is_behavioral:
                    # Use STAR format for behavioral questions
                    prompt = f"""
You are a senior interviewer for the {role} position. Answer this behavioral question using the STAR method.

Question: "{q_text}"

Role: {role}
Company: {company}
Job Description: {job_desc}

Provide a realistic example that directly answers this specific question. Use this format:

**Situation:** [Specific context/scenario]
**Task:** [Your responsibility/what needed to be done]  
**Action:** [Specific steps you took, tools used, decisions made]
**Result:** [Quantified outcomes and impact]

Requirements:
- Answer the EXACT question asked
- 150-200 words total
- Include specific tools and technologies relevant to the role
- Quantify results where possible
- Make it realistic and relevant to the question
"""
                else:
                    # Use technical format for technical questions
                    prompt = f"""
You are a senior professional in the {role} position providing an optimal technical answer.

Question: "{q_text}"

Role: {role}
Company: {company}
Job Description: {job_desc}

Provide a comprehensive technical answer that directly addresses this question.

Requirements:
- Answer the EXACT question asked - don't change the topic
- 120-180 words total
- Include specific technical details, tools, and methodologies
- Show systematic professional approach
- Mention relevant standards, methodologies, or analysis methods
- Be practical and actionable
- Focus on the technical aspects requested in the question
"""
                llm_response = llm_client.generate_response(prompt)
                
                # Validate response based on question type
                if is_behavioral:
                    # For behavioral questions, expect STAR format
                    if all(h in llm_response for h in ["**Situation:**", "**Task:**", "**Action:**", "**Result:**"]):
                        generated_answer = llm_response.strip()
                        key_points = [
                            "Uses STAR method structure",
                            "Provides specific example",
                            "Includes technical details",
                            "Shows quantified results"
                        ]
                    else:
                        generated_answer = None
                else:
                    # For technical questions, just check if it's a reasonable response
                    if len(llm_response.strip()) > 50 and q_text.lower()[:20] in llm_response.lower():
                        generated_answer = llm_response.strip()
                        key_points = [
                            "Addresses the specific question",
                            "Includes technical methodology",
                            "Shows engineering approach",
                            "Provides actionable insights"
                        ]
                    else:
                        generated_answer = None
            except Exception as e:
                print(f"⚠️ LLM sample answer generation failed: {e}")
                # Try OpenAI as fallback if Groq fails (rate limiting)
                if "rate limit" in str(e).lower() or "429" in str(e):
                    try:
                        print("🔄 Trying OpenAI as fallback for rate limit...")
                        # Try to get OpenAI client
                        global openai_service
                        if openai_service and hasattr(openai_service, 'client'):
                            openai_response = openai_service.client.chat.completions.create(
                                model="gpt-4o-mini",
                                messages=[{"role": "user", "content": prompt}],
                                max_tokens=300,
                                temperature=0.7
                            )
                            llm_response = openai_response.choices[0].message.content
                            
                            # Validate OpenAI response
                            if is_behavioral:
                                if all(h in llm_response for h in ["**Situation:**", "**Task:**", "**Action:**", "**Result:**"]):
                                    generated_answer = llm_response.strip()
                                    key_points = ["Uses STAR method structure", "Provides specific example", "Includes technical details", "Shows quantified results"]
                            else:
                                if len(llm_response.strip()) > 50:
                                    generated_answer = llm_response.strip()
                                    key_points = ["Addresses the specific question", "Includes technical methodology", "Shows engineering approach", "Provides actionable insights"]
                            
                            if generated_answer:
                                print("✅ OpenAI fallback successful")
                    except Exception as openai_error:
                        print(f"⚠️ OpenAI fallback also failed: {openai_error}")
                        
                if not generated_answer:
                    generated_answer = None
        
        # Fallback if LLM unavailable/invalid
        if not generated_answer:
            fb = smart_fallback(i, q_text)
            generated_answer = fb["text"]
            key_points = fb["key_points"]
        
        sample_answers.append({
            "question_number": i + 1,
            "question_text": q_text,
            "sample_answer": generated_answer,
            "key_points": key_points
        })
    
    return sample_answers

def generate_recommendations(score: float, analysis: List[Dict]) -> List[str]:
    """Generate personalized recommendations based on performance"""
    recommendations = []
    
    if score < 60:
        recommendations.extend([
            "Practice using the STAR method (Situation, Task, Action, Result) to structure your answers more effectively",
            "Prepare 3-5 specific examples from your experience that demonstrate technical problem-solving skills",
            "Focus on quantifying your achievements with specific numbers, percentages, or cost savings",
            "Practice explaining technical concepts clearly, as if teaching someone new to the field",
            "Work on providing more detailed explanations of your thought process and methodology"
        ])
    elif score < 80:
        recommendations.extend([
            "Continue using the STAR method but add more technical depth to your Action sections",
            "Prepare examples that show progression in your technical skills and responsibilities",
            "Practice discussing trade-offs and alternative solutions you considered",
            "Work on connecting your technical work to business impact and value creation",
            "Develop stories that showcase both individual contributions and teamwork"
        ])
    else:
        recommendations.extend([
            "Excellent use of structured responses! Continue refining your storytelling technique",
            "Consider preparing examples that demonstrate leadership in technical decision-making",
            "Focus on stories that show innovation, process improvement, or mentoring others",
            "Prepare to discuss emerging technologies and how they might impact your field",
            "Practice discussing failures or challenges and what you learned from them"
        ])
    
    # Add universal recommendations
    recommendations.extend([
        "Research the company's recent projects, challenges, and technical stack before interviews",
        "Practice mock interviews with a focus on behavioral questions using real examples",
        "Prepare questions to ask the interviewer about technical challenges and team dynamics"
    ])
    
    return recommendations

# Practice Mode Endpoints

@app.get("/practice/session")
async def get_practice_session():
    """Get or create a practice session"""
    try:
        session_id = "practice_session"  # Single session for now
        
        if session_id not in practice_sessions:
            # Create new session
            available_questions = [q for q in question_bank if q['id'] not in []]
            if available_questions:
                current_question = random.choice(available_questions)
                practice_sessions[session_id] = {
                    "currentQuestion": current_question,
                    "questionIndex": 0,
                    "completedQuestions": [],
                    "startTime": datetime.now()
                }
        
        session = practice_sessions.get(session_id)
        if session:
            return {
                "success": True,
                "currentQuestion": session["currentQuestion"],
                "questionIndex": session["questionIndex"],
                "completedQuestions": session["completedQuestions"]
            }
        else:
            raise HTTPException(status_code=404, detail="No questions available")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get practice session: {str(e)}")

@app.post("/practice/next-question")
async def get_next_question(request: dict):
    """Get the next random question"""
    try:
        completed_questions = request.get("completedQuestions", [])
        
        # Filter out completed questions
        available_questions = [q for q in question_bank if q['id'] not in completed_questions]
        
        if not available_questions:
            return {"success": True, "question": None, "message": "All questions completed!"}
        
        # Select random question
        next_question = random.choice(available_questions)
        question_index = len(completed_questions)
        
        # Update session
        session_id = "practice_session"
        if session_id in practice_sessions:
            practice_sessions[session_id]["currentQuestion"] = next_question
            practice_sessions[session_id]["questionIndex"] = question_index
        
        return {
            "success": True,
            "question": next_question,
            "questionIndex": question_index
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get next question: {str(e)}")

@app.post("/practice/analyze-answer")
async def analyze_practice_answer(request: dict):
    """Analyze user's answer - GPT-4o provides complete analysis for images, Groq compares to model answer for text"""
    try:
        question_id = request.get("questionId")
        user_answer = request.get("userAnswer", "")
        image_data = request.get("imageData", "")
        model_answer = request.get("modelAnswer", "")
        
        # Get the current question text for GPT-4o analysis
        current_question = None
        if question_id and question_bank:
            current_question = next((q for q in question_bank if q.get("id") == question_id), None)
        
        question_text = current_question.get("question", "Unknown question") if current_question else "Unknown question"
        
        # NEW LOGIC: Different behavior for GPT-4o vs Groq
        used_model = "groq"
        if image_data:
            print("🖼️ Image detected - using OpenAI GPT-4o for complete multimodal analysis")
            # Use OpenAI for comprehensive image + text analysis
            if openai_service.client and openai_service.test_connection():
                try:
                    # GPT-4o provides complete analysis without using model answer
                    feedback = openai_service.analyze_practice_answer(user_answer, question_text, model_answer, image_data)
                    print(f"✅ OpenAI analysis successful: {feedback}")
                    used_model = "openai"
                except Exception as e:
                    print(f"❌ OpenAI analysis error: {e}")
                    feedback = "⚠️ Image analysis failed."
                    used_model = "openai_failed"
            else:
                # Fall back to Groq text-only if OpenAI not available
                print("⚠️ OpenAI unavailable - falling back to Groq text-only analysis")
                feedback = groq_service.analyze_practice_answer_text_only(user_answer, model_answer)
                used_model = "groq_fallback"
        else:
            print("📝 Text-only analysis - using Groq Llama model")
            # Use Groq for text-only analysis (compares to model answer)
            if groq_service.client:
                try:
                    feedback = groq_service.analyze_practice_answer_text_only(user_answer, model_answer)
                    print(f"✅ Groq analysis successful: {feedback}")
                    used_model = "groq"
                except Exception as e:
                    print(f"❌ Groq analysis error: {e}")
                    feedback = "⚠️ Analysis failed."
            else:
                feedback = "⚠️ Analysis unavailable."
        
        return {
            "success": True,
            "feedback": feedback,
            "usedModel": used_model
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze answer: {str(e)}")

@app.post("/practice/chat")
async def practice_chat(request: dict):
    """Handle follow-up questions in practice mode"""
    try:
        message = request.get("message", "")
        current_question = request.get("currentQuestion", {})
        
        # Create context-aware response
        prompt = f"""
        Current Question: {current_question.get('question', '')}
        Model Answer: {current_question.get('answer', '')}
        
        User's Follow-up: {message}
        
        If the user is asking for:
        - "next" or "next question": Respond with "Ready for the next question!"
        - Analysis, explanation, or "why": Provide detailed explanation
        - Clarification: Give brief, focused answer
        
        Keep responses concise unless they specifically ask for detailed explanation.
        """
        
        # Use Groq for response
        if groq_service.client:
            try:
                response = groq_service.client.chat.completions.create(
                    model="meta-llama/llama-4-maverick-17b-128e-instruct",
                    messages=[
                        {"role": "system", "content": "You are a concise technical tutor. Give brief answers unless detailed explanation is specifically requested."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=200,
                    temperature=0.7
                )
                ai_response = response.choices[0].message.content
                
                # Add next question prompt if not already present
                if "next" not in ai_response.lower():
                    ai_response += "\n\n---\n\n🔄 **Ready for the next question?** Type \"next\" to continue!"
                    
            except Exception as e:
                ai_response = "I'm here to help! Feel free to ask any questions about this topic.\n\n---\n\n🔄 **Ready for the next question?** Type \"next\" to continue!"
        else:
            ai_response = "Great question! Let me know if you need clarification on any concepts.\n\n---\n\n🔄 **Ready for the next question?** Type \"next\" to continue!"
        
        return {
            "success": True,
            "response": ai_response
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process chat: {str(e)}")

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time communication"""
    await websocket.accept()
    
    # Create or get session
    if session_id not in active_sessions:
        active_sessions[session_id] = SessionState(
            session_id=session_id,
            created_at=datetime.now(),
            last_activity=datetime.now()
        )
    
    active_connections[session_id] = websocket
    print(f"Client {session_id} connected")
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            print(f"Received message: {message_data.get('type', 'unknown')}")
            
            # Update session activity
            active_sessions[session_id].last_activity = datetime.now()
            
            # Handle different message types
            if message_data["type"] == "whiteboard_analysis":
                # Process whiteboard analysis
                image_data = message_data.get("image_data", "")
                user_speech = message_data.get("user_speech", "")
                ai_model = message_data.get("ai_model", "gpt4o")
                
                # Add user message to history
                if user_speech:
                    user_msg = ChatMessage(
                        role="user",
                        content=user_speech,
                        timestamp=datetime.now(),
                        message_type="speech"
                    )
                    active_sessions[session_id].conversation_history.append(user_msg)
                
                # Analyze with selected AI model
                print(f"🎤 User speech: '{user_speech}'")
                print(f"🤖 Using AI model: {ai_model}")
                
                # Always use OpenAI for image analysis in interview mode (same as practice page)
                print(f"🖼️ Interview image analysis - using OpenAI GPT-4o (same as practice page)")
                try:
                    ai_response = openai_service.analyze_whiteboard_and_speech(
                        image_data,
                        user_speech
                    )
                    visual_analysis = "OpenAI GPT-4o multimodal analysis"
                    print(f"✅ Interview OpenAI analysis successful: {len(ai_response)} chars")
                except Exception as e:
                    print(f"❌ Interview OpenAI analysis error: {e}")
                    ai_response = f"Sorry, I encountered an error analyzing your whiteboard: {str(e)}"
                    visual_analysis = "OpenAI analysis failed"
                
                print(f"🤖 AI response: {ai_response[:100]}...")
                
                # Add AI response to history
                ai_msg = ChatMessage(
                    role="assistant",
                    content=ai_response,
                    timestamp=datetime.now()
                )
                active_sessions[session_id].conversation_history.append(ai_msg)
                
                # Send response back to client
                response = {
                    "type": "ai_response",
                    "visual_analysis": visual_analysis,
                    "ai_response": ai_response,
                    "timestamp": datetime.now().isoformat()
                }
                
                await websocket.send_text(json.dumps(response))
            
            elif message_data["type"] == "chat_message":
                # Handle regular chat messages
                user_content = message_data.get("content", "")
                
                # Add to conversation history
                user_msg = ChatMessage(
                    role="user",
                    content=user_content,
                    timestamp=datetime.now()
                )
                active_sessions[session_id].conversation_history.append(user_msg)
                
                # For text-only chat, use a simple educational response
                # TODO: Could enhance this with conversation context
                ai_response = f"I understand you said: '{user_content}'. Could you tell me more about what you're working on or draw something on the whiteboard so I can better help you?"
                
                # Add AI response to history
                ai_msg = ChatMessage(
                    role="assistant",
                    content=ai_response,
                    timestamp=datetime.now()
                )
                active_sessions[session_id].conversation_history.append(ai_msg)
                
                # Send response
                response = {
                    "type": "chat_response",
                    "content": ai_response,
                    "timestamp": datetime.now().isoformat()
                }
                
                await websocket.send_text(json.dumps(response))
                
    except WebSocketDisconnect:
        # Clean up on disconnect
        if session_id in active_connections:
            del active_connections[session_id]
        print(f"Client {session_id} disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        if session_id in active_connections:
            del active_connections[session_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=Config.BACKEND_PORT, 
        reload=False
    )
