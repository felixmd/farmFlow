
import os
from dotenv import load_dotenv

load_dotenv()

token1 = os.getenv("TELEGRAM_TOKEN")
token2 = os.getenv("TELEGRAM_TOKEN_EMERGENCY_BOT")
vet_group_id = os.getenv("VET_GROUP_CHAT_ID")

print(f"TELEGRAM_TOKEN exists: {bool(token1)}")
print(f"TELEGRAM_TOKEN_EMERGENCY_BOT exists: {bool(token2)}")
print(f"VET_GROUP_CHAT_ID exists: {bool(vet_group_id)}")

if token1 and token2:
    if token1 == token2:
        print("CRITICAL WARNING: TELEGRAM_TOKEN and TELEGRAM_TOKEN_EMERGENCY_BOT are the SAME!")
    else:
        print("Tokens are different.")
else:
    print("One or both tokens are missing.")

print(f"VET_GROUP_CHAT_ID: {vet_group_id}")
