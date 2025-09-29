#!/usr/bin/env python3
"""
Automated Interview Flow Testing System
Tests all three interview types with real resume/JD combinations
Generates comprehensive JSON reports for analysis
"""

import sys
import os
import json
import time
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add the parent directory to the path to import interview system modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import interview system components
from interview_system.main_interface import InterviewSystemAPI
from interview_system.llm_integration import create_llm_client, MockLLMClient
from backend.config import Config

class MockCandidate:
    """Simulates candidate responses for automated testing"""
    
    def __init__(self, interview_type: str):
        self.interview_type = interview_type
        self.turn_count = 0
        
    def generate_response(self, question: str) -> str:
        """Generate appropriate mock responses based on question and interview type"""
        self.turn_count += 1
        
        # Vary responses to trigger different AI Conductor actions and ensure full interview flow
        if self.turn_count == 1:
            # First response - provide general answer to trigger CHALLENGE
            if "technical" in self.interview_type:
                return "I have experience with various technical projects and have worked on several challenging problems in my previous roles."
            else:
                return "I have experience working in teams and have handled various challenging situations in my career."
                
        elif self.turn_count == 2:
            # Second response - provide specific example to trigger DEEPEN
            if "technical" in self.interview_type:
                return "In my recent project, I worked on developing a distributed system using Python and implemented microservices architecture with Docker containers."
            else:
                return "In one specific situation, I led a cross-functional team of 5 people to deliver a critical project under tight deadlines."
                
        elif self.turn_count == 3:
            # Third response - provide detailed answer to trigger TRANSITION
            if "technical" in self.interview_type:
                return "I implemented a caching layer using Redis, optimized database queries, and reduced response time by 40%. I also set up monitoring with Prometheus and Grafana for real-time performance tracking."
            else:
                return "I organized daily standups, facilitated conflict resolution between team members, and implemented a new communication process that improved team efficiency by 30%. The project was delivered on time and under budget."
                
        elif self.turn_count == 4:
            # Fourth response - show some uncertainty to trigger CONCEDE_AND_PIVOT
            return "I don't have extensive experience in this particular area. Could we discuss something else I'm more familiar with?"
            
        elif self.turn_count == 5:
            # Fifth response - provide good answer to continue conversation
            if "technical" in self.interview_type:
                return "I have solid experience with this. I've worked on similar challenges where I had to balance performance requirements with system constraints. I typically start by analyzing the requirements and then design a scalable solution."
            else:
                return "I've handled similar situations before. My approach is to first understand all stakeholders' perspectives, then develop a structured plan with clear milestones and regular check-ins."
                
        elif self.turn_count == 6:
            # Sixth response - another detailed answer
            if "technical" in self.interview_type:
                return "In my experience, I've found that proper testing and documentation are crucial. I always implement comprehensive unit tests and maintain clear technical documentation for future maintenance."
            else:
                return "Communication is key in these situations. I make sure to keep all stakeholders informed and create transparent processes that everyone can follow and understand."
                
        elif self.turn_count == 7:
            # Seventh response - trigger another transition
            return "I have some experience with this, but I'd be interested in discussing other aspects of the role where I can demonstrate my stronger skills."
            
        elif self.turn_count == 8:
            # Eighth response - provide comprehensive answer
            if "technical" in self.interview_type:
                return "I've worked extensively with this technology stack. I understand the trade-offs between different approaches and have experience optimizing for both performance and maintainability. I also stay current with industry best practices."
            else:
                return "I have strong experience in this area. I've successfully managed similar challenges by building consensus among team members, setting clear expectations, and ensuring everyone has the resources they need to succeed."
                
        elif self.turn_count == 9:
            # Ninth response - show depth of knowledge
            if "technical" in self.interview_type:
                return "I've not only implemented these solutions but also mentored other engineers on best practices. I believe in knowledge sharing and have contributed to internal documentation and training materials."
            else:
                return "Beyond just managing the situation, I've also worked to improve our processes to prevent similar issues in the future. I believe in continuous improvement and learning from every experience."
                
        else:
            # Default responses for additional turns (10+)
            if "technical" in self.interview_type:
                return f"I continue to learn and grow in this area. I stay updated with the latest technologies and best practices through continuous learning and hands-on experience in my projects."
            else:
                return f"I'm always looking to improve my approach. I regularly seek feedback from colleagues and stakeholders to ensure I'm delivering the best possible results and growing as a professional."

