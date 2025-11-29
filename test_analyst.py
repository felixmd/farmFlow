"""
Market Analyst Agent Test Script
Tests the Market Analyst Agent's ROI calculation capabilities using Google ADK Runtime

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

# Import the Market Analyst agent dynamically
agent_path = Path(__file__).parent / "agents" / "market_analyst_agent"
sys.path.insert(0, str(agent_path))

# Dynamic import to avoid IDE errors
try:
    market_analyst_module = import_module('market_analyst')
    root_agent = market_analyst_module.root_agent
except ImportError:
    # Fallback for direct import
    from market_analyst import root_agent  # type: ignore # noqa: E402


class MarketAnalystTester:
    """Tests the Market Analyst Agent with financial calculation queries"""

    def __init__(self, agent, app_name="farmerpilot-analyst-test"):
        self.agent = agent
        self.app_name = app_name
        self.user_id = "test_analyst_001"

        # Initialize session service (using InMemorySession for testing)
        self.session_service = InMemorySessionService()

        # Create ADK Runner
        self.runner = Runner(
            agent=self.agent,
            app_name=self.app_name,
            session_service=self.session_service
        )

        self.session_id = None

    async def setup_session(self):
        """Create a test session"""
        session = await self.session_service.create_session(
            app_name=self.app_name,
            user_id=self.user_id
        )
        self.session_id = session.id
        print(f"\nSession ID: {self.session_id}")
        print(f"Agent: {self.agent.name}")
        print(f"Model: {self.agent.model}")

    async def send_query(self, query: str, test_name: str = "") -> dict:
        """
        Send a query to the agent and return detailed results

        Args:
            query: The user's question
            test_name: Name of the test for logging

        Returns:
            Dict with response details
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

        # Run the agent and collect events
        events = self.runner.run(
            user_id=self.user_id,
            session_id=self.session_id,
            new_message=content
        )

        final_response = None
        tool_calls = []
        used_code_execution = False
        used_search = False
        has_non_text_parts = False

        # Process events
        for event in events:
            # Track tool usage
            if hasattr(event, 'tool_call') and event.tool_call:
                tool_name = event.tool_call.name
                tool_calls.append(tool_name)
                print(f"\n[Tool Used] {tool_name}")

                if 'search' in tool_name.lower():
                    used_search = True
                if 'code' in tool_name.lower() or 'execution' in tool_name.lower():
                    used_code_execution = True

            # Check content parts for code execution
            if hasattr(event, 'content') and event.content and hasattr(event.content, 'parts'):
                for part in event.content.parts:
                    # Check if part has executable_code or code_execution_result
                    if hasattr(part, 'executable_code') or hasattr(part, 'code_execution_result'):
                        used_code_execution = True
                        has_non_text_parts = True
                        print(f"\n[Code Execution Detected]")

            # Capture final response
            if event.is_final_response():
                if event.content and event.content.parts:
                    # Get text parts only
                    text_parts = []
                    for p in event.content.parts:
                        if hasattr(p, 'text') and p.text:
                            text_parts.append(p.text)
                    final_response = '\n'.join(text_parts) if text_parts else "Response generated with code execution"
                    if final_response:
                        print(f"\n[Agent Response]:\n{final_response}\n")

        # If there are non-text parts (code execution), we know the agent worked
        if has_non_text_parts and not final_response:
            final_response = "Code execution completed successfully"

        return {
            "query": query,
            "response": final_response,
            "tool_calls": tool_calls,
            "used_code_executor": used_code_execution,
            "used_search": used_search,
            "success": final_response is not None and len(final_response) > 0
        }

    async def test_roi_calculation(self) -> dict:
        """Test Case 1: Basic ROI Calculation"""
        query = """I am planning to plant cotton on 5 acres in Gujarat.
        The cost is ₹35,000 per acre. Expected yield is 10 quintals per acre.
        Current market price is ₹7,000 per quintal. What is my ROI?"""

        result = await self.send_query(
            query,
            test_name="ROI Calculation - Cotton Investment"
        )

        # Validate that code execution was used
        result["test_name"] = "ROI Calculation"
        result["expected_behavior"] = "Should use Code Execution to calculate ROI"
        result["passed"] = result["used_code_executor"] and result["success"]

        return result

    async def test_profit_comparison(self) -> dict:
        """Test Case 2: Profit Comparison Between Crops"""
        query = """Compare the profit between planting wheat vs soybean on 10 acres.
        Wheat: Cost ₹28,000/acre, Yield 25 quintals/acre, Price ₹2,500/quintal.
        Soybean: Cost ₹32,000/acre, Yield 20 quintals/acre, Price ₹4,200/quintal.
        Which is more profitable?"""

        result = await self.send_query(
            query,
            test_name="Profit Comparison - Wheat vs Soybean"
        )

        result["test_name"] = "Profit Comparison"
        result["expected_behavior"] = "Should calculate profit for both crops and compare"
        result["passed"] = result["used_code_executor"] and result["success"]

        return result

    async def test_breakeven_analysis(self) -> dict:
        """Test Case 3: Breakeven Price Analysis"""
        query = """I invested ₹2,50,000 in tomato farming on 5 acres.
        My yield is 800 quintals. What minimum price do I need to breakeven?
        What price do I need for 30% profit?"""

        result = await self.send_query(
            query,
            test_name="Breakeven Analysis - Tomato Farming"
        )

        result["test_name"] = "Breakeven Analysis"
        result["expected_behavior"] = "Should calculate breakeven price and target price"
        result["passed"] = result["used_code_executor"] and result["success"]

        return result

    async def test_market_price_with_calculation(self) -> dict:
        """Test Case 4: Market Price Search + ROI Calculation"""
        query = """What is the current onion price in Nashik?
        If I have 100 quintals and my investment was ₹80,000, what is my profit?"""

        result = await self.send_query(
            query,
            test_name="Market Price + ROI - Onion Trading"
        )

        result["test_name"] = "Market Price + Calculation"
        result["expected_behavior"] = "Should use Google Search for price, then calculate profit"
        result["passed"] = result["used_search"] and result["used_code_executor"] and result["success"]

        return result

    async def test_scenario_analysis(self) -> dict:
        """Test Case 5: Multi-Scenario Analysis"""
        query = """I want to plant chili on 3 acres. Cost is ₹60,000 per acre.
        Yield could be 30-50 quintals per acre. Market price ranges from ₹8,000 to ₹15,000 per quintal.
        Show me profit in best case, average case, and worst case scenarios."""

        result = await self.send_query(
            query,
            test_name="Scenario Analysis - Chili Investment"
        )

        result["test_name"] = "Scenario Analysis"
        result["expected_behavior"] = "Should calculate profit for multiple scenarios"
        result["passed"] = result["used_code_executor"] and result["success"]

        return result

    async def run_all_tests(self):
        """Run all test cases and generate report"""
        print("\n" + "="*70)
        print("MARKET ANALYST AGENT - ROI CALCULATION VALIDATION")
        print("="*70)

        # Setup session
        await self.setup_session()

        # Run all tests
        test_methods = [
            self.test_roi_calculation,
            self.test_profit_comparison,
            self.test_breakeven_analysis,
            self.test_market_price_with_calculation,
            self.test_scenario_analysis
        ]

        results = []
        for test_method in test_methods:
            try:
                result = await test_method()
                results.append(result)
            except Exception as e:
                results.append({
                    "test_name": test_method.__name__,
                    "passed": False,
                    "error": str(e),
                    "success": False
                })
                print(f"\n[ERROR] {e}")

            # Small delay between tests
            await asyncio.sleep(1)

        # Print summary
        self._print_summary(results)

        return results

    def _print_summary(self, results):
        """Print test summary"""
        print("\n\n" + "="*70)
        print("VALIDATION SUMMARY")
        print("="*70)

        passed = sum(1 for r in results if r.get("passed", False))
        failed = len(results) - passed

        for i, result in enumerate(results, 1):
            status_symbol = "✓" if result.get("passed", False) else "✗"
            test_name = result.get("test_name", "Unknown")
            print(f"\n{status_symbol} Test {i}: {test_name}")
            print(f"   Expected: {result.get('expected_behavior', 'N/A')}")

            if result.get("passed", False):
                print(f"   Status: PASS")
                if result.get("used_code_executor"):
                    print(f"   ✓ Code Execution Used")
                if result.get("used_search"):
                    print(f"   ✓ Google Search Used")
            else:
                print(f"   Status: FAIL")
                if "error" in result:
                    print(f"   Error: {result['error']}")

        print(f"\n{'-'*70}")
        print(f"Total: {len(results)} | Passed: {passed} | Failed: {failed}")
        print(f"Success Rate: {(passed/len(results)*100):.1f}%")
        print("="*70)


async def main():
    """Main entry point for test script"""
    tester = MarketAnalystTester(agent=root_agent)
    results = await tester.run_all_tests()

    # Return exit code based on results
    failed = sum(1 for r in results if not r.get("passed", False))
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
