# Automated Interview Flow Testing System

This testing system validates that all three interview types (Technical Only, Behavioral Only, Technical+Behavioral) are working correctly with real resume and job description data.

## 📁 Directory Structure

```
tests/
├── test_interview_flow.py          # Main testing framework
├── run_all_tests.py               # Simple test runner
├── README.md                      # This file
├── test_data/                     # Input test data
│   ├── resumes/
│   │   ├── aakash_mechanical_resume.txt    # Aakash (Mechanical Engineer)
│   │   └── aarshee_software_resume.txt     # Aarshee (Software Engineer)
│   └── job_descriptions/
│       ├── mechanical_engineer_jd.txt      # Lucid Motors Mechanical JD
│       └── software_developer_jd.txt       # Adobe Software JD
└── test_results/                  # Output JSON files
    ├── aakash_mechanical_technical_only.json
    ├── aakash_mechanical_behavioral_only.json
    ├── aakash_mechanical_technical_behavioral.json
    ├── aarshee_software_technical_only.json
    ├── aarshee_software_behavioral_only.json
    ├── aarshee_software_technical_behavioral.json
    └── comprehensive_test_results.json
```

## 🚀 How to Run Tests

### Option 1: Run All Tests (Recommended)
```bash
cd tests
python run_all_tests.py
```

### Option 2: Run Individual Test
```bash
cd tests
python test_interview_flow.py --resume test_data/resumes/aakash_mechanical_resume.txt --jd test_data/job_descriptions/mechanical_engineer_jd.txt --type technical_only
```

### Option 3: Run All Tests with Full Control
```bash
cd tests
python test_interview_flow.py --all
```

## 📊 Test Combinations

The system tests 6 combinations with correct resume-JD pairings:

| Resume | Job Description | Interview Types |
|--------|----------------|-----------------|
| Aakash (Mechanical) | Mechanical Engineer JD | Technical, Behavioral, Combined |
| Aarshee (Software) | Software Developer JD | Technical, Behavioral, Combined |

## 📋 What Each Test Validates

### 1. Blueprint Generation
- ✅ Correct number of technical/behavioral questions
- ✅ Interview type routing (technical-only gets only technical questions)
- ✅ Question relevance to resume and JD

### 2. AI Conductor Behavior
- ✅ All 4 actions: CHALLENGE, DEEPEN, TRANSITION, CONCEDE_AND_PIVOT
- ✅ Proper decision-making logic
- ✅ Topic progression without repetition

### 3. Interview Flow
- ✅ Complete interview from start to finish
- ✅ Proper topic transitions
- ✅ Interview completion detection
- ✅ No infinite loops or repetition

## 📄 JSON Output Format

Each test generates a detailed JSON file with:

```json
{
  "test_metadata": {
    "resume_file": "aakash_mechanical_resume.txt",
    "job_description": "mechanical_engineer_jd.txt", 
    "interview_type": "technical_only",
    "test_timestamp": "2025-01-15T10:30:00Z",
    "total_duration": "45.2 seconds"
  },
  "blueprint_validation": {
    "technical_questions_count": 4,
    "behavioral_questions_count": 0,
    "interview_type_routing": "CORRECT"
  },
  "conversation_flow": [
    {
      "turn": 1,
      "ai_question": "Can you tell me about your experience with CATIA?",
      "mock_answer": "I have experience with various technical projects...",
      "ai_conductor_decision": {
        "chosen_action": "CHALLENGE",
        "analysis": "Candidate provided general answer, need specifics",
        "next_utterance": "That's interesting. Can you walk me through a specific CATIA project..."
      }
    }
  ],
  "test_results": {
    "status": "PASS",
    "topics_covered": ["CATIA", "FEA", "Thermal Analysis"],
    "topic_repetition_detected": false,
    "interview_completed_successfully": true,
    "total_turns": 6,
    "api_calls_made": 8
  }
}
```

## 🔍 How to Analyze Results

### 1. Check Overall Success
Look at `comprehensive_test_results.json` → `test_summary` → `overall_stats`:
- `success_rate`: Should be 100%
- `failed_tests`: Should be 0

### 2. Validate Interview Types
Check each individual JSON file:
- **Technical Only**: `technical_questions_count > 0`, `behavioral_questions_count = 0`
- **Behavioral Only**: `behavioral_questions_count > 0`, `technical_questions_count = 0`  
- **Combined**: Both counts > 0

### 3. Check Topic Progression
Look at `conversation_flow` array:
- Questions should be different each turn
- `topic_repetition_detected` should be `false`
- AI actions should vary (CHALLENGE, DEEPEN, TRANSITION, CONCEDE_AND_PIVOT)

### 4. Verify Domain Matching
- Aakash (Mechanical) tests should mention: CATIA, FEA, thermal analysis, mechanical design
- Aarshee (Software) tests should mention: Python, Java, system design, APIs, microservices

## ⚠️ Troubleshooting

### Common Issues:
1. **Import Errors**: Make sure you're running from the `tests/` directory
2. **API Rate Limits**: Tests include delays to prevent rate limiting
3. **Missing Files**: Ensure all files in `test_data/` exist

### If Tests Fail:
1. Check individual JSON files for error details
2. Look at `test_results.errors` array
3. Verify LLM API keys are configured
4. Check server logs for additional context

## 🎯 Expected Results

When everything is working correctly, you should see:
- ✅ All 6 tests pass
- ✅ No topic repetition
- ✅ Correct interview type routing
- ✅ Relevant questions for each domain (mechanical vs software)
- ✅ Proper AI Conductor decision flow

This validates that your interview system is ready for production use!
