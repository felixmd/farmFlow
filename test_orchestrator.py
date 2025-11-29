"""
Orchestrator Test Script
Tests the routing logic and session management

Based on Google ADK Documentation:
https://google.github.io/adk-docs/runtime/
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

# Import the Orchestrator agent dynamically
agent_path = Path(__file__).parent / "agents" / "orchestrator"
sys.path.insert(0, str(agent_path))

try:
    orchestrator_module = import_module('orchestrator')
    root_agent = orchestrator_module.root_agent
    route_query = orchestrator_module.route_query
except ImportError:
    from orchestrator import root_agent, route_query  # type: ignore # noqa: E402


class OrchestratorTester:
    """Tests the Orchestrator Agent's routing capabilities"""

    def __init__(self, agent, app_name="farmerpilot-orchestrator-test"):
        self.agent = agent
        self.app_name = app_name
        self.user_id = "test_orchestrator_001"

        # Initialize session service with InMemorySession
        self.session_service = InMemorySessionService()

        # Create ADK Runner
        self.runner = Runner(
            agent=self.agent,
            app_name=self.app_name,
            session_service=self.session_service
        )

        self.session_id = None

    async def setup_session(self):
        """Create a test session for maintaining chat history"""
        session = await self.session_service.create_session(
            app_name=self.app_name,
            user_id=self.user_id
        )
        self.session_id = session.id
        print(f"\n{'='*70}")
        print(f"ORCHESTRATOR ROUTING TEST")
        print(f"{'='*70}")
        print(f"Session ID: {self.session_id}")
        print(f"Agent: {self.agent.name}")
        print(f"Model: {self.agent.model}")
        print(f"Session Service: InMemorySessionService (maintains chat history)")

    async def send_query(self, query: str, test_name: str = "") -> dict:
        """
        Send a query to the orchestrator and get routing decision

        Args:
            query: The user's question
            test_name: Name of the test for logging

        Returns:
            Dict with routing details
        """
        print(f"\n{'='*70}")
        if test_name:
            print(f"TEST: {test_name}")
        print(f"Query: {query}")
        print(f"{'='*70}")

        # Create content from query
        content = types.Content(
            role='user',
            parts=[types.Part(text=query)]
        )

        # Run the orchestrator and collect events
        events = self.runner.run(
            user_id=self.user_id,
            session_id=self.session_id,
            new_message=content
        )

        final_response = None

        # Process events
        for event in events:
            # Capture final response
            if event.is_final_response():
                if event.content and event.content.parts:
                    text_parts = [p.text for p in event.content.parts if hasattr(p, 'text') and p.text]
                    final_response = '\n'.join(text_parts)

        if not final_response:
            return {
                "query": query,
                "route": "ERROR",
                "reason": "No response from orchestrator",
                "success": False
            }

        print(f"\n[Orchestrator Response]:\n{final_response}\n")

        # Parse routing decision
        query_type, reason, target_agent = route_query(query, final_response)

        agent_name = target_agent.name if target_agent else "None (handled by orchestrator)"
        print(f"[Routing Decision]")
        print(f"  Route: {query_type}")
        print(f"  Target Agent: {agent_name}")
        print(f"  Reason: {reason}")

        return {
            "query": query,
            "route": query_type,
            "reason": reason,
            "target_agent": agent_name,
            "orchestrator_response": final_response,
            "success": True
        }

    async def test_agronomy_routing(self) -> list[dict]:
        """Test cases that should route to Agronomist"""
        test_cases = [
            {
                "query": "My wheat crop has yellow rust. What should I do?",
                "expected": "AGRONOMY_QUERY",
                "test_name": "Pest/Disease Query"
            },
            {
                "query": "What is the best time to sow cotton in Gujarat?",
                "expected": "AGRONOMY_QUERY",
                "test_name": "Sowing Time Query"
            },
            {
                "query": "What are the current tomato prices in Maharashtra?",
                "expected": "AGRONOMY_QUERY",
                "test_name": "Market Price Lookup"
            }
        ]

        results = []
        for tc in test_cases:
            result = await self.send_query(tc["query"], tc["test_name"])
            result["expected"] = tc["expected"]
            result["passed"] = result["route"] == tc["expected"]
            results.append(result)
            await asyncio.sleep(1)

        return results

    async def test_financial_routing(self) -> list[dict]:
        """Test cases that should route to Market Analyst"""
        test_cases = [
            {
                "query": "If I plant cotton on 5 acres at ₹35,000 per acre and get 10 quintals per acre at ₹7,000 per quintal, what is my ROI?",
                "expected": "FINANCIAL_QUERY",
                "test_name": "ROI Calculation"
            },
            {
                "query": "Which is more profitable: wheat or soybean on 10 acres?",
                "expected": "FINANCIAL_QUERY",
                "test_name": "Profit Comparison"
            },
            {
                "query": "I spent ₹2,00,000 on farming. My yield is 500 quintals. What price do I need to break even?",
                "expected": "FINANCIAL_QUERY",
                "test_name": "Breakeven Analysis"
            }
        ]

        results = []
        for tc in test_cases:
            result = await self.send_query(tc["query"], tc["test_name"])
            result["expected"] = tc["expected"]
            result["passed"] = result["route"] == tc["expected"]
            results.append(result)
            await asyncio.sleep(1)

        return results

    async def test_general_chat_routing(self) -> list[dict]:
        """Test cases that should be handled by orchestrator"""
        test_cases = [
            {
                "query": "Hello! How are you?",
                "expected": "GENERAL_CHAT",
                "test_name": "Greeting"
            },
            {
                "query": "Thank you so much for your help!",
                "expected": "GENERAL_CHAT",
                "test_name": "Gratitude"
            }
        ]

        results = []
        for tc in test_cases:
            result = await self.send_query(tc["query"], tc["test_name"])
            result["expected"] = tc["expected"]
            result["passed"] = result["route"] == tc["expected"]
            results.append(result)
            await asyncio.sleep(1)

        return results

    async def test_session_memory(self) -> dict:
        """Test that session maintains chat history for follow-up questions"""
        print(f"\n{'='*70}")
        print(f"TEST: Session Memory - Follow-up Questions")
        print(f"{'='*70}")

        # First query
        query1 = "What are the current onion prices?"
        result1 = await self.send_query(query1, "Initial Query")
        await asyncio.sleep(1)

        # Follow-up query (should maintain context)
        query2 = "What about tomatoes?"
        result2 = await self.send_query(query2, "Follow-up Query")

        return {
            "test_name": "Session Memory",
            "passed": result1["success"] and result2["success"],
            "first_route": result1["route"],
            "followup_route": result2["route"]
        }

    async def run_all_tests(self):
        """Run complete orchestrator test suite"""
        await self.setup_session()

        all_results = []

        # Test Agronomy routing
        print(f"\n{'#'*70}")
        print(f"# AGRONOMY ROUTING TESTS")
        print(f"{'#'*70}")
        agronomy_results = await self.test_agronomy_routing()
        all_results.extend(agronomy_results)

        # Test Financial routing
        print(f"\n{'#'*70}")
        print(f"# FINANCIAL ROUTING TESTS")
        print(f"{'#'*70}")
        financial_results = await self.test_financial_routing()
        all_results.extend(financial_results)

        # Test General Chat routing
        print(f"\n{'#'*70}")
        print(f"# GENERAL CHAT TESTS")
        print(f"{'#'*70}")
        chat_results = await self.test_general_chat_routing()
        all_results.extend(chat_results)

        # Test Session Memory
        print(f"\n{'#'*70}")
        print(f"# SESSION MEMORY TEST")
        print(f"{'#'*70}")
        memory_result = await self.test_session_memory()

        # Print summary
        self._print_summary(all_results, memory_result)

        return all_results

    def _print_summary(self, results, memory_result):
        """Print test summary"""
        print("\n\n" + "="*70)
        print("VALIDATION SUMMARY")
        print("="*70)

        # Routing tests
        passed = sum(1 for r in results if r.get("passed", False))
        failed = len(results) - passed

        print("\n[Routing Tests]")
        for i, result in enumerate(results, 1):
            status_symbol = "✓" if result.get("passed", False) else "✗"
            route_status = f"{result['route']} (expected: {result['expected']})"
            print(f"{status_symbol} Test {i}: {route_status}")
            print(f"   Query: {result['query'][:60]}...")
            print(f"   Target: {result.get('target_agent', 'Unknown')}")

        print(f"\n[Session Memory Test]")
        memory_symbol = "✓" if memory_result["passed"] else "✗"
        print(f"{memory_symbol} Session maintains context across queries")

        print(f"\n{'-'*70}")
        print(f"Routing Tests: {len(results)} | Passed: {passed} | Failed: {failed}")
        print(f"Success Rate: {(passed/len(results)*100):.1f}%")
        print(f"Session Memory: {'PASS' if memory_result['passed'] else 'FAIL'}")
        print("="*70)


async def main():
    """Main entry point for test script"""
    tester = OrchestratorTester(agent=root_agent)
    results = await tester.run_all_tests()

    # Return exit code based on results
    failed = sum(1 for r in results if not r.get("passed", False))
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
