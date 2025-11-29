"""
FarmerPilot Telegram Bot
Primary user interface for farmers to interact with AI agents

Features:
- Multi-agent routing via Orchestrator
- Session memory per user
- Real-time responses with typing indicators
- Markdown formatting for better readability
"""

import asyncio
import os
import sys
import logging
from pathlib import Path
from importlib import import_module
from typing import Dict
from dotenv import load_dotenv

from telegram import Update, PhotoSize
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from telegram.constants import ChatAction, ParseMode
import httpx
import base64

from google.genai import types, Client
from google.adk import Runner
from google.adk.apps.app import App, EventsCompactionConfig
from google.adk.sessions import InMemorySessionService
from google.adk.plugins.logging_plugin import LoggingPlugin

from emergency_case_manager import get_case_manager
from emergency_handler import EmergencyHandler
from memory_service import get_memory_service, is_memory_available

# Load environment variables
load_dotenv()

# Configure logging - stdout only for Cloud Run
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)
logger.info("Logging initialized (stdout)")

# Import Orchestrator and specialist agents
orchestrator_path = Path(__file__).parent / "agents" / "orchestrator"
sys.path.insert(0, str(orchestrator_path))

try:
    orchestrator_module = import_module('orchestrator')
    orchestrator_agent = orchestrator_module.root_agent
    route_query = orchestrator_module.route_query
except ImportError:
    from orchestrator import root_agent as orchestrator_agent, route_query  # type: ignore

# Import specialist agents
agronomist_path = Path(__file__).parent / "agents" / "agronomist_agent"
sys.path.insert(0, str(agronomist_path))
try:
    agronomist_module = import_module('agronomist')
    agronomist_agent = agronomist_module.root_agent
except ImportError:
    from agronomist import root_agent as agronomist_agent  # type: ignore

market_analyst_path = Path(__file__).parent / "agents" / "market_analyst_agent"
sys.path.insert(0, str(market_analyst_path))
try:
    market_analyst_module = import_module('market_analyst')
    market_analyst_agent = market_analyst_module.root_agent
except ImportError:
    from market_analyst import root_agent as market_analyst_agent  # type: ignore

livestock_path = Path(__file__).parent / "agents" / "livestock_agent"
sys.path.insert(0, str(livestock_path))
try:
    livestock_module = import_module('livestock')
    livestock_agent = livestock_module.root_agent
except ImportError:
    from livestock import root_agent as livestock_agent  # type: ignore

crop_advisor_path = Path(__file__).parent / "agents" / "crop_advisor_agent"
sys.path.insert(0, str(crop_advisor_path))
try:
    crop_advisor_module = import_module('crop_advisor')
    crop_advisor_agent = crop_advisor_module.root_agent
except ImportError:
    from crop_advisor import root_agent as crop_advisor_agent  # type: ignore


