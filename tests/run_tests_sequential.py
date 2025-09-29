#!/usr/bin/env python3
"""
Sequential Test Runner - Runs one test at a time to avoid API rate limits
"""

import sys
import os
import time

# Add the parent directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from test_interview_flow import InterviewFlowTester

def run_sequential_tests():
    print("🚀 Starting Sequential Automated Interview Testing")
    print("Running one test at a time to avoid API rate limits...")
    print("=" * 80)
    
    # Define test combinations
    test_combinations = [
        {
            "name": "aakash_mechanical_technical_only",
            "description": "Aakash (Mechanical) + Mechanical JD + Technical Only",
            "resume": "aakash_mechanical_resume.txt",
            "jd": "mechanical_engineer_jd.txt",
            "interview_type": "technical_only"
        },
        {
            "name": "aakash_mechanical_behavioral_only",
            "description": "Aakash (Mechanical) + Mechanical JD + Behavioral Only", 
            "resume": "aakash_mechanical_resume.txt",
            "jd": "mechanical_engineer_jd.txt",
            "interview_type": "behavioral_only"
        },
        {
            "name": "aakash_mechanical_technical_behavioral",
            "description": "Aakash (Mechanical) + Mechanical JD + Technical+Behavioral",
            "resume": "aakash_mechanical_resume.txt",
            "jd": "mechanical_engineer_jd.txt",
            "interview_type": "technical_behavioral"
        },
        {
            "name": "aarshee_software_technical_only",
            "description": "Aarshee (Software) + Software JD + Technical Only",
            "resume": "aarshee_software_resume.txt",
            "jd": "software_developer_jd.txt",
            "interview_type": "technical_only"
        },
        {
            "name": "aarshee_software_behavioral_only",
            "description": "Aarshee (Software) + Software JD + Behavioral Only",
            "resume": "aarshee_software_resume.txt",
            "jd": "software_developer_jd.txt",
            "interview_type": "behavioral_only"
        },
        {
            "name": "aarshee_software_technical_behavioral",
            "description": "Aarshee (Software) + Software JD + Technical+Behavioral",
            "resume": "aarshee_software_resume.txt",
            "jd": "software_developer_jd.txt",
            "interview_type": "technical_behavioral"
        }
    ]
    
    # Get base directory for absolute paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Initialize tester
    tester = InterviewFlowTester()
    all_results = {}
    
    for i, test_config in enumerate(test_combinations, 1):
        print(f"\n{'='*80}")
        print(f"🧪 RUNNING TEST {i}/6: {test_config['description']}")
        print(f"{'='*80}")
        
        # Build full paths
        resume_path = os.path.join(base_dir, f"tests/test_data/resumes/{test_config['resume']}")
        jd_path = os.path.join(base_dir, f"tests/test_data/job_descriptions/{test_config['jd']}")
        
        try:
            # Run individual test
            print(f"📄 Resume: {test_config['resume']}")
            print(f"💼 Job Description: {test_config['jd']}")
            print(f"🎯 Interview Type: {test_config['interview_type']}")
            print(f"⏱️  Starting test...")
            
            result = tester.test_interview_flow(
                resume_path,
                jd_path,
                test_config['interview_type']
            )
            
            all_results[test_config["name"]] = result
            
            # Save individual result
            result_file = os.path.join(base_dir, f"tests/test_results/{test_config['name']}.json")
            os.makedirs(os.path.dirname(result_file), exist_ok=True)
            
            import json
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            # Show result summary
            status = result.get("test_results", {}).get("status", "UNKNOWN")
            total_turns = result.get("test_results", {}).get("total_turns", 0)
            completed = result.get("test_results", {}).get("interview_completed_successfully", False)
            
            print(f"\n📊 TEST {i} RESULTS:")
            print(f"   Status: {status}")
            print(f"   Total Turns: {total_turns}")
            print(f"   Completed Successfully: {completed}")
            print(f"   Results saved to: {result_file}")
            
            if status == "PASS":
                print(f"✅ Test {i} PASSED!")
            else:
                print(f"❌ Test {i} FAILED!")
                errors = result.get("test_results", {}).get("errors", [])
                if errors:
                    print(f"   Errors: {errors}")
            
        except Exception as e:
            print(f"❌ Test {test_config['name']} failed with exception: {e}")
            all_results[test_config["name"]] = {
                "test_metadata": test_config,
                "test_results": {"status": "FAIL", "errors": [str(e)]}
            }
        
        # Wait between tests to avoid rate limits
        if i < len(test_combinations):
            print(f"\n⏳ Waiting 30 seconds before next test to avoid API rate limits...")
            time.sleep(30)
    
    # Generate final summary
    print(f"\n{'='*80}")
    print("🎉 ALL SEQUENTIAL TESTS COMPLETED!")
    print(f"{'='*80}")
    
    total_tests = len(all_results)
    passed_tests = sum(1 for result in all_results.values() 
                      if result.get("test_results", {}).get("status") == "PASS")
    failed_tests = total_tests - passed_tests
    
    print(f"📊 FINAL RESULTS:")
    print(f"   Total Tests: {total_tests}")
    print(f"   Passed: {passed_tests}")
    print(f"   Failed: {failed_tests}")
    print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    # Show individual results
    print(f"\n📋 INDIVIDUAL TEST RESULTS:")
    for i, (test_name, result) in enumerate(all_results.items(), 1):
        status = result.get("test_results", {}).get("status", "UNKNOWN")
        total_turns = result.get("test_results", {}).get("total_turns", 0)
        status_icon = "✅" if status == "PASS" else "❌"
        print(f"   {i}. {test_name}: {status_icon} {status} ({total_turns} turns)")
    
    # Save comprehensive results
    from datetime import datetime
    comprehensive_results = {
        "test_summary": {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": f"{(passed_tests/total_tests)*100:.1f}%"
        },
        "individual_results": all_results,
        "test_timestamp": datetime.now().isoformat()
    }
    
    summary_file = os.path.join(base_dir, "tests/test_results/comprehensive_sequential_results.json")
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(comprehensive_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📁 Results saved in: tests/test_results/")
    print(f"   - Individual JSONs: {total_tests} files")
    print(f"   - Comprehensive: comprehensive_sequential_results.json")
    
    if passed_tests == total_tests:
        print(f"\n🎉 ALL TESTS PASSED! Interview system working perfectly!")
    else:
        print(f"\n⚠️  {failed_tests} tests need investigation")
    
    return comprehensive_results

if __name__ == "__main__":
    run_sequential_tests()
