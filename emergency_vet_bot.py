"""
Emergency Veterinary Bot

This bot posts livestock emergency cases to the "Livestock Emergency" Telegram group
where expert veterinarians can review cases and provide guidance.

Vets can respond by:
1. Replying to the case message
2. Using /respond [case_id] [advice] command
"""

import os
import sys
import logging
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler
)
from telegram.constants import ChatAction, ParseMode

from emergency_case_manager import get_case_manager

# Load environment variables
load_dotenv()

# Configure logging
log_file = Path(__file__).parent / "emergency_vet_bot.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EmergencyVetBot:
    """Telegram bot for posting to vet emergency group"""

    def __init__(self):
        self.telegram_token = os.getenv('TELEGRAM_TOKEN_EMERGENCY_BOT')
        if not self.telegram_token:
            raise ValueError("TELEGRAM_TOKEN_EMERGENCY_BOT not found in environment")

        self.case_manager = get_case_manager()
        self.application = None

        logger.info("Emergency Vet Bot initialized")

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome = """
🩺 **Livestock Emergency Vet Bot**

This bot posts critical livestock cases that require expert veterinary review.

**How to respond to a case:**
1. **Reply** to the case message with your diagnosis/advice
2. **Use command:** `/respond [case_id] [your advice]`

**Available Commands:**
/start - Show this message
/stats - Show case statistics
/active - Show active cases
"""
        await update.message.reply_text(welcome, parse_mode=ParseMode.MARKDOWN)

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show case statistics"""
        stats = self.case_manager.get_stats()

        message = f"""
📊 **Emergency Case Statistics**

**Total Cases:** {stats['total_cases']}
**Active Cases:** {stats['active_cases']}