class FarmerPilotBot:
    """Main bot class handling Telegram interactions and agent routing"""

    def __init__(self, telegram_token: str):
        self.telegram_token = telegram_token
        self.app_name = "agents"

        # Initialize session service for maintaining chat history
        self.session_service = InMemorySessionService()

        # Dictionary to store user sessions {user_id: session_id}
        self.user_sessions: Dict[str, str] = {}

        # Initialize Memory Bank service for pesticide knowledge (before runners)
        self.memory_service = get_memory_service()
        if self.memory_service:
            logger.info("[MemoryService] Memory Bank initialized - pesticide safety knowledge available")
        else:
            logger.warning("[MemoryService] Memory Bank not available - agents will run without persistent memory")

        # Initialize orchestrator runner
        self.orchestrator_runner = Runner(
            agent=orchestrator_agent,
            app_name=self.app_name,
            session_service=self.session_service,
            plugins=[LoggingPlugin()]
        )

        # Initialize specialist runners (persistent, reused across queries)
        # Agronomist gets memory service for pesticide knowledge
        agronomist_runner_config = {
            "agent": agronomist_agent,
            "app_name": self.app_name,
            "session_service": self.session_service,
            "plugins": [LoggingPlugin()]
        }
        if self.memory_service:
            agronomist_runner_config["memory_service"] = self.memory_service
            logger.info("[agronomist] Memory Bank attached to runner")

        self.agronomist_runner = Runner(**agronomist_runner_config)

        # Market Analyst Runner (plain Runner like other agents)
        # Note: Removed App wrapper to ensure session service sharing works correctly
        self.market_analyst_runner = Runner(
            agent=market_analyst_agent,
            app_name=self.app_name,
            session_service=self.session_service,
            plugins=[LoggingPlugin()]
        )
        logger.info("[market_analyst] Runner initialized with shared session service")


        self.livestock_runner = Runner(
            agent=livestock_agent,
            app_name=self.app_name,
            session_service=self.session_service,
            plugins=[LoggingPlugin()]
        )

        self.crop_advisor_runner = Runner(
            agent=crop_advisor_agent,
            app_name=self.app_name,
            session_service=self.session_service,
            plugins=[LoggingPlugin()]
        )

        logger.info("All specialist runners initialized (agronomist, market_analyst, livestock, crop_advisor)")

        # Initialize emergency handler for livestock cases
        vet_group_chat_id = os.getenv('VET_GROUP_CHAT_ID')
        if vet_group_chat_id:
            self.emergency_handler = EmergencyHandler(vet_group_chat_id=vet_group_chat_id)
            logger.info(f"Emergency handler initialized with vet group: {vet_group_chat_id}")
        else:
            self.emergency_handler = None
            logger.warning("VET_GROUP_CHAT_ID not set - emergency vet review disabled")

        logger.info("FarmerPilot Bot initialized")

    async def get_or_create_session(self, user_id: str) -> str:
        """Get existing session or create new one for user"""
        if user_id not in self.user_sessions:
            session = await self.session_service.create_session(
                app_name=self.app_name,
                user_id=user_id
            )
            self.user_sessions[user_id] = session.id
            logger.info(f"Created new session for user {user_id}: {session.id}")

        return self.user_sessions[user_id]

    async def download_image(self, photo: list[PhotoSize]) -> bytes:
        """Download the highest resolution photo from Telegram"""
        # Get the largest photo (last in the list)
        largest_photo = photo[-1]

        # Get file from Telegram
        file = await largest_photo.get_file()

        # Download image bytes
        async with httpx.AsyncClient() as client:
            response = await client.get(file.file_path)
            return response.content

    async def transcribe_voice(self, voice_data: bytes) -> str:
        """Transcribe voice audio using Gemini (runs in thread)"""
        return await asyncio.to_thread(self._transcribe_sync, voice_data)

    def _transcribe_sync(self, voice_data: bytes) -> str:
        """Synchronous helper for transcription with proper client cleanup"""
        with Client(api_key=os.getenv("GOOGLE_API_KEY")) as client:
            prompt = "Transcribe this audio exactly as spoken. Return ONLY the text, no other commentary."
            
            response = client.models.generate_content(
                model='gemini-2.0-flash-exp',
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part(text=prompt),
                            types.Part(inline_data=types.Blob(
                                mime_type='audio/ogg',
                                data=voice_data
                            ))
                        ]
                    )
                ]
            )
            
            return response.text.strip()

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command - welcome message"""
        user = update.effective_user
        user_id = str(user.id)

        # Create session for new user
        await self.get_or_create_session(user_id)

        welcome_message = f"""
🌾 *Namaste {user.first_name}!*

Welcome to *FarmerPilot* - your AI-powered farming assistant! 🤖

I can help you with:
• 🌱 *Crop advice* - diseases, pests, sowing times
• 💰 *Market prices* - current market rates
• 📊 *Financial analysis* - ROI, profit calculations
• 🌦 *Weather impacts* - farming recommendations

*How to use:*
Just send me your farming question in any language, and I'll route it to the right expert!
📷 You can also send photos of your crops for visual diagnosis!

*Examples:*
- "My wheat has yellow rust, what should I do?"
- "What are tomato prices in Maharashtra?"
- "Calculate ROI for 5 acres of cotton at ₹35,000 per acre"
- 📷 Send a photo of diseased leaves for diagnosis

Let's grow together! 🌾
"""

        await update.message.reply_text(
            welcome_message,
            parse_mode=ParseMode.MARKDOWN
        )

        logger.info(f"User {user_id} ({user.first_name}) started the bot")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = """
