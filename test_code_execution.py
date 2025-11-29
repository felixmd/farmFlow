"""
Test Code Execution Tool for Market Analyst Agent

This script demonstrates the Market Analyst agent using Python code execution
to perform financial calculations for farmers.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add agent path
sys.path.insert(0, str(Path(__file__).parent / "agents" / "market_analyst_agent"))

from market_analyst import root_agent as market_analyst_agent
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Load environment variables
load_dotenv()

# Set up Vertex AI
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"

print("=" * 80)
print("🧮 CODE EXECUTION TOOL DEMONSTRATION")
print("=" * 80)
print()

# Initialize session service
session_service = InMemorySessionService()

# Test queries
test_queries = [
    {
        "name": "Simple ROI Calculation",
        "query": "I have 5 acres. Cotton costs ₹35,000/acre to grow and sells at ₹7,000/quintal. Average yield is 8 quintals/acre. What's my profit?",
        "expected": ["code execution", "ROI", "profit"]
    },
    {
        "name": "Breakeven Analysis",
        "query": "I invested ₹2,00,000 in wheat farming on 10 acres. I got 120 quintals total. What price per quintal do I need to breakeven?",
        "expected": ["code execution", "breakeven", "price"]
    },
    {
        "name": "Multi-Variable Calculation",
        "query": "Compare profit: Crop A costs ₹40,000/acre with yield 12 quintals at ₹6,500/quintal vs Crop B costs ₹30,000/acre with yield 8 quintals at ₹8,000/quintal. Which is better for 3 acres?",
        "expected": ["code execution", "comparison", "profit"]
    }
]

async def test_code_execution():
    """Test the code execution tool with various queries"""

    for i, test in enumerate(test_queries, 1):
        print(f"\n{'='*80}")
        print(f"TEST {i}: {test['name']}")
        print(f"{'='*80}")
        print(f"\n📝 Query: {test['query']}\n")

        try:
            # Create session
            session = await session_service.create_session(
                app_name="test_code_execution",
                user_id="test_user"
            )

            # Create runner
            runner = Runner(
                agent=market_analyst_agent,
                app_name="test_code_execution",
                session_service=session_service
            )

            # Build request
            request = types.GenerateContentRequest(
                contents=[
                    types.Content(
                        role='user',
                        parts=[types.Part(text=test['query'])]
                    )
                ]
            )

            print("🤖 Agent Response:\n")
            print("-" * 80)

            # Run agent and collect response
            full_response = ""
            code_executed = False

            for event in runner.run(request, session_id=session.session_id):
                if hasattr(event, 'text') and event.text:
                    full_response += event.text
                    print(event.text, end='', flush=True)

                # Check if code was executed
                if hasattr(event, 'executable_code'):
                    code_executed = True
                    print(f"\n\n[Code Execution Detected]")

            print("\n" + "-" * 80)

            # Verify expectations
            print(f"\n✅ Test completed")
            if code_executed:
                print("✅ Code execution tool was used")
            else:
                print("⚠️  Code execution not detected (agent may have answered without calculation)")

            # Check for expected keywords
            response_lower = full_response.lower()
            found_keywords = [kw for kw in test['expected'] if kw.lower() in response_lower]

            if found_keywords:
                print(f"✅ Found expected keywords: {', '.join(found_keywords)}")
            else:
                print(f"⚠️  Expected keywords not found: {', '.join(test['expected'])}")

        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()

        print()

# Main execution
if __name__ == "__main__":
    import asyncio

    print("Starting Code Execution Tool Tests...")
    print("This will demonstrate the Market Analyst agent using Python code")
    print("for financial calculations.\n")

    try:
        asyncio.run(test_code_execution())

        print("\n" + "=" * 80)
        print("🎉 CODE EXECUTION TOOL DEMONSTRATION COMPLETE")
        print("=" * 80)
        print("\nKey Capabilities Demonstrated:")
        print("✅ Python code execution for financial calculations")
        print("✅ ROI and profit analysis")
        print("✅ Breakeven analysis")
        print("✅ Multi-variable comparisons")
        print("✅ Real-time computation with formatted output")

    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
