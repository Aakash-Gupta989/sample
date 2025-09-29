#!/usr/bin/env python3
"""
Simple test runner script
Usage: python run_all_tests.py
"""

import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from test_interview_flow import InterviewFlowTester

def main():
    print("🚀 Starting Automated Interview Testing System")
    print("This will test all 6 combinations:")
    print("  - Aakash (Mechanical) + Mechanical JD: Technical, Behavioral, Combined")
    print("  - Aarshee (Software) + Software JD: Technical, Behavioral, Combined")
    print("\nStarting tests...")
    
    tester = InterviewFlowTester()
    results = tester.run_all_tests()
    
    print("\n" + "="*80)
    print("🎉 ALL TESTS COMPLETED!")
    print("="*80)
    
    summary = results["test_summary"]
    print(f"📊 RESULTS SUMMARY:")
    print(f"   Total Tests: {summary['overall_stats']['total_tests']}")
    print(f"   Passed: {summary['overall_stats']['passed_tests']}")
    print(f"   Failed: {summary['overall_stats']['failed_tests']}")
    print(f"   Success Rate: {summary['overall_stats']['success_rate']}")
    
    print(f"\n📁 Results saved in: tests/test_results/")
    print(f"   - Individual test JSONs: 6 files")
    print(f"   - Comprehensive results: comprehensive_test_results.json")
    
    print(f"\n🔍 Key Findings:")
    for finding in summary["key_findings"]:
        print(f"   {finding}")
    
    print(f"\n✅ Testing complete! Check the JSON files for detailed analysis.")

if __name__ == "__main__":
    main()
