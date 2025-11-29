"""
Helper script to get Telegram Chat ID for emergency vet group

Usage:
1. Run this script: python get_chat_id.py
2. Send any message in your Telegram group
3. The script will print the Chat ID
4. Copy that Chat ID to your .env file
"""

import os
import sys
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

load_dotenv()

async def show_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display chat ID whenever a message is received"""
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    chat_title = update.effective_chat.title if update.effective_chat.title else "Private Chat"

    print("\n" + "="*60)
    print("✅ CHAT ID FOUND!")
    print("="*60)
    print(f"Chat Title: {chat_title}")
    print(f"Chat Type: {chat_type}")
    print(f"Chat ID: {chat_id}")
    print("="*60)
    print("\nAdd this line to your .env file:")
    print(f"VET_GROUP_CHAT_ID={chat_id}")
    print("="*60 + "\n")

    # Send confirmation back to the chat
    await update.message.reply_text(
        f"✅ Chat ID detected!\n\n"
        f"Chat ID: `{chat_id}`\n"
        f"Chat Type: {chat_type}\n\n"
        f"Add this to your .env file:\n"
        f"`VET_GROUP_CHAT_ID={chat_id}`",
        parse_mode='Markdown'
    )

def main():
    """Run the chat ID detector"""
    emergency_token = os.getenv('TELEGRAM_TOKEN_EMERGENCY_BOT')

    if not emergency_token:
        print("❌ ERROR: TELEGRAM_TOKEN_EMERGENCY_BOT not found in .env file!")
        sys.exit(1)

    print("="*60)
    print("🔍 CHAT ID DETECTOR")
    print("="*60)
    print("Waiting for messages...")
    print("\nInstructions:")
    print("1. Add this bot to your Telegram group (if not already added)")
    print("2. Send ANY message in the group")
    print("3. The Chat ID will be displayed here")
    print("4. Copy it to your .env file")
    print("="*60 + "\n")

    # Create application
    application = Application.builder().token(emergency_token).build()

    # Add handler for all message types
    application.add_handler(MessageHandler(filters.ALL, show_chat_id))

    # Run the bot
    print("🤖 Bot is running... Send a message in your group!\n")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
