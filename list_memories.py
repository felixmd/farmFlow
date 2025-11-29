"""
List all memories in Vertex AI Memory Bank to verify they exist
"""

import os
from dotenv import load_dotenv
import vertexai

load_dotenv()

PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
AGENT_ENGINE_ID = os.getenv("AGENT_ENGINE_ID")

os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"

print("=" * 70)
print("🔍 LISTING MEMORIES IN AGENT ENGINE")
print("=" * 70)
print(f"Project: {PROJECT}")
print(f"Agent Engine ID: {AGENT_ENGINE_ID}")
print()

# Initialize client
client = vertexai.Client(project=PROJECT, location=LOCATION)
agent_engine_name = f"projects/{PROJECT}/locations/{LOCATION}/reasoningEngines/{AGENT_ENGINE_ID}"

try:
    print("📡 Fetching memories...")

    # List memories (API doesn't support scope filtering in list())
    memories = client.agent_engines.memories.list(
        name=agent_engine_name
    )

    memory_list = list(memories)

    print(f"\n✅ Found {len(memory_list)} memories")
    print()

    if memory_list:
        for i, memory in enumerate(memory_list, 1):
            print(f"Memory {i}:")
            print(f"  Name: {memory.name}")
            print(f"  Create Time: {memory.create_time}")
            print(f"  Update Time: {memory.update_time}")
            if hasattr(memory, 'display_name'):
                print(f"  Display Name: {memory.display_name}")
            print()
    else:
        print("⚠️  No memories found!")
        print()
        print("This means memories were never created or the scope doesn't match.")
        print()
        print("To fix:")
        print("1. Run: python load_pesticide_knowledge.py")
        print("2. Wait 2-5 minutes for indexing")
        print("3. Retry this script")

except Exception as e:
    print(f"❌ Error listing memories: {e}")
    import traceback
    traceback.print_exc()

print("=" * 70)
