"""
Agent Validator Script for FarmerPilot
Tests the Agronomist Agent using Google ADK Runtime

Based on Google ADK Documentation:
https://google.github.io/adk-docs/runtime/
https://github.com/google/adk-python
"""

import asyncio
import sys
from pathlib import Path
from importlib import import_module
from google.genai import types
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the Agronomist agent dynamically
agent_path = Path(__file__).parent / "agents" / "agronomist_agent"
sys.path.insert(0, str(agent_path))

# Dynamic import to avoid IDE errors
try:
    agronomist_module = import_module('agronomist')
    root_agent = agronomist_module.root_agent
except ImportError:
    # Fallback for direct import
    from agronomist import root_agent  # type: ignore # noqa: E402


class AgentValidator:
    """Validates the Agronomist Agent with test queries"""

    def __init__(self, agent, app_name="farmerpilot-test"):
        self.agent = agent
        self.app_name = app_name
        self.user_id = "test_user_001"

        # Initialize session service (using InMemorySession for testing)
        self.session_service = InMemorySessionService()

        # Create ADK Runner
        self.runner = Runner(
            agent=self.agent,
            app_name=self.app_name,
            session_service=self.session_service
        )

    async def send_query(self, query: str, session_id: str) -> str:
        """
        Send a query to the agent and return the final response

        Args:
            query: The user's question
            session_id: Session ID for conversation continuity

        Returns:
            The agent's final response text
        """
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")

        # Create content from query
        content = types.Content(
            role='user',
            parts=[types.Part(text=query)]
        )

        # Run the agent and collect events
        events = self.runner.run(
            user_id=self.user_id,
            session_id=session_id,
            new_message=content
        )

        final_response = None

        # Process events
        for event in events:
            # Show tool usage if any
            if hasattr(event, 'tool_call') and event.tool_call:
                print(f"\n[Tool Call] {event.tool_call.name}")

            # Capture final response
            if event.is_final_response():
                if event.content and event.content.parts:
                    final_response = event.content.parts[0].text
                    print(f"\n[Agent Response]:\n{final_response}\n")

        return final_response

    async def run_test_suite(self):
        """Run a suite of test queries to validate the agent"""
        print("\n" + "="*60)
        print("FARMERPILOT AGRONOMIST AGENT VALIDATION")
        print("="*60)

        # Create a test session
        session = await self.session_service.create_session(
            app_name=self.app_name,
            user_id=self.user_id
        )
        session_id = session.id

        print(f"\nSession ID: {session_id}")
        print(f"Agent: {self.agent.name}")
        print(f"Model: {self.agent.model}")

        # Test Case 1: Market Price Query (Should use Google Search)
        test_queries = [
            {
                "query": "What are the current tomato prices in Maharashtra?",
                "expected_behavior": "Should use Google Search tool to find real-time mandi rates"
            },
            {
                "query": "My wheat crop has yellow rust. What should I do? I am in Punjab.",
                "expected_behavior": "Should search for current pest advisories and provide treatment steps"
            },
            {
                "query": "What is the best time to sow cotton in Gujarat?",
                "expected_behavior": "Should provide region-specific sowing advice, possibly with weather search"
            }
        ]

        results = []

        for i, test_case in enumerate(test_queries, 1):
            print(f"\n\n{'*'*60}")
            print(f"TEST CASE {i}/{len(test_queries)}")
            print(f"Expected Behavior: {test_case['expected_behavior']}")
            print(f"{'*'*60}")

            try:
                response = await self.send_query(test_case["query"], session_id)

                # Validate response
                if response:
                    results.append({
                        "test_case": i,
                        "query": test_case["query"],
                        "status": "PASS",
                        "response_length": len(response)
                    })
                else:
                    results.append({
                        "test_case": i,
                        "query": test_case["query"],
                        "status": "FAIL",
                        "error": "No response received"
                    })

            except Exception as e:
                results.append({
                    "test_case": i,
                    "query": test_case["query"],
                    "status": "ERROR",
                    "error": str(e)
                })
                print(f"\n[ERROR] {e}")

            # Small delay between queries
            await asyncio.sleep(1)

        # Print summary
        print("\n\n" + "="*60)
        print("VALIDATION SUMMARY")
        print("="*60)

        passed = sum(1 for r in results if r["status"] == "PASS")
        failed = sum(1 for r in results if r["status"] in ["FAIL", "ERROR"])

        for result in results:
            status_symbol = "✓" if result["status"] == "PASS" else "✗"
            print(f"{status_symbol} Test {result['test_case']}: {result['status']}")
            if result["status"] != "PASS":
                print(f"  Error: {result.get('error', 'Unknown')}")

        print(f"\nTotal: {len(results)} | Passed: {passed} | Failed: {failed}")
        print(f"Success Rate: {(passed/len(results)*100):.1f}%")

        return results


async def main():
    """Main entry point for validation script"""
    validator = AgentValidator(agent=root_agent)
    results = await validator.run_test_suite()

    # Return exit code based on results
    failed = sum(1 for r in results if r["status"] != "PASS")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
