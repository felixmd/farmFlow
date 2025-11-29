
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from google.adk.evaluation.eval_set import EvalSet

json_path = "evals/data/market_analyst.test.json"

with open(json_path, "r") as f:
    content = f.read()
    print(f"JSON Content:\n{content}\n")
    
    try:
        eval_set = EvalSet.model_validate_json(content)
        print("Successfully parsed EvalSet!")
        print(f"Eval Set ID: {eval_set.eval_set_id}")
        print(f"Number of cases: {len(eval_set.eval_cases)}")
        
        for i, case in enumerate(eval_set.eval_cases):
            print(f"\nCase {i+1} ID: {case.eval_id}")
            print(f"Conversation: {case.conversation}")
            print(f"Conversation Scenario: {case.conversation_scenario}")
            
            if case.conversation is None:
                print("❌ ERROR: Conversation is None!")
            else:
                print(f"✅ Conversation length: {len(case.conversation)}")
                
    except Exception as e:
        print(f"❌ Failed to parse: {e}")
