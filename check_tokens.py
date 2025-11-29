
import os
import sys
from dotenv import load_dotenv

load_dotenv()

token1 = os.getenv("TELEGRAM_TOKEN")
token2 = os.getenv("TELEGRAM_TOKEN_EMERGENCY_BOT")

print(f"Token 1 (FarmBot): {token1[:10]}..." if token1 else "Token 1: None")
print(f"Token 2 (Emergency): {token2[:10]}..." if token2 else "Token 2: None")

if token1 and token2 and token1 == token2:
    print("RESULT: SAME")
else:
    print("RESULT: DIFFERENT")