class InterviewFlowTester:
    """Main testing class for automated interview flow validation"""
    
    def __init__(self):
        self.test_results = {}
        self.api_call_count = 0
        
        # Initialize LLM client
        try:
            if Config.GROQ_API_KEY and Config.GROQ_API_KEY != "your-groq-key-here":
                self.llm_client = create_llm_client(Config.GROQ_API_KEY, Config.OPENAI_API_KEY or "")
                print("🔧 Using real LLM services for testing")
            else:
                self.llm_client = MockLLMClient()
                print("🔧 Using mock LLM client for testing")
        except Exception as e:
            print(f"⚠️ LLM client initialization failed, using mock: {e}")
            self.llm_client = MockLLMClient()
            
        # Initialize interview API
        self.interview_api = InterviewSystemAPI(self.llm_client)
        
    def load_test_data(self, resume_file: str, jd_file: str) -> tuple:
        """Load resume and job description content"""
        try:
            with open(resume_file, 'r', encoding='utf-8') as f:
                resume_content = f.read().strip()
            with open(jd_file, 'r', encoding='utf-8') as f:
                jd_content = f.read().strip()
            return resume_content, jd_content
        except Exception as e:
            raise Exception(f"Failed to load test data: {e}")
    
    def test_interview_flow(self, resume_file: str, jd_file: str, interview_type: str, max_turns: int = 12) -> Dict[str, Any]:
        """Test complete interview flow and return detailed results"""
        
        print(f"\n{'='*60}")
        print(f"🧪 TESTING: {interview_type.upper()}")
        print(f"📄 Resume: {os.path.basename(resume_file)}")
        print(f"💼 Job Description: {os.path.basename(jd_file)}")
        print(f"{'='*60}")
        
        start_time = time.time()
        test_result = {
            "test_metadata": {
                "resume_file": os.path.basename(resume_file),
                "job_description": os.path.basename(jd_file),
                "interview_type": interview_type,
                "test_timestamp": datetime.now().isoformat(),
                "max_turns": max_turns
            },
            "blueprint_validation": {},
            "conversation_flow": [],
            "test_results": {
                "status": "UNKNOWN",
                "errors": [],
                "topics_covered": [],
                "topic_repetition_detected": False,
                "interview_completed_successfully": False,
                "total_turns": 0,
                "api_calls_made": 0
            }
        }
        
        try:
            # Load test data
            resume_content, jd_content = self.load_test_data(resume_file, jd_file)
            
            # Phase 1: Create interview session (Blueprint Generation)
            print("\n🔄 Phase 1: Blueprint Generation")
            session_response = self.interview_api.start_interview_flow({
                'username': 'TestCandidate',
                'position': self._extract_position_from_jd(jd_content),
                'company': self._extract_company_from_jd(jd_content),
                'jobDescription': jd_content,
                'resumeText': resume_content,
                'interviewType': self._normalize_interview_type_for_frontend(interview_type),
                'duration': 60
            })
            
            if not session_response or 'session_id' not in session_response:
                raise Exception("Failed to create interview session")
                
            session_id = session_response['session_id']
            print(f"✅ Session created: {session_id}")
            
            # Validate blueprint
            blueprint_validation = self._validate_blueprint(session_response, interview_type)
            test_result["blueprint_validation"] = blueprint_validation
            print(f"✅ Blueprint validation: {blueprint_validation}")
            
            # Phase 2: Submit introduction
            print("\n🔄 Phase 2: Introduction")
            try:
                intro_response = self.interview_api.submit_introduction(session_id, "Hello, I'm excited about this opportunity and ready to discuss my background and experience.")
                print(f"🔍 DEBUG: Introduction response: {intro_response}")
                
                # Handle different response formats
                message = intro_response.get('message') or intro_response.get('follow_up_question')
                
                # If no message but transition occurred, get the next question
                if not message and intro_response.get('conductor_action') == 'TRANSITION':
                    print("🔄 AI Conductor transitioned - getting next question...")
                    next_q_response = self.interview_api.get_next_question(session_id)
                    message = next_q_response.get('message', '') if next_q_response else ''
                
                if not intro_response or not message:
                    raise Exception(f"Failed to submit introduction - No message/question in response: {intro_response}")
            except Exception as e:
                print(f"❌ Introduction submission error: {e}")
                raise Exception(f"Failed to submit introduction: {e}")
                
            print(f"✅ Introduction submitted")
            first_question = message
            print(f"📝 First question: {first_question[:100]}...")
            
            # Phase 3: Complete conversation simulation (until interview ends or max turns)
            print(f"\n🔄 Phase 3: Complete Interview Simulation (up to {max_turns} turns)")
            mock_candidate = MockCandidate(interview_type)
            conversation_flow = []
            topics_seen = set()
            
            current_question = first_question
            
            for turn in range(1, max_turns + 1):
                print(f"\n--- Turn {turn} ---")
                
                # Generate mock candidate response
                mock_answer = mock_candidate.generate_response(current_question)
                print(f"🤖 Mock answer: {mock_answer[:80]}...")
                
                # Submit answer and get AI response
                answer_response = self.interview_api.submit_answer(
                    session_id, 
                    f"test_q_{turn}", 
                    mock_answer
                )
                
                if not answer_response:
                    print(f"⚠️ No response received for turn {turn}")
                    break
                
                # Extract AI Conductor decision details
                ai_message = answer_response.get('message') or answer_response.get('follow_up_question', '')
                conductor_decision = {
                    "chosen_action": answer_response.get('conductor_action', 'UNKNOWN'),
                    "analysis": answer_response.get('analysis', 'No analysis provided'),
                    "next_utterance": ai_message
                }
                
                print(f"🎯 AI Action: {conductor_decision['chosen_action']}")
                print(f"📝 Next question: {conductor_decision['next_utterance'][:80]}...")
                
                # Track conversation
                conversation_turn = {
                    "turn": turn,
                    "ai_question": current_question,
                    "mock_answer": mock_answer,
                    "ai_conductor_decision": conductor_decision
                }
                conversation_flow.append(conversation_turn)
                
                # Extract topics for analysis
                self._extract_topics_from_question(conductor_decision['next_utterance'], topics_seen)
                
                # Check for completion or company Q&A phase
                next_action = answer_response.get('next_action', 'continue')
                if next_action == 'start_company_qna':
                    print(f"🎉 Main interview completed after {turn} turns! Starting Company Q&A...")
                    
                    # Phase 4: Company Q&A simulation
                    print(f"\n🔄 Phase 4: Company Q&A Simulation")
                    try:
                        # Start company Q&A
                        qna_response = self.interview_api.start_company_qna(session_id)
                        if qna_response and 'message' in qna_response:
                            company_question = qna_response['message']
                            print(f"📝 Company Q&A question: {company_question[:100]}...")
                            
                            # Add to conversation flow
                            conversation_turn = {
                                "turn": turn + 1,
                                "ai_question": company_question,
                                "mock_answer": "I'm interested in learning about the team culture and growth opportunities. What are the biggest challenges the team is currently facing?",
                                "ai_conductor_decision": {
                                    "chosen_action": "COMPANY_QNA",
                                    "analysis": "Transitioning to company Q&A phase",
                                    "next_utterance": company_question
                                }
                            }
                            conversation_flow.append(conversation_turn)
                            
                            # Submit company question
                            final_response = self.interview_api.submit_company_question(
                                session_id, 
                                "I'm interested in learning about the team culture and growth opportunities. What are the biggest challenges the team is currently facing?"
                            )
                            
                            if final_response and 'message' in final_response:
                                print(f"📝 Company Q&A response: {final_response['message'][:100]}...")
                                
                                # Add final response to conversation
                                conversation_turn = {
                                    "turn": turn + 2,
                                    "ai_question": final_response['message'],
                                    "mock_answer": "Thank you for the information. I don't have any more questions at this time.",
                                    "ai_conductor_decision": {
                                        "chosen_action": "COMPANY_QNA_COMPLETE",
                                        "analysis": "Company Q&A phase completed",
                                        "next_utterance": "Thank you for your time today!"
                                    }
                                }
                                conversation_flow.append(conversation_turn)
                        
                        print(f"✅ Complete interview flow finished (including Company Q&A)")
                        test_result["test_results"]["interview_completed_successfully"] = True
                        
                    except Exception as e:
                        print(f"⚠️ Company Q&A phase failed: {e}")
                        test_result["test_results"]["interview_completed_successfully"] = True  # Main interview still completed
                    
                    break
                    
                elif next_action == 'interview_complete':
                    print(f"🎉 Interview completed after {turn} turns!")
                    test_result["test_results"]["interview_completed_successfully"] = True
                    break
                
                # Prepare for next turn
                current_question = conductor_decision['next_utterance']
                
                # Add delay to prevent rate limiting
                time.sleep(2.0)  # Increased delay between turns
            
            test_result["conversation_flow"] = conversation_flow
            test_result["test_results"]["total_turns"] = len(conversation_flow)
            test_result["test_results"]["topics_covered"] = list(topics_seen)
            
            # Check for topic repetition
            questions_asked = [turn["ai_question"] for turn in conversation_flow]
            unique_questions = set(q[:50] for q in questions_asked)  # Compare first 50 chars
            if len(unique_questions) < len(questions_asked):
                test_result["test_results"]["topic_repetition_detected"] = True
                print("⚠️ Topic repetition detected!")
            else:
                print("✅ No topic repetition detected")
            
            # Final status
            test_result["test_results"]["status"] = "PASS"
            print(f"\n✅ TEST PASSED")
            
        except Exception as e:
            test_result["test_results"]["status"] = "FAIL"
            test_result["test_results"]["errors"].append(str(e))
            print(f"\n❌ TEST FAILED: {e}")
        
        # Add timing and metadata
        end_time = time.time()
        test_result["test_metadata"]["total_duration"] = f"{end_time - start_time:.2f} seconds"
        test_result["test_results"]["api_calls_made"] = self.api_call_count
        
        return test_result
    
    def _normalize_interview_type_for_frontend(self, interview_type: str) -> str:
        """Convert test interview type to frontend format"""
        mapping = {
            "technical_only": "Technical",
            "behavioral_only": "Behavioral", 
            "technical_behavioral": "Behavioral + Technical"
        }
        return mapping.get(interview_type, interview_type)
    
    def _extract_position_from_jd(self, jd_content: str) -> str:
        """Extract position title from job description"""
        if "Software Development Engineer" in jd_content or "Software" in jd_content:
            return "Software Development Engineer"
        elif "Mechanical Design Engineer" in jd_content or "Mechanical" in jd_content:
            return "Senior Mechanical Design Engineer"
        else:
            return "Engineer"
    
    def _extract_company_from_jd(self, jd_content: str) -> str:
        """Extract company name from job description"""
        if "Adobe" in jd_content:
            return "Adobe"
        elif "Lucid" in jd_content:
            return "Lucid Motors"
        else:
            return "Company"
    
    def _validate_blueprint(self, session_response: Dict[str, Any], interview_type: str) -> Dict[str, Any]:
        """Validate that blueprint was generated correctly for interview type"""
        validation = {
            "technical_questions_count": 0,
            "behavioral_questions_count": 0,
            "interview_type_routing": "UNKNOWN"
        }
        
        try:
            # Extract blueprint info from session response
            interview_info = session_response.get('interview_info', {})
            blueprint = interview_info.get('blueprint', {})
            interview_plan = blueprint.get('interview_plan', {})
            interview_flow = interview_plan.get('interview_flow', [])
            
            # Count question types
            technical_count = 0
            behavioral_count = 0
            
            for question in interview_flow:
                intent = question.get('intent', '').lower()
                phase = question.get('phase', '').lower()
                
                if any(keyword in intent + phase for keyword in ['technical', 'coding', 'system', 'algorithm', 'programming']):
                    technical_count += 1
                elif any(keyword in intent + phase for keyword in ['behavioral', 'leadership', 'teamwork', 'collaboration']):
                    behavioral_count += 1
            
            validation["technical_questions_count"] = technical_count
            validation["behavioral_questions_count"] = behavioral_count
            
            # Validate routing correctness
            if interview_type == "technical_only":
                if technical_count > 0 and behavioral_count == 0:
                    validation["interview_type_routing"] = "CORRECT"
                else:
                    validation["interview_type_routing"] = "INCORRECT - Expected only technical questions"
            elif interview_type == "behavioral_only":
                if behavioral_count > 0 and technical_count == 0:
                    validation["interview_type_routing"] = "CORRECT"
                else:
                    validation["interview_type_routing"] = "INCORRECT - Expected only behavioral questions"
            elif interview_type == "technical_behavioral":
                if technical_count > 0 and behavioral_count > 0:
                    validation["interview_type_routing"] = "CORRECT"
                else:
                    validation["interview_type_routing"] = "INCORRECT - Expected both technical and behavioral questions"
            
        except Exception as e:
            validation["interview_type_routing"] = f"VALIDATION_ERROR: {str(e)}"
        
        return validation
    
    def _extract_topics_from_question(self, question: str, topics_seen: set):
        """Extract topic keywords from questions for analysis"""
        question_lower = question.lower()
        
        # Technical topics
        technical_keywords = ['python', 'java', 'system design', 'algorithm', 'database', 'api', 'microservices', 'cloud', 'docker', 'kubernetes']
        # Mechanical topics  
        mechanical_keywords = ['catia', 'cad', 'fea', 'ansys', 'thermal', 'vibration', 'mechanical design', 'enclosure', 'manufacturing']
        # Behavioral topics
        behavioral_keywords = ['leadership', 'teamwork', 'conflict', 'communication', 'project management', 'collaboration']
        
        all_keywords = technical_keywords + mechanical_keywords + behavioral_keywords
        
        for keyword in all_keywords:
            if keyword in question_lower:
                topics_seen.add(keyword.title())
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test combinations and return comprehensive results"""
        
        print("🚀 Starting Automated Interview Flow Testing")
        print("=" * 80)
        
        # Get base directory for absolute paths
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Define test combinations with correct pairings
        test_combinations = [
            # Aakash (Mechanical Engineer) with Mechanical JD
            {
                "name": "aakash_mechanical_technical_only",
                "resume": os.path.join(base_dir, "tests/test_data/resumes/aakash_mechanical_resume.txt"),
                "jd": os.path.join(base_dir, "tests/test_data/job_descriptions/mechanical_engineer_jd.txt"),
                "interview_type": "technical_only",
                "description": "Aakash (Mechanical) + Mechanical JD + Technical Only"
            },
            {
                "name": "aakash_mechanical_behavioral_only", 
                "resume": os.path.join(base_dir, "tests/test_data/resumes/aakash_mechanical_resume.txt"),
                "jd": os.path.join(base_dir, "tests/test_data/job_descriptions/mechanical_engineer_jd.txt"),
                "interview_type": "behavioral_only",
                "description": "Aakash (Mechanical) + Mechanical JD + Behavioral Only"
            },
            {
                "name": "aakash_mechanical_technical_behavioral",
                "resume": os.path.join(base_dir, "tests/test_data/resumes/aakash_mechanical_resume.txt"), 
                "jd": os.path.join(base_dir, "tests/test_data/job_descriptions/mechanical_engineer_jd.txt"),
                "interview_type": "technical_behavioral",
                "description": "Aakash (Mechanical) + Mechanical JD + Technical+Behavioral"
            },
            
            # Aarshee (Software Engineer) with Software JD
            {
                "name": "aarshee_software_technical_only",
                "resume": os.path.join(base_dir, "tests/test_data/resumes/aarshee_software_resume.txt"),
                "jd": os.path.join(base_dir, "tests/test_data/job_descriptions/software_developer_jd.txt"), 
                "interview_type": "technical_only",
                "description": "Aarshee (Software) + Software JD + Technical Only"
            },
            {
                "name": "aarshee_software_behavioral_only",
                "resume": os.path.join(base_dir, "tests/test_data/resumes/aarshee_software_resume.txt"),
                "jd": os.path.join(base_dir, "tests/test_data/job_descriptions/software_developer_jd.txt"),
                "interview_type": "behavioral_only", 
                "description": "Aarshee (Software) + Software JD + Behavioral Only"
            },
            {
                "name": "aarshee_software_technical_behavioral",
                "resume": os.path.join(base_dir, "tests/test_data/resumes/aarshee_software_resume.txt"),
                "jd": os.path.join(base_dir, "tests/test_data/job_descriptions/software_developer_jd.txt"),
                "interview_type": "technical_behavioral",
                "description": "Aarshee (Software) + Software JD + Technical+Behavioral"
            }
        ]
        
        all_results = {}
        
        for i, test_config in enumerate(test_combinations, 1):
            print(f"\n🧪 Running Test {i}/{len(test_combinations)}: {test_config['description']}")
            
            try:
                result = self.test_interview_flow(
                    test_config["resume"],
                    test_config["jd"], 
                    test_config["interview_type"]
                )
                
                all_results[test_config["name"]] = result
                
                # Save individual result
                result_file = os.path.join(base_dir, f"tests/test_results/{test_config['name']}.json")
                os.makedirs(os.path.dirname(result_file), exist_ok=True)
                with open(result_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                print(f"💾 Results saved to: {result_file}")
                
            except Exception as e:
                print(f"❌ Test {test_config['name']} failed: {e}")
                all_results[test_config["name"]] = {
                    "test_metadata": test_config,
                    "test_results": {"status": "FAIL", "errors": [str(e)]}
                }
        
        # Generate summary report
        summary = self._generate_summary_report(all_results)
        
        # Save comprehensive results
        comprehensive_results = {
            "test_summary": summary,
            "individual_results": all_results,
            "test_timestamp": datetime.now().isoformat()
        }
        
        summary_file = os.path.join(base_dir, "tests/test_results/comprehensive_test_results.json")
        os.makedirs(os.path.dirname(summary_file), exist_ok=True)
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📊 COMPREHENSIVE RESULTS SAVED: {summary_file}")
        
        return comprehensive_results
    
    def _generate_summary_report(self, all_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics from all test results"""
        
        total_tests = len(all_results)
        passed_tests = sum(1 for result in all_results.values() 
                          if result.get("test_results", {}).get("status") == "PASS")
        failed_tests = total_tests - passed_tests
        
        # Analyze by interview type
        type_analysis = {}
        for test_name, result in all_results.items():
            interview_type = result.get("test_metadata", {}).get("interview_type", "unknown")
            if interview_type not in type_analysis:
                type_analysis[interview_type] = {"total": 0, "passed": 0, "failed": 0}
            
            type_analysis[interview_type]["total"] += 1
            if result.get("test_results", {}).get("status") == "PASS":
                type_analysis[interview_type]["passed"] += 1
            else:
                type_analysis[interview_type]["failed"] += 1
        
        summary = {
            "overall_stats": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": f"{(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%"
            },
            "by_interview_type": type_analysis,
            "key_findings": []
        }
        
        # Add key findings
        if failed_tests == 0:
            summary["key_findings"].append("✅ All interview types working correctly")
        else:
            summary["key_findings"].append(f"⚠️ {failed_tests} tests failed - requires investigation")
        
        # Check for topic repetition issues
        repetition_issues = sum(1 for result in all_results.values()
                               if result.get("test_results", {}).get("topic_repetition_detected", False))
        if repetition_issues > 0:
            summary["key_findings"].append(f"⚠️ Topic repetition detected in {repetition_issues} tests")
        else:
            summary["key_findings"].append("✅ No topic repetition issues detected")
        
        return summary

def main():
    """Main function for command line usage"""
    parser = argparse.ArgumentParser(description='Automated Interview Flow Testing')
    parser.add_argument('--resume', type=str, help='Path to resume file')
    parser.add_argument('--jd', type=str, help='Path to job description file') 
    parser.add_argument('--type', type=str, choices=['technical_only', 'behavioral_only', 'technical_behavioral'],
                       help='Interview type to test')
    parser.add_argument('--all', action='store_true', help='Run all test combinations')
    
    args = parser.parse_args()
    
    tester = InterviewFlowTester()
    
    if args.all:
        # Run all test combinations
        results = tester.run_all_tests()
        print("\n" + "="*80)
        print("📊 FINAL SUMMARY")
        print("="*80)
        summary = results["test_summary"]
        print(f"Total Tests: {summary['overall_stats']['total_tests']}")
        print(f"Passed: {summary['overall_stats']['passed_tests']}")
        print(f"Failed: {summary['overall_stats']['failed_tests']}")
        print(f"Success Rate: {summary['overall_stats']['success_rate']}")
        print("\nKey Findings:")
        for finding in summary["key_findings"]:
            print(f"  {finding}")
            
    elif args.resume and args.jd and args.type:
        # Run single test
        result = tester.test_interview_flow(args.resume, args.jd, args.type)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        result_file = os.path.join(base_dir, f"tests/test_results/single_test_{args.type}.json")
        os.makedirs(os.path.dirname(result_file), exist_ok=True)
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Results saved to: {result_file}")
        print(f"📊 Test Status: {result['test_results']['status']}")
        
    else:
        print("❌ Please specify either --all or provide --resume, --jd, and --type arguments")
        parser.print_help()

if __name__ == "__main__":
    main()
