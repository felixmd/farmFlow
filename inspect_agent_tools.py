
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "agents" / "crop_advisor_agent"))
from crop_advisor import root_agent as crop_advisor_agent

print(f"Agent: {crop_advisor_agent.name}")
print(f"Tools count: {len(crop_advisor_agent.tools) if crop_advisor_agent.tools else 0}")

if crop_advisor_agent.tools:
    for i, tool in enumerate(crop_advisor_agent.tools):
        print(f"Tool {i+1}: {tool}")
        if hasattr(tool, 'name'):
            print(f"  Name: {tool.name}")
        if hasattr(tool, 'agent'):
            print(f"  Wraps Agent: {tool.agent.name}")

print(f"Sub-agents count: {len(crop_advisor_agent.sub_agents) if crop_advisor_agent.sub_agents else 0}")
if crop_advisor_agent.sub_agents:
    for i, agent in enumerate(crop_advisor_agent.sub_agents):
        print(f"Sub-agent {i+1}: {agent.name}")
