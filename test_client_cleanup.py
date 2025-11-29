
import os
import asyncio
from google.genai import Client, types
from dotenv import load_dotenv

load_dotenv()

async def test_transcribe():
    print("Creating client...")
    client = Client(api_key=os.getenv("GOOGLE_API_KEY"))
    print(f"Has __enter__: {hasattr(client, '__enter__')}")
    print(f"Has __aenter__: {hasattr(client, '__aenter__')}")
    print(f"Has close: {hasattr(client, 'close')}")


    print("Function end. Client should be GC'ed.")

async def main():
    await test_transcribe()
    print("Main end. Sleeping to allow async cleanup...")
    await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())
