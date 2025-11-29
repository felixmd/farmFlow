
import asyncio
import os
import logging
import time
from dotenv import load_dotenv
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.plugins.logging_plugin import LoggingPlugin

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the agent
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "agents" / "crop_advisor_agent"))
from crop_advisor import root_agent as crop_advisor_agent

async def main():
    logger.info("Starting A2A Latency Reproduction Test")
    
    app_name = "farmerpilot-telegram"
    session_service = InMemorySessionService()
    
    # Create session
    session = await session_service.create_session(
        app_name=app_name,
        user_id="test_user"
    )
    logger.info(f"Created session: {session.id}")
    
    # Initialize runner
    runner = Runner(
        agent=crop_advisor_agent,
        app_name=app_name,
        session_service=session_service,
        plugins=[LoggingPlugin()]
    )
    
    query = "Should I plant cotton or wheat? Which is more profitable?"
    logger.info(f"Sending query: {query}")
    
    start_time = time.time()
    
    try:        
        event_count = 0
        for event in runner.run(
            user_id="test_user",
            session_id=session.id,
            new_message=query
        ):
            event_count += 1
            if event.is_final_response():
                logger.info("Received final response")
                if event.content and event.content.parts:
                    print("Response:", event.content.parts[0].text)
            
    except Exception as e:
        logger.error(f"Error running agent: {e}", exc_info=True)
        
    end_time = time.time()
    duration = end_time - start_time
    
    logger.info(f"Test completed in {duration:.2f} seconds")
    logger.info(f"Total events processed: {event_count}")

if __name__ == "__main__":
    asyncio.run(main())