📚 *FarmerPilot Help*

*Available Commands:*
/start - Start the bot and see welcome message
/help - Show this help message
/clear - Clear your conversation history

*How to ask questions:*
Simply send me your farming question - with text or photos! I'll automatically:
1. Understand your question (and analyze any images)
2. Route it to the right expert agent
3. Get you the best answer

📷 *Image Support:*
- Send a photo of diseased/damaged crops
- Add a caption describing the issue (optional)
- Get AI-powered visual diagnosis!

*Types of questions I can answer:*

🌱 *FarmBot Agronomist*
- Crop diseases and pests
- Sowing times and seasons
- Weather-based advice
- Market price lookups

💰 *FarmBot Market Analyst*
- Profit and ROI calculations
- Cost analysis
- Breakeven pricing
- Crop comparison

Need help? Just ask your question naturally!
"""

        await update.message.reply_text(
            help_message,
            parse_mode=ParseMode.MARKDOWN
        )

    async def clear_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /clear command - clear user session"""
        user_id = str(update.effective_user.id)

        if user_id in self.user_sessions:
            old_session = self.user_sessions[user_id]
            # Create new session
            session = await self.session_service.create_session(
                app_name=self.app_name,
                user_id=user_id
            )
            self.user_sessions[user_id] = session.id

            logger.info(f"Cleared session for user {user_id}: {old_session} -> {session.id}")

            await update.message.reply_text(
                "✅ Your conversation history has been cleared. Starting fresh!"
            )
        else:
            await update.message.reply_text(
                "No active session found. Send me a message to start!"
            )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming user messages (text and images)"""
        user = update.effective_user
        user_id = str(user.id)

        # Check if message has photo
        has_photo = update.message.photo is not None and len(update.message.photo) > 0
        user_message = update.message.caption if has_photo else update.message.text

        # Default message if only photo without caption
        if has_photo and not user_message:
            user_message = "What's wrong with this crop? Can you help diagnose the issue?"

        logger.info(f"Received from {user_id} ({user.first_name}): {user_message} [Photo: {has_photo}]")

        # Show typing indicator
        await update.message.chat.send_action(ChatAction.TYPING)

        try:
            # Get or create session
            logger.info(f"[STEP 1/5] Getting/creating session for user {user_id}")
            session_id = await self.get_or_create_session(user_id)
            logger.info(f"[STEP 1/5] ✓ Session ID: {session_id}")

            # Download image if present
            image_data = None
            if has_photo:
                logger.info(f"[STEP 2/5] Downloading image from user {user_id}")
                try:
                    image_data = await self.download_image(update.message.photo)
                    logger.info(f"[STEP 2/5] ✓ Image downloaded: {len(image_data)} bytes")
                except Exception as img_error:
                    logger.error(f"[STEP 2/5] ✗ Image download failed: {img_error}", exc_info=True)
                    await update.message.reply_text(
                        "⚠️ Failed to download image. Please try sending it again."
                    )
                    return
            else:
                logger.info(f"[STEP 2/5] No image attached")

            # Handle Voice Messages
            if update.message.voice:
                logger.info(f"[STEP 2.5/5] Processing voice message")
                try:
                    # Download voice file
                    voice_file = await update.message.voice.get_file()
                    voice_data = None
                    async with httpx.AsyncClient() as client:
                        response = await client.get(voice_file.file_path)
                        voice_data = response.content
                    
                    # Transcribe
                    transcribed_text = await self.transcribe_voice(voice_data)
                    logger.info(f"[STEP 2.5/5] ✓ Transcribed: '{transcribed_text}'")
                    
                    # Update user_message with transcription
                    user_message = transcribed_text
                    
                    # Notify user what we heard
                    await update.message.reply_text(f"🎤 I heard: \"{user_message}\"")
                    
                except Exception as voice_error:
                    logger.error(f"Voice processing failed: {voice_error}", exc_info=True)
                    await update.message.reply_text("⚠️ Sorry, I couldn't understand that voice message.")
                    return

            if not user_message:
                logger.warning("No text or voice content found")
                await update.message.reply_text("Please send text, a photo, or a voice message.")
                return

            # Step 1: Send to Orchestrator for routing
            logger.info(f"[STEP 3/5] Querying orchestrator for routing decision")
            logger.info(f"[STEP 3/5] Query text: {user_message[:100]}{'...' if len(user_message) > 100 else ''}")

            try:
                orchestrator_response = await self.query_orchestrator(
                    user_message,
                    user_id,
                    session_id,
                    image_data
                )
                logger.info(f"[STEP 3/5] ✓ Orchestrator response received")
            except Exception as orch_error:
                logger.error(f"[STEP 3/5] ✗ Orchestrator query failed: {orch_error}", exc_info=True)
                await update.message.reply_text(
                    f"⚠️ Routing error: {str(orch_error)[:100]}. Please try again."
                )
                return

            if not orchestrator_response:
                logger.error(f"[STEP 3/5] ✗ Empty orchestrator response")
                await update.message.reply_text(
                    "⚠️ Sorry, I couldn't process your request. Please try again."
                )
                return

            # Step 2: Parse routing decision
            logger.info(f"[STEP 4/5] Parsing routing decision")
            try:
                query_type, reason, target_agent = route_query(user_message, orchestrator_response)
                logger.info(f"[STEP 4/5] ✓ Route: {query_type} -> {target_agent.name if target_agent else 'orchestrator'}")
                logger.info(f"[STEP 4/5] Reason: {reason[:100]}{'...' if len(reason) > 100 else ''}")
            except Exception as route_error:
                logger.error(f"[STEP 4/5] ✗ Routing parse failed: {route_error}", exc_info=True)
                await update.message.reply_text(
                    f"⚠️ Routing parse error: {str(route_error)[:100]}"
                )
                return

            # Step 3: Handle based on routing
            logger.info(f"[STEP 5/5] Executing routing decision: {query_type}")

            if query_type == "GENERAL_CHAT":
                # Orchestrator handled it directly
                logger.info(f"[STEP 5/5] ✓ Responding with general chat")
                await update.message.reply_text(reason)
                logger.info(f"[STEP 5/5] ✓ Message sent successfully")

            elif target_agent:
                # Route to specialist agent
                logger.info(f"[STEP 5/5] Routing to specialist: {target_agent.name}")
                await update.message.chat.send_action(ChatAction.TYPING)

                try:
                    specialist_response = await self.query_specialist(
                        user_message,
                        user_id,
                        session_id,
                        target_agent,
                        image_data
                    )
                    logger.info(f"[STEP 5/5] ✓ Specialist response received ({len(specialist_response) if specialist_response else 0} chars)")
                except Exception as spec_error:
                    logger.error(f"[STEP 5/5] ✗ Specialist query failed: {spec_error}", exc_info=True)
                    await update.message.reply_text(
                        f"⚠️ {target_agent.name} error: {str(spec_error)[:100]}. Please try again."
                    )
                    return

                # Check for livestock emergency requiring vet review
                if specialist_response and target_agent.name == "livestock_specialist" and self.emergency_handler:
                    is_emergency, emergency_data = self.emergency_handler.detect_emergency(specialist_response)

                    if is_emergency and emergency_data:
                        logger.info(f"[EMERGENCY] Livestock emergency detected: {emergency_data['disease']}")

                        # Create and post emergency case
                        case_id, success = await self.emergency_handler.create_and_post_emergency_case(
                            farmer_user_id=user_id,
                            farmer_name=user.first_name,
                            session_id=session_id,
                            query=user_message,
                            emergency_data=emergency_data,
                            image_file_id=update.message.photo[-1].file_id if has_photo else None,
                            main_bot=context.bot
                        )

                        if success:
                            # Extract farmer-facing instructions
                            farmer_message = self.emergency_handler.extract_farmer_instructions(specialist_response)

                            # Notify farmer
                            emergency_notice = f"""
