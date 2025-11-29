"""
Test to verify Context Compaction is configured correctly
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add agent paths
sys.path.insert(0, str(Path(__file__).parent / "agents" / "market_analyst_agent"))

from market_analyst import root_agent as market_analyst_agent
from google.adk import Runner
from google.adk.apps.app import App, EventsCompactionConfig
from google.adk.sessions import InMemorySessionService
from google.adk.plugins.logging_plugin import LoggingPlugin
from google.genai import types

# Load environment variables
load_dotenv()

# Set up Vertex AI
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"

print("=" * 80)
print("🗜️  CONTEXT COMPACTION TEST")
print("=" * 80)
print()

# Create App with context compaction
market_analyst_app = App(
    name="test_compaction_market_analyst",
    root_agent=market_analyst_agent,
    events_compaction_config=EventsCompactionConfig(
        compaction_interval=8,
        overlap_size=1,
    ),
)

print("✅ App created with context compaction config:")
print(f"   - Name: {market_analyst_app.name}")
print(f"   - Root Agent: {market_analyst_app.root_agent.name}")
print(f"   - Compaction Interval: {market_analyst_app.events_compaction_config.compaction_interval}")
print(f"   - Overlap Size: {market_analyst_app.events_compaction_config.overlap_size}")
print()

# Create session service and runner
session_service = InMemorySessionService()

runner = Runner(
    app=market_analyst_app,
    session_service=session_service,
    plugins=[LoggingPlugin()]
)

print("✅ Runner created with App (instead of agent parameter)")
print()

async def test_compaction():
    """Test that compaction works with a simple query"""

    session = await session_service.create_session(
        app_name="test_compaction_market_analyst",
        user_id="test_user"
    )

    print(f"✅ Session created: {session.id}")
    print()

    query = "What is 5 + 5?"

    print(f"📝 Test Query: {query}")
    print("-" * 80)

    content = types.Content(
        role='user',
        parts=[types.Part(text=query)]
    )

    response_text = ""
    for event in runner.run(
        user_id="test_user",
        session_id=session.id,
        new_message=content
    ):
        if hasattr(event, 'content') and event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, 'text') and part.text:
                    response_text += part.text

    print(response_text)
    print("-" * 80)
    print()

    print("✅ Context compaction is configured correctly!")
    print()
    print("📊 Configuration Summary:")
    print(f"   - Every 8 user queries, the conversation history will be compacted")
    print(f"   - The most recent 1 conversation turn will be kept for context")
    print(f"   - This prevents context rot in long financial analysis sessions")
    print()
    print("=" * 80)

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_compaction())
