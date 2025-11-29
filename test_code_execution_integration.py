"""
Quick test to verify Code Execution Tool works with persistent runners
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add agent paths
sys.path.insert(0, str(Path(__file__).parent / "agents" / "market_analyst_agent"))

from market_analyst import root_agent as market_analyst_agent
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.plugins.logging_plugin import LoggingPlugin
from google.genai import types

# Load environment variables
load_dotenv()

# Set up Vertex AI
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"

print("=" * 80)
print("🧮 CODE EXECUTION INTEGRATION TEST")
print("=" * 80)
print()
print("Testing: Market Analyst Agent with Code Execution + Persistent Runner")
print()

async def test_code_execution():
    """Test code execution with persistent runner"""

    # Create session service
    session_service = InMemorySessionService()

    # Create persistent runner (like in telegram_bot.py)
    market_analyst_runner = Runner(
        agent=market_analyst_agent,
        app_name="test_code_execution",
        session_service=session_service,
        plugins=[LoggingPlugin()]
    )

    print("✅ Persistent runner created")
    print()

    # Create session
    session = await session_service.create_session(
        app_name="test_code_execution",
        user_id="test_user"
    )

    print(f"✅ Session created: {session.id}")
    print()

    # Test query
    query = "I have 5 acres. Cotton costs ₹35,000/acre to grow and sells at ₹7,000/quintal. Average yield is 8 quintals/acre. What's my profit?"

    print(f"📝 Query: {query}")
    print()
    print("-" * 80)
    print("🤖 Agent Response:")
    print("-" * 80)

    # Build content
    content = types.Content(
        role='user',
        parts=[types.Part(text=query)]
    )

    # Run agent
    full_response = ""
    code_executed = False

    for event in market_analyst_runner.run(
        user_id="test_user",
        session_id=session.id,
        new_message=content
    ):
        if hasattr(event, 'text') and event.text:
            full_response += event.text
            print(event.text, end='', flush=True)

        # Check if code was executed
        if hasattr(event, 'executable_code'):
            code_executed = True

    print()
    print("-" * 80)
    print()

    # Verify results
    if code_executed:
        print("✅ CODE EXECUTION DETECTED")
    else:
        print("⚠️  Code execution not detected")

    # Check for expected keywords
    response_lower = full_response.lower()
    keywords = ['profit', 'roi', 'revenue']
    found_keywords = [kw for kw in keywords if kw in response_lower]

    if found_keywords:
        print(f"✅ Found expected keywords: {', '.join(found_keywords)}")
    else:
        print(f"⚠️  Expected keywords not found: {', '.join(keywords)}")

    print()
    print("=" * 80)
    print("✅ TEST COMPLETE")
    print("=" * 80)

# Main execution
if __name__ == "__main__":
    import asyncio

    try:
        asyncio.run(test_code_execution())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
