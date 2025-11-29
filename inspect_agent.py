
import sys
from pathlib import Path
from importlib import import_module

# Add paths
project_root = Path("/Users/felixdevasia/projects/hackathons/google/FarmFlow")
sys.path.insert(0, str(project_root / "agents" / "crop_advisor_agent"))

try:
    from crop_advisor import root_agent
    print(f"Agent Name: {root_agent.name}")
    print(f"Model: {root_agent.model}")
    print(f"Tools: {len(root_agent.tools)}")
    for tool in root_agent.tools:
        print(f" - Tool: {tool}")
    from market_analyst_a2a import market_analyst_a2a
    print(f"Has as_tool: {hasattr(market_analyst_a2a, 'as_tool')}")
except Exception as e:
    print(f"Error: {e}")
