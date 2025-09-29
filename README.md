# Intelligent Interview System for Mechanical Engineering

A comprehensive AI-powered interview platform that analyzes resumes, matches skills with job requirements, and conducts adaptive technical and behavioral interviews.

## 🎯 Features

### Core Capabilities
- **Resume Analysis**: Extracts skills, experience, and competencies using LLM
- **Job Description Analysis**: Identifies requirements, skills, and role context
- **Skill Matching**: Intelligent matching algorithm with gap analysis
- **Dynamic Question Generation**: Creates targeted questions based on analysis
- **Adaptive Interview Flow**: Real-time adjustment based on candidate responses
- **Multi-Modal Support**: Handles text, images, and documents
- **Comprehensive Assessment**: Detailed evaluation and recommendations

### Interview Types
- **Technical Screening**: Focus on technical skills and fundamentals
- **Technical + Behavioral**: Balanced assessment of technical and soft skills  
- **Behavioral Only**: Emphasis on communication, leadership, and cultural fit

### AI Interviewer Personas
- Multiple interviewer personalities with different expertise areas
- Natural conversation flow with professional tone
- Context-aware follow-up questions

## 🏗️ System Architecture

```
Frontend Input → LLM Analysis → Skill Matching → Question Generation → Interview Flow → Assessment
     ↓              ↓              ↓               ↓                ↓            ↓
  User Data    Resume/Job     Gap Analysis    Targeted Qs      Adaptive      Final Report
              Analysis                                        Responses
```

### Core Components

1. **ResumeAnalyzer** - Extracts and categorizes candidate information
2. **JobAnalyzer** - Analyzes job requirements and context
3. **SkillMatcher** - Matches skills and identifies gaps
4. **QuestionGenerator** - Creates targeted interview questions
5. **InterviewConductor** - Orchestrates the complete interview flow
6. **InterviewSystemAPI** - Main interface for frontend integration

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd interview-system

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```python
from interview_system import InterviewSystemAPI
from interview_system.llm_integration import create_llm_client

# Initialize LLM client
llm_client = create_llm_client(groq_api_key, openai_api_key)

# Create interview API
interview_api = InterviewSystemAPI(llm_client)

# Start interview
candidate_inputs = {
    'username': 'John Doe',
    'position': 'Mechanical Design Engineer',
    'job_description': 'Job description text...',
    'resume': 'Resume text...',
    'interview_type': 'technical_behavioral',
    'duration_minutes': 60
}

# Initialize interview
result = interview_api.initialize_interview(candidate_inputs)
session_id = result['session_id']

# Conduct interview
question = interview_api.get_next_question(session_id)
evaluation = interview_api.submit_answer(session_id, question_id, answer)

# Get final assessment
summary = interview_api.get_interview_summary(session_id)
```

### Demo Mode

```bash
# Run complete demo
python -m interview_system.demo_runner

# Choose option 1 for full demo or 2 for quick test
```

## 📊 Input/Output Specification

### Input Format

```json
{
  "username": "string",
  "position": "string", 
  "job_description": "string",
  "resume": "string",
  "linkedin_profile": "string (optional)",
  "interview_type": "technical_screening|technical_behavioral|behavioral_only",
  "duration_minutes": "integer"
}
```

### Output Format

```json
{
  "session_id": "string",
  "greeting_message": "string",
  "interview_info": {
    "interviewer_name": "string",
    "company": "string",
    "position": "string"
  },
  "skill_analysis_summary": {
    "overall_fit_score": "float",
    "perfect_matches": "integer",
    "critical_gaps": "integer"
  }
}
```

## 🔧 Configuration

### LLM Setup

The system supports two LLM providers:

1. **Groq API** (Primary) - Fast, cost-effective
   - Model: `meta-llama/llama-4-maverick-17b-128e-instruct`
   - Used for: Resume analysis, question generation, response evaluation

2. **OpenAI GPT-4o** (Fallback) - Advanced reasoning
   - Used for: Complex analysis, image processing, fallback scenarios

### Environment Variables

```bash
GROQ_API_KEY=your_groq_api_key
OPENAI_API_KEY=your_openai_api_key
```

## 📋 API Reference

### Main Interface Methods

#### `initialize_interview(candidate_inputs)`
Starts new interview session with analysis and question generation.

#### `get_next_question(session_id)`
Retrieves next question in interview sequence.

#### `submit_answer(session_id, question_id, answer_text)`
Processes candidate answer and provides evaluation.

#### `get_interview_summary(session_id)`
Generates comprehensive assessment and recommendations.

### Response Evaluation

The system evaluates responses on multiple criteria:
- **Technical Accuracy**: Correctness of technical concepts
- **Communication Clarity**: Structure and clarity of explanation
- **Problem-Solving Approach**: Systematic thinking process
- **Depth of Knowledge**: Understanding beyond surface level

## 🎓 Question Database

The system includes 184+ example questions covering:

### Technical Areas
- **Fundamentals**: Stress/strain, thermodynamics, materials
- **Design**: GD&T, tolerance analysis, DFM principles
- **Analysis**: FEA, CFD, optimization methods
- **Manufacturing**: Processes, quality control, cost optimization

### Behavioral Areas
- **Problem Solving**: STAR method scenarios
- **Leadership**: Mentoring, team management
- **Collaboration**: Cross-functional teamwork
- **Learning Agility**: Adaptation and growth mindset

## 🔍 Skill Matching Algorithm

### Match Types
- **Perfect Match**: Exact skill with adequate proficiency
- **Partial Match**: Related skill or lower proficiency  
- **Transferable**: Different but applicable skill
- **Gap**: Required skill not present

### Scoring Factors
- Skill similarity (exact, synonym, transferable)
- Proficiency level alignment
- Years of experience
- Context relevance

## 📈 Assessment Framework

### Evaluation Criteria
- **Technical Competency**: Domain knowledge and application
- **Problem-Solving**: Systematic approach and creativity
- **Communication**: Clarity and professional presentation
- **Cultural Fit**: Alignment with company values
- **Growth Potential**: Learning agility and adaptability

### Recommendation Categories
- **Hire**: Strong candidate, ready for role
- **Hire with Conditions**: Good candidate, needs development
- **Not Ready**: Significant gaps, extensive training needed
- **Not Suitable**: Poor fit for role requirements

## 🛠️ Development

### Project Structure
```
interview_system/
├── __init__.py              # Package initialization
├── main_interface.py        # Primary API interface
├── interview_conductor.py   # Interview orchestration
├── resume_analyzer.py       # Resume analysis component
├── job_analyzer.py         # Job description analysis
├── skill_matcher.py        # Skill matching algorithm
├── question_generator.py   # Dynamic question creation
├── llm_integration.py      # LLM client management
└── demo_runner.py          # Demonstration scripts
```

### Testing

```bash
# Run quick functionality test
python -m interview_system.demo_runner
# Select option 2

# Run complete demo
python -m interview_system.demo_runner  
# Select option 1
```

### Mock Mode

For testing without API keys:

```python
from interview_system.llm_integration import MockLLMClient

llm_client = MockLLMClient()
interview_api = InterviewSystemAPI(llm_client)
```

## 🔒 Security & Privacy

- No persistent storage of candidate data
- Session-based data management
- API key encryption recommended
- GDPR compliance considerations

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📞 Support

For questions or issues:
- Create GitHub issue
- Check documentation
- Review demo examples

---

**Built with ❤️ for the future of technical interviewing**