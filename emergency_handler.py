"""
Emergency Handler for Livestock Cases

Detects emergency markers in livestock specialist responses
and coordinates posting to vet group.
"""

import logging
import re
import os
from typing import Optional, Tuple, Dict
from dotenv import load_dotenv
from telegram import Bot
from telegram.error import ChatMigrated

from emergency_case_manager import get_case_manager

load_dotenv()

logger = logging.getLogger(__name__)

class EmergencyHandler:
    """Handles emergency livestock cases requiring vet review"""

    def __init__(self, vet_group_chat_id: str):
        """
        Initialize emergency handler

        Args:
            vet_group_chat_id: Telegram chat ID of the vet emergency group
        """
        self.vet_group_chat_id = vet_group_chat_id
        self.case_manager = get_case_manager()

        # Initialize emergency bot
        emergency_token = os.getenv('TELEGRAM_TOKEN_EMERGENCY_BOT')
        if not emergency_token:
            raise ValueError("TELEGRAM_TOKEN_EMERGENCY_BOT not found in environment")

        self.emergency_bot = Bot(token=emergency_token)
        logger.info(f"[EmergencyHandler] Initialized with vet group: {vet_group_chat_id}")

    def detect_emergency(self, specialist_response: str) -> Tuple[bool, Optional[Dict]]:
        """
        Detect if specialist response contains emergency marker

        Args:
            specialist_response: Response from livestock specialist

        Returns:
            Tuple of (is_emergency, emergency_data_dict or None)
        """
        if "[EMERGENCY_VET_REVIEW_REQUIRED]" not in specialist_response:
            return False, None

        # Extract emergency block
        try:
            emergency_block = re.search(
                r'\[EMERGENCY_VET_REVIEW_REQUIRED\](.*?)\[END_EMERGENCY\]',
                specialist_response,
                re.DOTALL
            )

            if not emergency_block:
                logger.warning("[EmergencyHandler] Emergency marker found but couldn't parse block")
                return False, None

            block_content = emergency_block.group(1)

            # Parse fields
            disease_match = re.search(r'DISEASE:\s*(.+)', block_content)
            severity_match = re.search(r'SEVERITY:\s*(\w+)', block_content)
            confidence_match = re.search(r'CONFIDENCE:\s*(\w+)', block_content)
            reasoning_match = re.search(r'REASONING:\s*(.+)', block_content)

            emergency_data = {
                "disease": disease_match.group(1).strip() if disease_match else "Unknown",
                "severity": severity_match.group(1).strip() if severity_match else "HIGH",
                "confidence": confidence_match.group(1).strip() if confidence_match else "UNKNOWN",
                "reasoning": reasoning_match.group(1).strip() if reasoning_match else "Critical condition detected"
            }

            logger.info(f"[EmergencyHandler] Emergency detected: {emergency_data['disease']} ({emergency_data['severity']})")
            return True, emergency_data

        except Exception as e:
            logger.error(f"[EmergencyHandler] Failed to parse emergency block: {e}", exc_info=True)
            return False, None

    def extract_farmer_instructions(self, specialist_response: str) -> str:
        """
        Extract the farmer-facing part of the response (after emergency block)

        Args:
            specialist_response: Full response from specialist

        Returns:
            The part of response to show to farmer
        """
        # Find the end of emergency block
        end_marker = "[END_EMERGENCY]"
        if end_marker in specialist_response:
            # Return everything after the emergency block
            return specialist_response.split(end_marker, 1)[1].strip()
        else:
            # Fallback: return original response
            return specialist_response

    async def create_and_post_emergency_case(
        self,
        farmer_user_id: str,
        farmer_name: str,
        session_id: str,
        query: str,
        emergency_data: Dict,
        image_file_id: Optional[str] = None,
        main_bot: Optional[Bot] = None
    ) -> Tuple[str, bool]:
        """
        Create emergency case and post to vet group

        Args:
            farmer_user_id: Telegram user ID of farmer
            farmer_name: Farmer's name
            session_id: ADK session ID
            query: Original farmer query
            emergency_data: Parsed emergency data (disease, severity, etc.)
            image_file_id: Telegram file ID of the livestock image (from main bot)
            main_bot: Main bot instance (needed to download the photo)

        Returns:
            Tuple of (case_id, success)
        """
        # Create case in manager
        case_id = self.case_manager.create_case(
            farmer_user_id=farmer_user_id,
            farmer_name=farmer_name,
            session_id=session_id,
            query=query,
            detected_disease=emergency_data["disease"],
            severity=emergency_data["severity"],
            image_telegram_file_id=image_file_id
        )

        # Post to vet group
        try:
            case = self.case_manager.get_case(case_id)

            # Build message
            message = f"""
🚨 **LIVESTOCK EMERGENCY CASE**

**Case #{case_id}**

**Disease Detected:** {emergency_data['disease']}
**Severity:** {emergency_data['severity']}
**Confidence:** {emergency_data['confidence']}

**Farmer:** {farmer_name} (ID: {farmer_user_id})
**Query:** {query}

**AI Analysis:**
{emergency_data['reasoning']}

---
**Instructions for Vets:**
Reply to this message with your expert diagnosis and treatment advice.

The farmer will receive your guidance immediately.
"""

            # Send to vet group with retry logic for ChatMigrated
            sent_message = None
            try:
                sent_message = await self._send_to_vet_group(message, image_file_id, main_bot)
            except ChatMigrated as e:
                logger.warning(f"[EmergencyHandler] Chat migrated to {e.new_chat_id}. Updating ID and retrying.")
                self.vet_group_chat_id = str(e.new_chat_id)
                # Retry once with new ID
                sent_message = await self._send_to_vet_group(message, image_file_id, main_bot)

            if sent_message:
                # Update case with vet message ID
                self.case_manager.mark_vet_posted(case_id, sent_message.message_id)
                logger.info(f"[EmergencyHandler] Posted case {case_id} to vet group (msg_id: {sent_message.message_id})")
                return case_id, True
            else:
                return case_id, False

        except Exception as e:
            logger.error(f"[EmergencyHandler] Failed to post case {case_id}: {e}", exc_info=True)
            return case_id, False

    async def _send_to_vet_group(self, message: str, image_file_id: Optional[str], main_bot: Optional[Bot]):
        """Helper to send message to vet group"""
        if image_file_id and main_bot:
            try:
                logger.info(f"[EmergencyHandler] Downloading photo {image_file_id} from main bot")
                file = await main_bot.get_file(image_file_id)
                photo_bytes = await file.download_as_bytearray()
                
                return await self.emergency_bot.send_photo(
                    chat_id=self.vet_group_chat_id,
                    photo=bytes(photo_bytes),
                    caption=message,
                    parse_mode='Markdown'
                )
            except Exception as photo_error:
                logger.warning(f"[EmergencyHandler] Failed to send photo: {photo_error}, sending text only")
                # Fall through to text only
        
        return await self.emergency_bot.send_message(
            chat_id=self.vet_group_chat_id,
            text=message,
            parse_mode='Markdown'
        )

    async def check_for_vet_responses(self):
        """
        Poll for new messages in the vet group (replies to cases)
        """
        try:
            # Get updates for the emergency bot
            # We use a high offset to only get new messages
            updates = await self.emergency_bot.get_updates(
                offset=self.last_update_id + 1 if hasattr(self, 'last_update_id') else None,
                allowed_updates=['message']
            )

            for update in updates:
                # Update offset
                self.last_update_id = update.update_id

                if not update.message or not update.message.reply_to_message:
                    continue

                # Check if it's a reply to one of our cases
                reply_to_id = update.message.reply_to_message.message_id
                
                # Find case associated with this message ID
                case = self.case_manager.get_case_by_vet_message(reply_to_id)
                
                if case and case['status'] == 'awaiting_vet':
                    # It's a reply to a pending case!
                    vet_response = update.message.text
                    vet_name = update.message.from_user.first_name
                    vet_user_id = str(update.message.from_user.id)

                    # Update case status
                    self.case_manager.mark_vet_response(
                        case_id=case['case_id'],
                        vet_response=vet_response,
                        vet_name=vet_name,
                        vet_user_id=vet_user_id
                    )
                    logger.info(f"[EmergencyHandler] Processed vet response for case {case['case_id']}")

        except Exception as e:
            logger.error(f"[EmergencyHandler] Error checking vet responses: {e}")

    def get_pending_farmer_notifications(self):
        """Get cases where vet has responded but farmer hasn't been notified"""
        return self.case_manager.get_pending_farmer_notifications()

    def mark_case_completed(self, case_id: str):
        """Mark case as completed"""
        self.case_manager.mark_completed(case_id)