🚨 **URGENT: Serious Condition Detected**

**Case ID:** #{case_id}
**Suspected Disease:** {emergency_data['disease']}

Your case has been escalated to our expert veterinary team for immediate review. You will receive their guidance within 30 minutes.

{farmer_message}
"""
                            await update.message.reply_text(emergency_notice, parse_mode=ParseMode.MARKDOWN)
                            logger.info(f"[EMERGENCY] Case {case_id} created and farmer notified")
                            return  # Don't send the full specialist response
                        else:
                            logger.error(f"[EMERGENCY] Failed to post case, sending normal response")

                if specialist_response:
                    # Format response with markdown
                    formatted_response = self.format_response(specialist_response, target_agent.name)
                    try:
                        await update.message.reply_text(
                            formatted_response,
                            parse_mode=ParseMode.MARKDOWN
                        )
                        logger.info(f"[STEP 5/5] ✓ Response sent successfully (with markdown)")
                    except Exception as send_error:
                        # Markdown parsing failed - this is common with LLM-generated content
                        logger.warning(f"[STEP 5/5] Markdown parse failed, sending plain text: {send_error}")
                        # Send without markdown formatting
                        await update.message.reply_text(specialist_response)
                        logger.info(f"[STEP 5/5] ✓ Response sent successfully (plain text fallback)")
                else:
                    logger.error(f"[STEP 5/5] ✗ Empty specialist response")
                    await update.message.reply_text(
                        "⚠️ Sorry, I couldn't get a response from the specialist. Please try again."
                    )

            else:
                logger.warning(f"[STEP 5/5] ⚠ Unknown routing result")
                await update.message.reply_text(
                    "⚠️ I'm not sure how to handle that. Could you rephrase your question?"
                )

        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            await update.message.reply_text(
                "⚠️ An error occurred. Please try again later."
            )

    def run_agent_sync(self, runner, user_id, session_id, new_message):
        """Helper to run agent synchronously in a thread"""
        events = []
        try:
            for event in runner.run(
                user_id=user_id,
                session_id=session_id,
                new_message=new_message
            ):
                events.append(event)
        except Exception as e:
            logger.error(f"Error in run_agent_sync: {e}", exc_info=True)
            raise
        return events

    async def query_orchestrator(self, query: str, user_id: str, session_id: str, image_data: bytes = None) -> str:
        """Send query to orchestrator for routing decision"""
        logger.info(f"[Orchestrator] Building request for user {user_id}")

        # Create ephemeral routing session (separate from user's conversation session)
        # This prevents orchestrator events from polluting the specialist's session
        routing_session = await self.session_service.create_session(
            app_name=self.app_name,
            user_id=f"routing_{user_id}"  # Separate user ID for routing
        )
        logger.info(f"[Orchestrator] Created ephemeral routing session: {routing_session.id}")

        parts = []

        # Add image first if present
        if image_data:
            logger.info(f"[Orchestrator] Adding image data ({len(image_data)} bytes)")
            parts.append(types.Part(inline_data=types.Blob(
                mime_type='image/jpeg',
                data=image_data
            )))

        # Add text query
        parts.append(types.Part(text=query))
        logger.info(f"[Orchestrator] Request has {len(parts)} parts")

        content = types.Content(
            role='user',
            parts=parts
        )

        logger.info(f"[Orchestrator] Starting runner.run() for routing session {routing_session.id}")
        try:
            # Run in thread to avoid blocking asyncio loop
            events = await asyncio.to_thread(
                self.run_agent_sync,
                self.orchestrator_runner,
                f"routing_{user_id}",
                routing_session.id,
                content
            )
            logger.info(f"[Orchestrator] Runner finished, processing {len(events)} events...")
        except Exception as runner_error:
            logger.error(f"[Orchestrator] Runner.run() failed: {runner_error}", exc_info=True)
            raise

        response_text = None
        event_count = 0
        for event in events:
            event_count += 1
            logger.debug(f"[Orchestrator] Event {event_count}: {type(event).__name__}")

            if event.is_final_response():
                logger.info(f"[Orchestrator] Final response event received")
                if event.content and event.content.parts:
                    text_parts = [p.text for p in event.content.parts if hasattr(p, 'text') and p.text]
                    response_text = '\n'.join(text_parts)
                    logger.info(f"[Orchestrator] Extracted {len(text_parts)} text parts ({len(response_text)} chars)")

        logger.info(f"[Orchestrator] Processed {event_count} events total")
        if not response_text:
            logger.warning(f"[Orchestrator] No response text extracted from {event_count} events")

        return response_text

    async def query_specialist(self, query: str, user_id: str, session_id: str, agent, image_data: bytes = None) -> str:
        """Send query to specialist agent"""
        agent_name = agent.name

        # Use persistent runner (created at bot startup)
        if agent_name == "agronomist":
            specialist_runner = self.agronomist_runner
        elif agent_name == "market_analyst":
            specialist_runner = self.market_analyst_runner
        elif agent_name == "livestock_specialist":
            specialist_runner = self.livestock_runner
        elif agent_name == "crop_investment_advisor":
            specialist_runner = self.crop_advisor_runner
        else:
            logger.error(f"[{agent_name}] Unknown agent name, cannot find runner")
            return f"Error: Unknown agent '{agent_name}'"

        logger.info(f"[{agent_name}] Using persistent runner")
        logger.info(f"[{agent_name}] Building request")
        parts = []

        # Add image first if present
        if image_data:
            logger.info(f"[{agent_name}] Adding image data ({len(image_data)} bytes)")
            parts.append(types.Part(inline_data=types.Blob(
                mime_type='image/jpeg',
                data=image_data
            )))

        # Add text query
        parts.append(types.Part(text=query))
        logger.info(f"[{agent_name}] Request has {len(parts)} parts")

        content = types.Content(
            role='user',
            parts=parts
        )

        logger.info(f"[{agent_name}] Starting runner.run() for session {session_id}")
        try:
            # Run in thread to avoid blocking asyncio loop
            events = await asyncio.to_thread(
                self.run_agent_sync,
                specialist_runner,
                user_id,
                session_id,
                content
            )
            logger.info(f"[{agent_name}] Runner finished, processing {len(events)} events...")
        except Exception as runner_error:
            logger.error(f"[{agent_name}] Runner.run() failed: {runner_error}", exc_info=True)
            raise

        response_text = None
        event_count = 0
        tool_calls = []

        for event in events:
            event_count += 1
            logger.debug(f"[{agent_name}] Event {event_count}: {type(event).__name__}")

            # Track tool calls
            if hasattr(event, 'tool_call') and event.tool_call:
                tool_name = event.tool_call.name if hasattr(event.tool_call, 'name') else 'unknown'
                tool_calls.append(tool_name)
                logger.info(f"[{agent_name}] Tool called: {tool_name}")

            if event.is_final_response():
                logger.info(f"[{agent_name}] Final response event received")
                if event.content and event.content.parts:
                    # Handle code execution parts
                    text_parts = []
                    non_text_parts = []

                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            text_parts.append(part.text)
                        elif hasattr(part, 'executable_code'):
                            non_text_parts.append('code')
                        elif hasattr(part, 'code_execution_result'):
                            non_text_parts.append('code_result')

                    response_text = '\n'.join(text_parts) if text_parts else "Response generated"
                    logger.info(f"[{agent_name}] Extracted {len(text_parts)} text parts, {len(non_text_parts)} non-text parts")
                    logger.info(f"[{agent_name}] Response length: {len(response_text)} chars")

        logger.info(f"[{agent_name}] Processed {event_count} events total")
        logger.info(f"[{agent_name}] Tools used: {tool_calls if tool_calls else 'none'}")

        if not response_text:
            logger.warning(f"[{agent_name}] No response text extracted from {event_count} events")

        return response_text

    def format_response(self, response: str, agent_name: str) -> str:
        """Format agent response with appropriate header"""
        if agent_name == "agronomist":
            header = "🌱 *FarmBot Agronomist says:*\n\n"
        elif agent_name == "market_analyst":
            header = "💰 *FarmBot Market Analyst says:*\n\n"
        else:
            header = "🤖 *FarmerPilot says:*\n\n"

        return header + response

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Update {update} caused error {context.error}", exc_info=context.error)

    async def check_vet_responses(self, context: ContextTypes.DEFAULT_TYPE):
        """
        Background task to check for vet responses and notify farmers
        Runs every 30 seconds
        """
        if not self.emergency_handler:
            return

        try:
            # Poll for new vet responses
            await self.emergency_handler.check_for_vet_responses()

            # Get cases where vet has responded but farmer hasn't been notified
            pending_cases = self.emergency_handler.get_pending_farmer_notifications()

            for case in pending_cases:
                try:
                    farmer_user_id = case['farmer_user_id']
                    case_id = case['case_id']
                    vet_response = case['vet_response']
                    vet_name = case['vet_name']

                    # Send vet's response to farmer
                    notification = f"""
