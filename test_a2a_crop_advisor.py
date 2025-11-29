"""
A2A (Agent-to-Agent) Protocol Demonstration
Tests the Crop Investment Advisor agent with sub-agents
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add agent paths
# sys.path.insert(0, str(Path(__file__).parent / "agents" / "crop_advisor_agent"))

from agents.crop_advisor_agent.crop_advisor import root_agent as crop_advisor_agent
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from google.adk.plugins.logging_plugin import LoggingPlugin

# Load environment variables
load_dotenv()

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up Vertex AI
# os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"

print("=" * 80)
print("🤝 A2A PROTOCOL DEMONSTRATION")
print("=" * 80)
print()
print("Testing: Crop Investment Advisor (Parent Agent)")
print("  ├─ Market Analyst (Sub-Agent)")
print("  └─ Agronomist (Sub-Agent)")
print()
print("This demonstrates Agent-to-Agent communication where:")
print("1. Parent agent receives crop comparison query")
print("2. Parent consults Market Analyst sub-agent for financial analysis")
print("3. Parent consults Agronomist sub-agent for growing feasibility")
print("4. Parent synthesizes both responses into final recommendation")
print()
print("=" * 80)
print()

async def test_a2a():
    """Test A2A protocol with crop comparison query"""

    # Create session service
    session_service = InMemorySessionService()

    # Create runner for crop advisor (which has sub-agents)
    crop_advisor_runner = Runner(
        agent=crop_advisor_agent,
        app_name="agents",
        session_service=session_service,
        plugins=[LoggingPlugin()]
    )

    print("✅ Crop Advisor agent initialized with A2A sub-agents")
    print(f"   - Agent: {crop_advisor_agent.name}")
    print(f"   - Sub-agents: {len(crop_advisor_agent.sub_agents)} agents")
    if crop_advisor_agent.sub_agents:
        for sub_agent in crop_advisor_agent.sub_agents:
            print(f"     • {sub_agent.name}")
    print()

    # Create session
    session = await session_service.create_session(
        app_name="agents",
        user_id="test_user"
    )

    print(f"✅ Session created: {session.id}")
    print()

    # Test query - crop comparison requiring both financial and agronomic analysis
    query = "Should I plant cotton or wheat on my 10 acres? Which is better for maximum profit and ease of growing?"

    print(f"📝 Test Query (A2A Scenario):")
    print(f"   {query}")
    print()
    print("-" * 80)
    print("🤖 Crop Advisor Response (with A2A sub-agent calls):")
    print("-" * 80)
    print()

    # Build content
    content = types.Content(
        role='user',
        parts=[types.Part(text=query)]
    )

    # Run agent - this will trigger A2A communication
    full_response = ""
    function_calls_detected = 0
    all_events = []

    # Define sync helper for running agent
    def run_agent_sync(current_content):
        events = []
        for event in crop_advisor_runner.run(
            user_id="test_user",
            session_id=session.id,
            new_message=current_content
        ):
            events.append(event)
        return events

    # Run twice to test history/reuse
    for i in range(2):
        print(f"\n\n🔁 Run {i+1}...")
        
        # Build content
        content = types.Content(
            role='user',
            parts=[types.Part(text=query)]
        )

        # Run agent in thread - this will trigger A2A communication
        print("🚀 Starting agent execution (in thread)...")
        full_response = ""
        function_calls_detected = 0
        all_events = []

        # Run in thread
        all_events = await asyncio.to_thread(run_agent_sync, content)

        # Process events
        for event in all_events:
            # print(f"DEBUG: Event type: {type(event)}")
            
            # Track text response
            if hasattr(event, 'content') and event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        full_response += part.text
                        print(part.text, end='', flush=True)
                    # Count function calls (A2A sub-agent invocations)
                    elif hasattr(part, 'function_call') and part.function_call:
                        function_calls_detected += 1
                        print(f"\n[🔄 Calling sub-agent: {part.function_call.name}]", flush=True)
        
        print(f"\n✅ Run {i+1} completed.")

    print()
    print()
    print("-" * 80)
    print()

    # Verify A2A protocol was used
    print("📊 A2A Protocol Verification:")
    print()

    # Check for function calls (sub-agent invocations)
    if function_calls_detected >= 2:
        print(f"✅ Sub-agent invocations detected: {function_calls_detected} function calls")
        print("   Expected: market_analyst_a2a and agronomist_a2a")
    elif function_calls_detected == 1:
        print(f"⚠️  Only 1 sub-agent invocation detected (expected 2)")
    else:
        print(f"❌ No sub-agent invocations detected")

    print()

    # Check for keywords indicating sub-agent consultation
    response_lower = full_response.lower()

    market_keywords = ['market', 'financial', 'roi', 'profit', 'revenue']
    agro_keywords = ['growing', 'agronomist', 'soil', 'season', 'water']

    market_found = any(kw in response_lower for kw in market_keywords)
    agro_found = any(kw in response_lower for kw in agro_keywords)

    if market_found:
        print("✅ Market analysis content detected in response")
        print(f"   Keywords found: {[kw for kw in market_keywords if kw in response_lower][:3]}")
    else:
        print("⚠️  Market analysis content not detected")

    if agro_found:
        print("✅ Agronomic analysis content detected in response")
        print(f"   Keywords found: {[kw for kw in agro_keywords if kw in response_lower][:3]}")
    else:
        print("⚠️  Agronomic analysis content not detected")

    print()

    # Check for synthesis/recommendation
    recommendation_keywords = ['recommend', 'verdict', 'choose', 'better', 'suggest']
    has_recommendation = any(kw in response_lower for kw in recommendation_keywords)

    if has_recommendation:
        print("✅ Final synthesized recommendation provided")
    else:
        print("⚠️  No clear recommendation detected")

    print()

    if function_calls_detected >= 2 and (market_found or agro_found) and has_recommendation:
        print("=" * 80)
        print("🎉 A2A PROTOCOL SUCCESSFULLY DEMONSTRATED!")
        print("=" * 80)
        print()
        print("The parent agent (Crop Advisor) successfully:")
        print(f"  1. ✅ Invoked {function_calls_detected} sub-agents via A2A protocol")
        print("  2. ✅ Received responses from sub-agents")
        print("  3. ✅ Synthesized both inputs into a comprehensive recommendation")
        print()
        print("This demonstrates true Agent-to-Agent (A2A) communication!")
        print("=" * 80)
    else:
        print("⚠️  A2A protocol verification incomplete")
        print(f"   Sub-agent invocations: {'✅' if function_calls_detected >= 2 else '❌'} ({function_calls_detected})")
        print(f"   Market analysis: {'✅' if market_found else '❌'}")
        print(f"   Agronomic analysis: {'✅' if agro_found else '❌'}")
        print(f"   Final recommendation: {'✅' if has_recommendation else '❌'}")
        print()
        print("=" * 80)

# Main execution
if __name__ == "__main__":
    import asyncio

    try:
        asyncio.run(test_a2a())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
