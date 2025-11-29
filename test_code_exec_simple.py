"""
Simple test to verify Code Execution Tool works
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
from google.genai import types

# Load environment variables
load_dotenv()

# Set up Vertex AI
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"

async def test():
    session_service = InMemorySessionService()

    runner = Runner(
        agent=market_analyst_agent,
        app_name="test_simple",
        session_service=session_service
    )

    session = await session_service.create_session(
        app_name="test_simple",
        user_id="test_user"
    )

    query = "I have 5 acres. Cotton costs ₹35,000/acre and sells at ₹7,000/quintal. Yield is 8 quintals/acre. Calculate my profit."

    print("=" * 80)
    print("📝 QUERY:")
    print(query)
    print("=" * 80)
    print()
    print("🤖 AGENT RESPONSE:")
    print("-" * 80)

    content = types.Content(
        role='user',
        parts=[types.Part(text=query)]
    )

    # Collect all parts
    response_parts = []
    code_found = False

    for event in runner.run(
        user_id="test_user",
        session_id=session.id,
        new_message=content
    ):
        if hasattr(event, 'content') and event.content and event.content.parts:
            for part in event.content.parts:
                # Check for code execution
                if hasattr(part, 'executable_code') and part.executable_code:
                    code_found = True
                    print("\n💻 CODE EXECUTED:")
                    print(part.executable_code.code)
                    print()

                # Check for code result
                if hasattr(part, 'code_execution_result') and part.code_execution_result:
                    print("✅ CODE RESULT:")
                    print(part.code_execution_result.output)
                    print()

                # Regular text
                if hasattr(part, 'text') and part.text:
                    print(part.text)

    print("-" * 80)
    print()

    if code_found:
        print("✅ CODE EXECUTION TOOL VERIFIED - WORKING PERFECTLY!")
    else:
        print("❌ Code execution not detected")

    print("=" * 80)

if __name__ == "__main__":
    import asyncio
    asyncio.run(test())