✅ **Expert Veterinary Guidance Received**

**Case ID:** #{case_id}
**Disease:** {case['detected_disease']}
**Expert Vet:** Dr. {vet_name}

**Diagnosis & Treatment Plan:**
{vet_response}

---
_This expert advice was provided by a licensed veterinarian. Follow the instructions carefully and contact your local vet if you have questions._
"""

                    await context.bot.send_message(
                        chat_id=farmer_user_id,
                        text=notification,
                        parse_mode=ParseMode.MARKDOWN
                    )

                    # Mark case as completed
                    self.emergency_handler.mark_case_completed(case_id)
                    logger.info(f"[EMERGENCY] Notified farmer {farmer_user_id} for case {case_id}")

                except Exception as case_error:
                    logger.error(f"[EMERGENCY] Failed to notify farmer for case {case.get('case_id')}: {case_error}", exc_info=True)

        except Exception as e:
            logger.error(f"[EMERGENCY] Error in vet response polling: {e}", exc_info=True)

    def run(self):
        """Run the bot"""
        # Create application
        application = Application.builder().token(self.telegram_token).build()

        # Add handlers
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("clear", self.clear_command))

        # Handle both text messages and photos (with or without captions)
        application.add_handler(MessageHandler((filters.TEXT & ~filters.COMMAND) | filters.PHOTO | filters.VOICE, self.handle_message))

        # Add error handler
        application.add_error_handler(self.error_handler)

        # Schedule background polling for vet responses (every 30 seconds)
        if self.emergency_handler:
            application.job_queue.run_repeating(
                self.check_vet_responses,
                interval=30,
                first=10  # Start after 10 seconds
            )
            logger.info("Emergency vet response polling scheduled (every 30s)")

        # Start bot
        logger.info("Starting FarmerPilot Telegram Bot...")

        mode = os.getenv("MODE", "POLLING").upper()
        
        if mode == "WEBHOOK":
            port = int(os.getenv("PORT", "8080"))
            webhook_url = os.getenv("WEBHOOK_URL")
            if not webhook_url:
                logger.error("WEBHOOK_URL not set for WEBHOOK mode")
                sys.exit(1)
                
            logger.info(f"Starting in WEBHOOK mode on port {port}")
            application.run_webhook(
                listen="0.0.0.0",
                port=port,
                url_path=self.telegram_token,
                webhook_url=f"{webhook_url}/{self.telegram_token}",
                allowed_updates=Update.ALL_TYPES
            )
        else:
            logger.info("Starting in POLLING mode")
            
            # Cloud Run requires a service listening on PORT (default 8080)
            # even for polling bots, otherwise it kills the container.
            # We start a dummy HTTP server to satisfy the health check.
            from http.server import HTTPServer, BaseHTTPRequestHandler
            import threading

            class HealthCheckHandler(BaseHTTPRequestHandler):
                def do_GET(self):
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"OK")
                
                # Suppress log messages
                def log_message(self, format, *args):
                    pass

            def start_health_check_server():
                port = int(os.getenv("PORT", "8080"))
                server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
                logger.info(f"Health check server listening on port {port}")
                server.serve_forever()

            # Start health check server in background thread
            health_thread = threading.Thread(target=start_health_check_server, daemon=True)
            health_thread.start()

            logger.info("Bot is ready to receive messages!")
            application.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    """Main entry point"""
    telegram_token = os.getenv("TELEGRAM_TOKEN")

    if not telegram_token:
        logger.error("TELEGRAM_TOKEN not found in environment variables!")
        logger.error("Please add TELEGRAM_TOKEN to your .env file")
        sys.exit(1)

    bot = FarmerPilotBot(telegram_token)
    bot.run()


if __name__ == "__main__":
    main()
