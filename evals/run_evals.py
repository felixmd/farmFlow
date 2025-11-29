
import asyncio
import argparse
import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from google.adk.evaluation.agent_evaluator import AgentEvaluator
from google.adk.evaluation.eval_set import EvalSet
from google.adk.evaluation.eval_config import get_evaluation_criteria_or_default
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def run_suite(suite_name: str):
    print(f"Running suite: {suite_name}")
    
    base_dir = Path(__file__).parent
    data_dir = base_dir / "data"
    config_dir = base_dir / "config"
    
    if suite_name == "market":
        agent_module = "agents.crop_advisor_agent.market_analyst_a2a"
        eval_set_path = data_dir / "market_analyst.test.json"
        config_path = config_dir / "financial_rubric.json"
        agent_name = "market_analyst_a2a"
    elif suite_name == "agronomist":
        agent_module = "agents.crop_advisor_agent.agronomist_a2a"
        eval_set_path = data_dir / "agronomist.test.json"
        config_path = config_dir / "agronomist_rubric.json"
        agent_name = "agronomist_a2a"
    elif suite_name == "crop_advisor":
        agent_module = "agents.crop_advisor_agent.crop_advisor"
        eval_set_path = data_dir / "crop_advisor.test.json"
        config_path = config_dir / "a2a_rubric.json"
        agent_name = "crop_investment_advisor"
    else:
        print(f"Unknown suite: {suite_name}")
        return

    # Load EvalSet
    if not eval_set_path.exists():
        print(f"Error: Eval set file not found: {eval_set_path}")
        return
        
    with open(eval_set_path, "r") as f:
        eval_set = EvalSet.model_validate_json(f.read())

    # Load EvalConfig
    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}")
        return

    eval_config = get_evaluation_criteria_or_default(str(config_path))

    # Run Eval
    print(f"Starting evaluation for {agent_name}...")
    try:
        await AgentEvaluator.evaluate_eval_set(
            agent_module=agent_module,
            eval_set=eval_set,
            eval_config=eval_config,
            agent_name=agent_name,
            print_detailed_results=False
        )
        print("Evaluation completed successfully.")
    except Exception as e:
        print(f"Evaluation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("suite", choices=["market", "agronomist", "crop_advisor"], help="Eval suite to run")
    args = parser.parse_args()
    
    asyncio.run(run_suite(args.suite))
