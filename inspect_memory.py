"""
Inspect the existing memory to see what was actually stored
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
print("🔍 INSPECTING MEMORY CONTENT")
print("=" * 70)

# Initialize client
client = vertexai.Client(project=PROJECT, location=LOCATION)
agent_engine_name = f"projects/{PROJECT}/locations/{LOCATION}/reasoningEngines/{AGENT_ENGINE_ID}"

try:
    # List memories
    memories = client.agent_engines.memories.list(name=agent_engine_name)
    memory_list = list(memories)

    if not memory_list:
        print("❌ No memories found!")
        exit(1)

    memory = memory_list[0]
    memory_id = memory.name.split("/")[-1]

    print(f"Memory ID: {memory_id}")
    print(f"Created: {memory.create_time}")
    print(f"Updated: {memory.update_time}")
    print()

    # Try to get full memory details
    print("📖 Attempting to retrieve memory content...")

    # Use retrieve API to search for content
    try:
        response = client.agent_engines.memories.retrieve(
            name=agent_engine_name,
            scope={
                "app_name": "FarmBot",
                "user_id": "pesticide_expert"
            },
            similarity_search_params={
                "search_query": "What pesticides are banned?"
            }
        )

        print("✅ Retrieve API succeeded!")
        print()

        # Iterate through results
        results = list(response)
        print(f"Found {len(results)} memory results")
        print()

        for i, result in enumerate(results, 1):
            print(f"Result {i}:")
            print(f"  {result}")
            print()

    except Exception as e:
        print(f"❌ Retrieve failed: {e}")
        import traceback
        traceback.print_exc()

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("=" * 70)
