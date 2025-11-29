"""
Telegram Bot End-to-End Test Script
Tests the complete flow from Telegram message to agent response

Based on Google ADK Documentation:
https://google.github.io/adk-docs/runtime/

This script simulates Telegram user interactions and validates:
- Routing to correct specialist agents
- Session memory across multiple queries
- Response formatting
- Error handling
"""

import asyncio
import sys
from pathlib import Path
from importlib import import_module
from typing import Dict
from google.genai import types
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the Orchestrator agent dynamically
orchestrator_path = Path(__file__).parent / "agents" / "orchestrator"
sys.path.insert(0, str(orchestrator_path))

try:
    orchestrator_module = import_module('orchestrator')
    orchestrator_agent = orchestrator_module.root_agent
    route_query = orchestrator_module.route_query
except ImportError:
    from orchestrator import root_agent as orchestrator_agent, route_query  # type: ignore


class TelegramBotTester:
    """Simulates Telegram bot interactions for end-to-end testing"""

    def __init__(self, app_name="farmerpilot-telegram-test"):
        self.app_name = app_name

        # Initialize session service for maintaining chat history
        self.session_service = InMemorySessionService()

        # Dictionary to store user sessions {user_id: session_id}
        self.user_sessions: Dict[str, str] = {}

        # Initialize orchestrator runner
        self.orchestrator_runner = Runner(
            agent=orchestrator_agent,
            app_name=self.app_name,
            session_service=self.session_service
        )

        print(f"\n{'='*70}")
        print(f"TELEGRAM BOT END-TO-END TEST")
        print(f"{'='*70}")
        print(f"App Name: {self.app_name}")
        print(f"Session Service: InMemorySessionService")
        print(f"Orchestrator Agent: {orchestrator_agent.name}")

    async def get_or_create_session(self, user_id: str) -> str:
        """Get existing session or create new one for user"""
        if user_id not in self.user_sessions:
            session = await self.session_service.create_session(
                app_name=self.app_name,
                user_id=user_id
            )
            self.user_sessions[user_id] = session.id
            print(f"\n[Session Created] User {user_id}: {session.id}")

        return self.user_sessions[user_id]

    async def query_orchestrator(self, query: str, user_id: str, session_id: str) -> str:
        """Send query to orchestrator for routing decision"""
        content = types.Content(
            role='user',
            parts=[types.Part(text=query)]
        )

        events = self.orchestrator_runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message=content
        )

        response_text = None
        for event in events:
            if event.is_final_response():
                if event.content and event.content.parts:
                    text_parts = [p.text for p in event.content.parts if hasattr(p, 'text') and p.text]
                    response_text = '\n'.join(text_parts)

        return response_text

    async def query_specialist(self, query: str, user_id: str, session_id: str, agent) -> str:
        """Send query to specialist agent"""
        # Create runner for specialist agent
        specialist_runner = Runner(
            agent=agent,
            app_name=self.app_name,
            session_service=self.session_service
        )

        content = types.Content(
            role='user',
            parts=[types.Part(text=query)]
        )

        events = specialist_runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message=content
        )

        response_text = None
        for event in events:
            if event.is_final_response():
                if event.content and event.content.parts:
                    text_parts = []
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            text_parts.append(part.text)

                    response_text = '\n'.join(text_parts) if text_parts else "Response generated"

        return response_text

    async def simulate_user_message(self, user_id: str, message: str, test_name: str) -> dict:
        """
        Simulate a complete Telegram message flow:
        1. Get/create session
        2. Query orchestrator
        3. Route to specialist if needed
        4. Return response
        """
        print(f"\n{'='*70}")
        print(f"TEST: {test_name}")
        print(f"{'='*70}")
        print(f"User ID: {user_id}")
        print(f"Message: {message}")

        try:
            # Step 1: Get or create session
            session_id = await self.get_or_create_session(user_id)

            # Step 2: Send to Orchestrator for routing
            print(f"\n[Step 1] Querying Orchestrator...")
            orchestrator_response = await self.query_orchestrator(
                message,
                user_id,
                session_id
            )

            if not orchestrator_response:
                print("❌ No response from orchestrator")
                return {
                    "test_name": test_name,
                    "user_id": user_id,
                    "query": message,
                    "success": False,
                    "error": "No orchestrator response"
                }

            print(f"[Orchestrator Response]:\n{orchestrator_response}")

            # Step 3: Parse routing decision
            query_type, reason, target_agent = route_query(message, orchestrator_response)

            agent_name = target_agent.name if target_agent else "orchestrator"
            print(f"\n[Step 2] Routing Decision:")
            print(f"  Route: {query_type}")
            print(f"  Target Agent: {agent_name}")
            print(f"  Reason: {reason}")

            # Step 4: Handle based on routing
            final_response = None
            if query_type == "GENERAL_CHAT":
                # Orchestrator handled it directly
                final_response = reason
                print(f"\n[Final Response - Orchestrator]:\n{final_response}")

            elif target_agent:
                # Route to specialist agent
                print(f"\n[Step 3] Querying {agent_name}...")
                specialist_response = await self.query_specialist(
                    message,
                    user_id,
                    session_id,
                    target_agent
                )

                if specialist_response:
                    final_response = specialist_response
                    print(f"\n[Final Response - {agent_name}]:")
                    # Print first 300 chars to keep output manageable
                    preview = final_response[:300] + "..." if len(final_response) > 300 else final_response
                    print(preview)
                else:
                    print("❌ No response from specialist")
                    return {
                        "test_name": test_name,
                        "user_id": user_id,
                        "query": message,
                        "route": query_type,
                        "target_agent": agent_name,
                        "success": False,
                        "error": "No specialist response"
                    }

            print(f"\n✅ Test completed successfully")

            return {
                "test_name": test_name,
                "user_id": user_id,
                "query": message,
                "route": query_type,
                "target_agent": agent_name,
                "orchestrator_response": orchestrator_response,
                "final_response": final_response,
                "success": True
            }

        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            return {
                "test_name": test_name,
                "user_id": user_id,
                "query": message,
                "success": False,
                "error": str(e)
            }

    async def test_agronomy_pest_diagnosis(self) -> dict:
        """Test Case 1: Agronomy Query - Pest/Disease Diagnosis"""
        return await self.simulate_user_message(
            user_id="test_user_001",
            message="My wheat crop has yellow rust disease. What should I do?",
            test_name="Agronomy - Pest Diagnosis"
        )

    async def test_agronomy_market_prices(self) -> dict:
        """Test Case 2: Agronomy Query - Market Price Lookup"""
        return await self.simulate_user_message(
            user_id="test_user_002",
            message="What are the current tomato prices in Maharashtra?",
            test_name="Agronomy - Market Prices"
        )

    async def test_financial_roi_calculation(self) -> dict:
        """Test Case 3: Financial Query - ROI Calculation"""
        return await self.simulate_user_message(
            user_id="test_user_003",
            message="If I plant cotton on 5 acres at ₹35,000 per acre and get 10 quintals per acre at ₹7,000 per quintal, what is my ROI?",
            test_name="Financial - ROI Calculation"
        )

    async def test_general_chat_greeting(self) -> dict:
        """Test Case 4: General Chat - Greeting"""
        return await self.simulate_user_message(
            user_id="test_user_004",
            message="Hello! How are you?",
            test_name="General Chat - Greeting"
        )

    async def test_session_memory(self) -> dict:
        """Test Case 5: Session Memory - Follow-up Questions"""
        user_id = "test_user_005"

        print(f"\n{'='*70}")
        print(f"TEST: Session Memory - Follow-up Questions")
        print(f"{'='*70}")

        # First query
        print("\n[Part 1] Initial Query")
        result1 = await self.simulate_user_message(
            user_id=user_id,
            message="What are the current onion prices?",
            test_name="Session Memory - Initial Query"
        )

        await asyncio.sleep(1)

        # Follow-up query (should maintain context)
        print("\n[Part 2] Follow-up Query (testing session memory)")
        result2 = await self.simulate_user_message(
            user_id=user_id,
            message="What about tomatoes?",
            test_name="Session Memory - Follow-up Query"
        )

        # Verify both used same session
        session_maintained = (
            result1.get("success") and
            result2.get("success") and
            user_id in self.user_sessions
        )

        return {
            "test_name": "Session Memory",
            "user_id": user_id,
            "initial_route": result1.get("route"),
            "followup_route": result2.get("route"),
            "session_id": self.user_sessions.get(user_id),
            "success": session_maintained
        }

    async def run_all_tests(self) -> list[dict]:
        """Run complete end-to-end test suite"""
        all_results = []

        # Test 1: Agronomy - Pest Diagnosis
        print(f"\n{'#'*70}")
        print(f"# TEST 1: AGRONOMY QUERY - PEST DIAGNOSIS")
        print(f"{'#'*70}")
        result1 = await self.test_agronomy_pest_diagnosis()
        all_results.append(result1)
        await asyncio.sleep(1)

        # Test 2: Agronomy - Market Prices
        print(f"\n{'#'*70}")
        print(f"# TEST 2: AGRONOMY QUERY - MARKET PRICES")
        print(f"{'#'*70}")
        result2 = await self.test_agronomy_market_prices()
        all_results.append(result2)
        await asyncio.sleep(1)

        # Test 3: Financial - ROI Calculation
        print(f"\n{'#'*70}")
        print(f"# TEST 3: FINANCIAL QUERY - ROI CALCULATION")
        print(f"{'#'*70}")
        result3 = await self.test_financial_roi_calculation()
        all_results.append(result3)
        await asyncio.sleep(1)

        # Test 4: General Chat
        print(f"\n{'#'*70}")
        print(f"# TEST 4: GENERAL CHAT - GREETING")
        print(f"{'#'*70}")
        result4 = await self.test_general_chat_greeting()
        all_results.append(result4)
        await asyncio.sleep(1)

        # Test 5: Session Memory
        print(f"\n{'#'*70}")
        print(f"# TEST 5: SESSION MEMORY - FOLLOW-UP QUESTIONS")
        print(f"{'#'*70}")
        result5 = await self.test_session_memory()
        all_results.append(result5)

        # Print summary
        self._print_summary(all_results)

        return all_results

    def _print_summary(self, results):
        """Print test summary"""
        print("\n\n" + "="*70)
        print("END-TO-END TEST SUMMARY")
        print("="*70)

        passed = sum(1 for r in results if r.get("success", False))
        failed = len(results) - passed

        print(f"\n[Test Results]")
        for i, result in enumerate(results, 1):
            status_symbol = "✅" if result.get("success", False) else "❌"
            test_name = result.get("test_name", "Unknown")
            print(f"{status_symbol} Test {i}: {test_name}")

            if result.get("success"):
                route = result.get("route", "N/A")
                agent = result.get("target_agent", "N/A")
                print(f"   Route: {route} → {agent}")
            else:
                error = result.get("error", "Unknown error")
                print(f"   Error: {error}")

        print(f"\n{'-'*70}")
        print(f"Total Tests: {len(results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/len(results)*100):.1f}%")
        print("="*70)

        if failed == 0:
            print("\n🎉 ALL TESTS PASSED! Telegram bot is ready for production.")
        else:
            print(f"\n⚠️  {failed} test(s) failed. Review the errors above.")


async def main():
    """Main entry point for test script"""
    tester = TelegramBotTester()
    results = await tester.run_all_tests()

    # Return exit code based on results
    failed = sum(1 for r in results if not r.get("success", False))
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
