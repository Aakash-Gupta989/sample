"""
Elite Coding Question Generator
Generates LeetCode-style algorithmic challenges tailored to specific job descriptions
"""
import json
import random
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import re

class Difficulty(Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"

@dataclass
class CodingQuestion:
    """Elite coding question with complete metadata"""
    title: str
    difficulty: Difficulty
    problem_statement: str
    example: Dict[str, str]
    constraints: List[str]
    primary_pattern: str
    data_structures: str
    optimal_complexity: Dict[str, str]
    follow_up_questions: List[str]
    template: str
    test_cases: List[Dict]
    id: str

class CodingQuestionGenerator:
    """Generates job-specific LeetCode-style coding challenges"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.used_patterns = []
        self._generating = False  # Simple lock to prevent simultaneous generation
        self._last_generation_time = 0  # Track last generation time
    
    def generate_question(self, job_description: str, position: str, seniority_level: str = "mid") -> CodingQuestion:
        """Generate a coding question tailored to the job description"""
        
        # Simple lock to prevent simultaneous generation and rate limiting
        import time
        current_time = time.time()
        
        if self._generating:
            raise Exception("Question generation already in progress. Please wait.")
        
        # Prevent requests within 10 seconds of each other to avoid rate limits
        if current_time - self._last_generation_time < 10:
            wait_time = 10 - (current_time - self._last_generation_time)
            print(f"⏳ Rate limiting: waiting {wait_time:.1f}s before generating question...")
            time.sleep(wait_time)
        
        self._generating = True
        self._last_generation_time = time.time()
        
        try:
            max_retries = 2
            last_error = None
            for attempt in range(max_retries + 1):
                # Create/augment prompt per attempt
                prompt = self._create_elite_prompt(job_description, position, seniority_level)
                if attempt > 0 and last_error:
                    prompt += f"\n\n### VALIDATION FEEDBACK ###\nPlease regenerate fixing these issues: {last_error}. Return JSON only."

                response = self.llm_client.generate_response(prompt, temperature=0.5)

                cleaned_response = self._clean_llm_response(response)

                try:
                    question_data = json.loads(cleaned_response)
                except json.JSONDecodeError as json_err:
                    print(f"⚠️  JSON parsing error: {json_err}")
                    print(f"Raw response: {response[:200]}...")
                    print(f"Cleaned response: {cleaned_response[:200]}...")
                    
                    # Try to fix the JSON
                    try:
                        fixed_json = self._fix_malformed_json(cleaned_response)
                        question_data = json.loads(fixed_json)
                        print("✅ Successfully fixed malformed JSON")
                    except Exception as fix_err:
                        print(f"❌ Could not fix JSON: {fix_err}")
                        last_error = f"Invalid JSON format: {json_err}"
                        if attempt < max_retries:
                            continue
                        raise Exception(f"JSON parsing failed: {json_err}")
                except Exception as e:
                    last_error = f"JSON parsing error: {e}"
                    if attempt < max_retries:
                        continue
                    raise

                validation_error = self._validate_question_data(question_data)
                if validation_error:
                    last_error = validation_error
                    if attempt < max_retries:
                        continue
                    raise Exception(f"Validation failed: {validation_error}")

                # Build templates and sanitize test cases
                templates = self._generate_template(question_data, "python")
                test_cases = self._sanitize_test_cases(question_data)

                # Extract example from first test case for compatibility
                structured_test_cases = question_data.get("structuredTestCases", {})
                first_test_case = next(iter(structured_test_cases.values()), {})
                problem_type = question_data.get("problemType", "function")
                
                if problem_type == "function":
                    example = {
                        "input": str(first_test_case.get("input", "")),
                        "output": str(first_test_case.get("expectedOutput", "")),
                        "explanation": first_test_case.get("rationale", "")
                    }
                else:  # class
                    # For class problems, create a simplified example from operations
                    operations = first_test_case.get("operations", [])
                    if operations:
                        example = {
                            "input": f"Operations: {json.dumps(operations[:2])}...",  # Show first 2 operations
                            "output": "See operations array for expected outputs",
                            "explanation": first_test_case.get("rationale", "")
                        }
                    else:
                        example = {
                            "input": "Class instantiation and method calls",
                            "output": "Various outputs based on method calls",
                            "explanation": first_test_case.get("rationale", "")
                        }

                coding_question = CodingQuestion(
                    title=question_data.get("title", "Coding Challenge"),
                    difficulty=Difficulty(question_data.get("difficulty", "Medium")),
                    problem_statement=question_data.get("problemStatement", ""),
                    example=example,
                    constraints=["See problem statement for constraints"],  # Placeholder
                    primary_pattern=question_data.get("primaryPattern", ""),
                    data_structures="Various",  # Placeholder
                    optimal_complexity={"time": "O(n)", "space": "O(1)"},  # Placeholder
                    follow_up_questions=["How would you optimize this further?"],  # Placeholder
                    template=templates,
                    test_cases=test_cases,
                    id=f"coding_{random.randint(1000, 9999)}"
                )

                if coding_question.primary_pattern and coding_question.primary_pattern not in self.used_patterns:
                    self.used_patterns.append(coding_question.primary_pattern)
                    if len(self.used_patterns) > 5:
                        self.used_patterns.pop(0)

                return coding_question
            # Should not get here
            raise Exception("Failed to generate a valid coding question")
            
        except Exception as e:
            print(f"Error generating coding question: {e}")
            # Surface failure to caller so UI can show proper error instead of fallback
            raise
        finally:
            self._generating = False  # Always release the lock
    
    def _create_elite_prompt(self, job_description: str, position: str, seniority_level: str) -> str:
        """Create the elite prompt based on your specification"""
        
        # Determine difficulty based on seniority - only Medium or Hard
        difficulty_mapping = {
            "junior": "Medium",
            "mid": "Medium", 
            "senior": "Hard",
        }
        target_difficulty = difficulty_mapping.get(str(seniority_level).lower(), "Medium")
        
        # Create the system prompt
        prompt = f"""### ROLE ###
You are a world-class Interview Engineer and Content Designer at a top-tier tech company. Your defining characteristic is an obsession with precision, clarity, and logical consistency. You are tasked with creating a flawless, LeetCode-style coding challenge. You must analyze the problem's requirements to decide if it is a simple stateless function or a more complex stateful class. Your primary goal is to produce a question that is unambiguous, engaging, and comes with a rich set of test cases that validate a candidate's understanding completely. You find lazy, invalid, or non-deterministic test cases unacceptable.

### TASK ###
Your task is to first THINK step-by-step about how to create the problem, and then generate one complete coding challenge as a single JSON object based on your reasoning. You must choose the appropriate JSON schema ("function" or "class") that best fits the problem you design.

Job Description: {job_description}
Position: {position}
Target Difficulty: {target_difficulty}

### CRITICAL INSTRUCTIONS ###
1.  **Choose the Right Problem Type:** If the problem is a simple, stateless transformation, choose the `"function"` schema. If it involves maintaining state, processing a stream, or building a specific data structure, you MUST choose the `"class"` schema.
2.  **Ensure Algorithmic Feasibility:** This is a strict rule. The generated problem MUST be solvable efficiently (in polynomial time) within a typical time limit (e.g., 1-2 seconds) given the provided constraints (e.g., N up to 10^5 or higher). You MUST AVOID generating problems that are known to be NP-hard (like the general Traveling Salesman or Bin Packing Problem) UNLESS you provide a specific simplification, constraint, or a greedy strategy in the problem statement that makes an efficient solution possible.
3.  **Think First, Then Format:** Your entire thought process must be captured in the `reasoningChain` key. This must be completed before you fill out the rest of the JSON.
4.  **The `rationale` Key is MANDATORY:** For every single test case, you must include a `rationale` that briefly explains *why* the `expectedOutput` is correct. This is non-negotiable.
5.  **Strictly Adhere to the Chosen JSON Schema:** The entire output must be a single JSON object. Do not add, remove, or rename any keys from your chosen schema. Do not include any text outside of the JSON.

---
### SCHEMA OPTION 1: For `"problemType": "function"` ###
{{
  "problemType": "function",
  "reasoningChain": "(String) Your step-by-step thought process...",
  "title": "(String) A descriptive, engaging title.",
  "difficulty": "(String) 'Easy', 'Medium', or 'Hard'.",
  "problemStatement": "(String) A clear, deterministic problem description for a single function call.",
  "primaryPattern": "(String) The main algorithmic pattern being tested.",
  "structuredTestCases": {{
    "generalCase": {{"name": "(String)", "input": "(JSON Value)", "expectedOutput": "(JSON Value)", "rationale": "(String)"}},
    "edgeCase_EmptyInput": {{"name": "(String)", "input": "(JSON Value)", "expectedOutput": "(JSON Value)", "rationale": "(String)"}},
    "edgeCase_SingleElement": {{"name": "(String)", "input": "(JSON Value)", "expectedOutput": "(JSON Value)", "rationale": "(String)"}},
    "complexCase_Logic": {{"name": "(String)", "input": "(JSON Value)", "expectedOutput": "(JSON Value)", "rationale": "(String)"}},
    "complexCase_Constraints": {{"name": "(String)", "input": "(JSON Value)", "expectedOutput": "(JSON Value)", "rationale": "(String)"}}
  }}
}}

---
### SCHEMA OPTION 2: For `"problemType": "class"` ###
{{
  "problemType": "class",
  "reasoningChain": "(String) Your step-by-step thought process...",
  "title": "(String) A descriptive, engaging title.",
  "difficulty": "(String) 'Easy', 'Medium', or 'Hard'.",
  "problemStatement": "(String) A clear problem description that requires implementing a class with specific methods to handle state or a stream of data.",
  "classSetup": {{
    "className": "(String) The name of the class to be implemented (e.g., 'PacketThrottler').",
    "constructor": {{"signature": "(String) e.g., '__init__(self, threshold, window_size)'", "description": "(String) Description of constructor parameters."}},
    "methods": [{{"signature": "(String) e.g., 'addPacket(self, timestamp, size)'", "description": "(String) Description of the method's purpose and return value."}}]
  }},
  "primaryPattern": "(String) The main algorithmic pattern or data structure.",
  "structuredTestCases": {{
    "generalCase": {{"name": "(String)", "rationale": "(String)", "operations": "[Array of operation objects]"}},
    "edgeCase_NoOperations": {{"name": "(String)", "rationale": "(String)", "operations": "[Array of operation objects]"}},
    "complexCase_StateChange": {{"name": "(String)", "rationale": "(String)", "operations": "[Array of operation objects]"}},
    "complexCase_OrderMatters": {{"name": "(String)", "rationale": "(String)", "operations": "[Array of operation objects]"}},
    "complexCase_Constraints": {{"name": "(String)", "rationale": "(String)", "operations": "[Array of operation objects]"}}
  }}
}}

---
### STRUCTURE FOR `operations` ARRAY (for class-based tests) ###
The `"operations"` array must contain a sequence of objects, each representing a method call.
* **For the constructor:** `{{"operation": "constructor", "params": {{"key": "value"}}, "expectedOutput": null}}`
* **For other methods:** `{{"operation": "methodName", "params": {{"key": "value"}}, "expectedOutput": "(JSON Value)"}}`

### END OF PROMPT ###"""

        return prompt
    
    def _clean_llm_response(self, response: str) -> str:
        cleaned = response.strip()
        
        # Remove markdown code blocks
        if cleaned.startswith('```json'):
            cleaned = cleaned[7:]
        elif cleaned.startswith('```'):
            cleaned = cleaned[3:]
        if cleaned.endswith('```'):
            cleaned = cleaned[:-3]
        
        # Find the first { and last } to extract just the JSON object
        first_brace = cleaned.find('{')
        last_brace = cleaned.rfind('}')
        
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            cleaned = cleaned[first_brace:last_brace + 1]
        
        return cleaned.strip()
    
    def _fix_malformed_json(self, content: str) -> str:
        """Attempt to fix common JSON formatting issues"""
        import re
        try:
            # Common fixes for malformed JSON
            fixed_content = content
            
            # Remove trailing commas before closing braces/brackets
            fixed_content = re.sub(r',\s*}', '}', fixed_content)
            fixed_content = re.sub(r',\s*]', ']', fixed_content)
            
            # Fix unescaped quotes in strings - basic attempt
            # Replace unescaped quotes inside string values (very basic)
            lines = fixed_content.split('\n')
            fixed_lines = []
            for line in lines:
                # If line contains a string value with unescaped quotes, try to fix
                if ':' in line and '"' in line:
                    # This is a very basic fix - more complex cases may still fail
                    # Look for patterns like "key": "value with "quote" inside"
                    if line.count('"') > 2:
                        # Try to escape quotes that are not at the beginning/end of values
                        line = re.sub(r'(?<!\\)"(?=.*":)', '\\"', line)
                
                fixed_lines.append(line)
            
            fixed_content = '\n'.join(fixed_lines)
            
            # Try to parse the fixed content
            json.loads(fixed_content)
            return fixed_content
            
        except Exception:
            # If we can't fix it, return the original content
            return content
    
    def _validate_question_data(self, data: Dict) -> Optional[str]:
        # Validate top-level required fields
        required_top = [
            "problemType", "reasoningChain", "title", "difficulty", 
            "problemStatement", "primaryPattern", "structuredTestCases"
        ]
        for k in required_top:
            if k not in data:
                return f"Missing field: {k}"
        
        # Validate problem type
        problem_type = data.get("problemType")
        if problem_type not in ["function", "class"]:
            return "problemType must be 'function' or 'class'"
        
        # Validate difficulty
        if data.get("difficulty") not in [d.value for d in Difficulty]:
            return "Invalid difficulty"
        
        # Validate problem statement length
        if len(str(data.get("problemStatement", ""))) < 100:
            return "problemStatement too short"
        
        # Validate class setup if problem type is class
        if problem_type == "class":
            class_setup = data.get("classSetup", {})
            if not class_setup:
                return "Missing classSetup for class problem type"
            
            required_class_fields = ["className", "constructor", "methods"]
            for field in required_class_fields:
                if field not in class_setup:
                    return f"classSetup missing field: {field}"
        
        # Validate structured test cases
        structured_test_cases = data.get("structuredTestCases", {})
        
        if problem_type == "function":
            required_test_case_keys = [
                "generalCase", "edgeCase_EmptyInput", "edgeCase_SingleElement", 
                "complexCase_Logic", "complexCase_Constraints"
            ]
            required_tc_fields = ["name", "input", "expectedOutput", "rationale"]
        else:  # class
            required_test_case_keys = [
                "generalCase", "edgeCase_NoOperations", "complexCase_StateChange", 
                "complexCase_OrderMatters", "complexCase_Constraints"
            ]
            required_tc_fields = ["name", "rationale", "operations"]
        
        for test_case_key in required_test_case_keys:
            if test_case_key not in structured_test_cases:
                return f"Missing test case: {test_case_key}"
            
            test_case = structured_test_cases[test_case_key]
            
            for field in required_tc_fields:
                if field not in test_case:
                    return f"Test case {test_case_key} missing field: {field}"
                
                # Validate that fields are not empty or "varies"
                if field != "operations":  # operations is an array, handle separately
                    value = str(test_case.get(field, "")).strip().lower()
                    if not value or value == "varies":
                        return f"Test case {test_case_key}.{field} cannot be empty or 'varies'"
            
            # Validate operations array for class problems
            if problem_type == "class":
                operations = test_case.get("operations", [])
                if not isinstance(operations, list):
                    return f"Test case {test_case_key}.operations must be an array"
        
        return None
    
    def _sanitize_test_cases(self, data: Dict) -> List[Dict]:
        """Convert structured test cases to a list format for compatibility."""
        def to_string(v):
            if isinstance(v, (dict, list)):
                return json.dumps(v)
            return str(v)
        
        result = []
        structured_test_cases = data.get("structuredTestCases", {})
        problem_type = data.get("problemType", "function")
        
        # Convert each structured test case to the expected format
        for test_case_key, test_case in structured_test_cases.items():
            if problem_type == "function":
                # Function-based test cases have input/expectedOutput
                result.append({
                    "input": to_string(test_case.get("input", "")),
                    "expected": to_string(test_case.get("expectedOutput", "")),
                    "description": test_case.get("name", test_case_key)
                })
            else:  # class
                # Class-based test cases have operations array
                operations = test_case.get("operations", [])
                operations_str = to_string(operations)
                result.append({
                    "input": f"Operations: {operations_str}",
                    "expected": "See operations for expected outputs",
                    "description": test_case.get("name", test_case_key)
                })
        
        return result
    
    def _generate_template(self, question_data: Dict, language: str = "python") -> Dict[str, str]:
        """Generate template code for the question in multiple languages"""
        
        title = question_data.get("title", "solution")
        function_name = self._title_to_function_name(title)
        class_name = self._title_to_class_name(title)
        problem_desc = question_data.get("problemStatement", "Solve the problem")[:100]
        
        templates = {}
        
        # Python template
        templates["python"] = f'''def {function_name}(nums):
    """
    {problem_desc}...
    
    Args:
        nums: Input array/list
    
    Returns:
        Result based on problem requirements
    """
    # Your code here
    pass

# Test cases
if __name__ == "__main__":
    # Test case 1
    test_input_1 = [2, 7, 11, 15]
    result_1 = {function_name}(test_input_1)
    print(f"Test 1 - Input: {{test_input_1}}, Output: {{result_1}}")
    
    # Test case 2
    test_input_2 = [3, 2, 4]
    result_2 = {function_name}(test_input_2)
    print(f"Test 2 - Input: {{test_input_2}}, Output: {{result_2}}")
'''

        # JavaScript template
        templates["javascript"] = f'''/**
 * {problem_desc}...
 * @param {{number[]}} nums - Input array
 * @return {{number[]|number}} Result based on problem requirements
 */
function {function_name}(nums) {{
    // Your code here
    
}}

// Test cases
console.log("Test 1:", {function_name}([2, 7, 11, 15]));
console.log("Test 2:", {function_name}([3, 2, 4]));
'''

        # Java template
        templates["java"] = f'''import java.util.*;

public class {class_name} {{
    /**
     * {problem_desc}...
     * @param nums Input array
     * @return Result based on problem requirements
     */
    public int[] {function_name}(int[] nums) {{
        // Your code here
        return new int[]{{}};
    }}
    
    public static void main(String[] args) {{
        {class_name} solution = new {class_name}();
        
        // Test case 1
        int[] test1 = {{2, 7, 11, 15}};
        System.out.println("Test 1: " + Arrays.toString(solution.{function_name}(test1)));
        
        // Test case 2
        int[] test2 = {{3, 2, 4}};
        System.out.println("Test 2: " + Arrays.toString(solution.{function_name}(test2)));
    }}
}}
'''

        # C++ template
        templates["cpp"] = f'''#include <vector>
#include <iostream>
using namespace std;

class {class_name} {{
public:
    /**
     * {problem_desc}...
     * @param nums Input vector
     * @return Result based on problem requirements
     */
    vector<int> {function_name}(vector<int>& nums) {{
        // Your code here
        return {{}};
    }}
}};

int main() {{
    {class_name} solution;
    
    // Test case 1
    vector<int> test1 = {{2, 7, 11, 15}};
    vector<int> result1 = solution.{function_name}(test1);
    cout << "Test 1: ";
    for(int x : result1) cout << x << " ";
    cout << endl;
    
    // Test case 2
    vector<int> test2 = {{3, 2, 4}};
    vector<int> result2 = solution.{function_name}(test2);
    cout << "Test 2: ";
    for(int x : result2) cout << x << " ";
    cout << endl;
    
    return 0;
}}
'''

        return templates
    
    def _generate_test_cases(self, question_data: Dict) -> List[Dict]:
        # Deprecated in favor of _sanitize_test_cases which uses LLM-provided cases
        return self._sanitize_test_cases(question_data)
    
    def _title_to_function_name(self, title: str) -> str:
        """Convert title to valid function name"""
        # Remove special characters and convert to snake_case
        import re
        clean_title = re.sub(r'[^a-zA-Z0-9\s]', '', title)
        words = clean_title.lower().split()
        return '_'.join(words[:3])  # Limit to 3 words
    
    def _title_to_class_name(self, title: str) -> str:
        """Convert title to valid class name"""
        import re
        clean_title = re.sub(r'[^a-zA-Z0-9\s]', '', title)
        words = clean_title.split()
        return ''.join(word.capitalize() for word in words[:3])  # Limit to 3 words
    
    def _get_fallback_question(self) -> CodingQuestion:
        """Return a fallback question if generation fails"""
        return CodingQuestion(
            title="Two Sum",
            difficulty=Difficulty.EASY,
            problem_statement="Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.",
            example={
                "input": "nums = [2,7,11,15], target = 9",
                "output": "[0,1]"
            },
            constraints=[
                "2 <= nums.length <= 10^4",
                "-10^9 <= nums[i] <= 10^9",
                "-10^9 <= target <= 10^9",
                "Only one valid answer exists"
            ],
            primary_pattern="Hash Map",
            data_structures="Hash Map",
            optimal_complexity={"time": "O(n)", "space": "O(n)"},
            follow_up_questions=[
                "Can you solve it in less than O(n^2) time complexity?",
                "What if the array was sorted?",
                "How would you handle duplicate values?"
            ],
            template='''def two_sum(nums, target):
    """
    Given an array of integers nums and an integer target,
    return indices of the two numbers such that they add up to target.
    """
    # Your code here
    pass

# Test cases
if __name__ == "__main__":
    result1 = two_sum([2, 7, 11, 15], 9)
    print(f"Test 1: {result1}")  # Expected: [0, 1]
    
    result2 = two_sum([3, 2, 4], 6)
    print(f"Test 2: {result2}")  # Expected: [1, 2]
''',
            test_cases=[
                {"input": "[2,7,11,15], target=9", "expected": "[0,1]", "description": "Basic case"},
                {"input": "[3,2,4], target=6", "expected": "[1,2]", "description": "Different order"},
                {"input": "[3,3], target=6", "expected": "[0,1]", "description": "Duplicate values"}
            ],
            id="coding_fallback"
        )

# Global instance
coding_generator = CodingQuestionGenerator(None)  # Will be initialized with LLM client