**By Status:**
"""
        for status, count in stats['by_status'].items():
            message += f"- {status}: {count}\n"

        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

    async def active_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show active cases"""
        active_cases = self.case_manager.get_active_cases()

        if not active_cases:
            await update.message.reply_text("✅ No active cases at the moment.")
            return

        message = "🚨 **Active Emergency Cases:**\n\n"
        for case in active_cases:
            message += f"**Case #{case['case_id']}**\n"
            message += f"Disease: {case['detected_disease']}\n"
            message += f"Severity: {case['severity']}\n"
            message += f"Status: {case['status']}\n"
            message += f"Created: {case['created_at'][:19]}\n"
            message += "---\n"

        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

    async def handle_any_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Unified handler for all text messages.
        Handles:
        1. Replies to case messages
        2. Messages containing Case IDs
        3. Messages that look like advice (provides help)
        """
        try:
            user = update.effective_user
            text = update.message.text or update.message.caption or ""
            logger.info(f"Received message from {user.first_name}: {text[:50]}...")

            case_id = None
            
            # 1. Check if it's a reply
            if update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id:
                original_text = update.message.reply_to_message.text or update.message.reply_to_message.caption or ""
                if "Case #" in original_text:
                    try:
                        case_id_line = [line for line in original_text.split('\n') if 'Case #' in line][0]
                        case_id = case_id_line.split('#')[1].split()[0].replace('*', '').strip()
                        logger.info(f"Extracted Case ID {case_id} from reply context")
                    except Exception:
                        logger.warning("Failed to extract Case ID from reply")

            # 2. If not a reply (or failed to extract), check if text contains Case ID
            if not case_id:
                import re
                # Look for 8-char hex string that matches a known case
                # We can check against active cases to be sure
                active_cases = self.case_manager.get_active_cases()
                for case in active_cases:
                    if case['case_id'] in text.upper():
                        case_id = case['case_id']
                        logger.info(f"Found Case ID {case_id} in message text")
                        break

            # 3. Process if we have a Case ID
            if case_id:
                case = self.case_manager.get_case(case_id)
                if case:
                    self.case_manager.mark_vet_response(
                        case_id=case_id,
                        vet_response=text,
                        vet_name=user.full_name,
                        vet_user_id=str(user.id)
                    )
                    await update.message.reply_text(
                        f"✅ Thank you Dr. {user.full_name}! Response for Case #{case_id} recorded."
                    )
                    return
                else:
                    await update.message.reply_text(f"⚠️ Case #{case_id} not found.")
                    return

            # 4. If no Case ID, check if it looks like medical advice and prompt user
            medical_keywords = ['treatment', 'diagnosis', 'symptoms', 'medicine', 'dose', 'injection', 'isolate', 'fmd', 'vaccine']
            if any(keyword in text.lower() for keyword in medical_keywords):
                await update.message.reply_text(
                    "⚠️ **I see you're providing advice, but I don't know which case this is for.**\n\n"
                    "Please either:\n"
                    "1. **Reply** directly to the Case message ↩️\n"
                    "2. Include the **Case ID** in your message (e.g., 'Case #1234ABCD ...')\n"
                    "3. Use the command: `/respond [case_id] [advice]`",
                    parse_mode=ParseMode.MARKDOWN
                )
                logger.info("Sent help prompt to user providing advice without context")
                return

            logger.info("Ignored message: No context found")

        except Exception as e:
            logger.error(f"Error in handle_any_message: {e}", exc_info=True)

    async def respond_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /respond command: /respond [case_id] [advice]"""
        if len(context.args) < 2:
            await update.message.reply_text(
                "Usage: `/respond [case_id] [your diagnosis/advice]`\n\n"
                "Example: `/respond ABC123 This is FMD. Start treatment with...`",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        case_id = context.args[0].upper()
        vet_response = ' '.join(context.args[1:])

        case = self.case_manager.get_case(case_id)
        if not case:
            await update.message.reply_text(f"⚠️ Case #{case_id} not found.")
            return

        # Get vet info
        vet_name = update.message.from_user.full_name
        vet_user_id = str(update.message.from_user.id)

        # Update case
        self.case_manager.mark_vet_response(
            case_id=case_id,
            vet_response=vet_response,
            vet_name=vet_name,
            vet_user_id=vet_user_id
        )

        await update.message.reply_text(
            f"✅ Thank you Dr. {vet_name}! Your response for case #{case_id} has been recorded.\n"
            f"The farmer will be notified shortly."
        )

        logger.info(f"[VetBot] Vet {vet_name} responded to case {case_id} via command")

    async def post_emergency_case(
        self,
        chat_id: str,
        case_id: str,
        case_data: dict,
        image_file_id: Optional[str] = None
    ) -> Optional[int]:
        """
        Post an emergency case to the vet group

        Args:
            chat_id: Telegram chat ID of the vet group
            case_id: Case identifier
            case_data: Case information dict
            image_file_id: Telegram file ID of the image

        Returns:
            message_id: ID of the posted message, or None if failed
        """
        try:
            # Build message
            message = f"""
🚨 **LIVESTOCK EMERGENCY CASE**

**Case #{case_data['case_id']}**

**Disease Detected:** {case_data['detected_disease']}
**Severity:** {case_data['severity']}
**Farmer:** {case_data['farmer_name']} (ID: {case_data['farmer_user_id']})

**Query:** {case_data['query']}

**Created:** {case_data['created_at'][:19]}

---
**Instructions for Vets:**
- Reply to this message with your diagnosis/treatment advice
- Or use: `/respond {case_data['case_id']} [your advice]`

The farmer will receive your guidance immediately.
"""

            # Send with image if available
            if image_file_id:
                sent_message = await self.application.bot.send_photo(
                    chat_id=chat_id,
                    photo=image_file_id,
                    caption=message,
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                sent_message = await self.application.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode=ParseMode.MARKDOWN
                )

            logger.info(f"[VetBot] Posted case {case_id} to vet group (msg_id: {sent_message.message_id})")
            return sent_message.message_id

        except Exception as e:
            logger.error(f"[VetBot] Failed to post case {case_id}: {e}", exc_info=True)
            return None

    def run(self):
        """Run the emergency vet bot"""
        # Create application
        self.application = Application.builder().token(self.telegram_token).build()

        # Add handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("active", self.active_command))
        self.application.add_handler(CommandHandler("respond", self.respond_command))

        # Handle replies to bot messages
        # Handle all text messages (replies, mentions, or just text)
        self.application.add_handler(
            MessageHandler(filters.TEXT & (~filters.COMMAND), self.handle_any_message)
        )

        # Start bot
        logger.info("Starting Emergency Vet Bot...")
        logger.info("Ready to post emergency cases to vet group!")

        # Run polling
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

def main():
    """Main entry point"""
    bot = EmergencyVetBot()
    bot.run()

if __name__ == "__main__":
    main()
