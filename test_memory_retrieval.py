"""
Test Memory Retrieval from Vertex AI Memory Bank

This script verifies that pesticide knowledge was loaded correctly
by testing similarity search for key queries.

Usage:
    python test_memory_retrieval.py
"""

import os
import sys
from dotenv import load_dotenv
import vertexai

# Load environment variables
load_dotenv()

PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
AGENT_ENGINE_ID = os.getenv("AGENT_ENGINE_ID")

if not all([PROJECT, LOCATION, AGENT_ENGINE_ID]):
    print("ERROR: Missing required environment variables!")
    sys.exit(1)

os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"

APP_NAME = "FarmBot"
USER_ID = "pesticide_expert"

print("=" * 70)
print("🧪 MEMORY RETRIEVAL TEST")
print("=" * 70)
print(f"Project: {PROJECT}")
print(f"Agent Engine ID: {AGENT_ENGINE_ID}")
print()

# Initialize client
print("📡 Connecting to Vertex AI...")
client = vertexai.Client(project=PROJECT, location=LOCATION)
agent_engine_name = f"projects/{PROJECT}/locations/{LOCATION}/reasoningEngines/{AGENT_ENGINE_ID}"
print("✅ Connected")
print()

# Test queries
test_queries = [
    {
        "query": "Is Imidacloprid safe for export chilli?",
        "expected_keywords": ["banned", "Imidacloprid", "Confidor", "export", "Grade A"]
    },
    {
        "query": "What should I use for Thrips on chilli?",
        "expected_keywords": ["Thrips", "Spinosad", "Neem Oil", "Blue Sticky Traps"]
    },
    {
        "query": "I already sprayed Chlorpyrifos, what now?",
        "expected_keywords": ["Chlorpyrifos", "segregate", "60 days", "Grade C", "emergency"]
    },
    {
        "query": "What is the price difference for export chilli?",
        "expected_keywords": ["Grade A", "Grade C", "$2.50", "$0.40", "80%"]
    },
    {
        "query": "Can I use Confidor on my chilli crop?",
        "expected_keywords": ["Confidor", "Imidacloprid", "banned", "export rejection"]
    }
]

print("🔍 Testing Similarity Search...")
print()

passed = 0
failed = 0

for i, test in enumerate(test_queries, 1):
    query = test["query"]
    expected = test["expected_keywords"]

    print(f"Test {i}: {query}")
    print("-" * 70)

    try:
        # Retrieve memories with similarity search
        response = client.agent_engines.memories.retrieve(
            name=agent_engine_name,
            scope={
                "app_name": APP_NAME,
                "user_id": USER_ID
            },
            similarity_search_params={
                "search_query": query
            }
        )

        # Convert response to list of Memory objects
        memory_results = list(response)

        if not memory_results:
            print("❌ FAIL: No memories retrieved")
            failed += 1
            print()
            continue

        # Collect all text from retrieved memories
        retrieved_text = ""
        memory_count = len(memory_results)
        print(f"📥 Retrieved {memory_count} memory result(s)")

        for memory in memory_results:
            # Debug: Print memory structure
            print(f"   DEBUG: Memory type: {type(memory)}")
            print(f"   DEBUG: Memory attributes: {dir(memory)[:10]}")  # First 10 attrs

            # Extract fact text from memory
            if hasattr(memory, 'memory'):
                # Memory is wrapped in another object
                actual_memory = memory.memory
                if hasattr(actual_memory, 'fact') and actual_memory.fact:
                    retrieved_text += actual_memory.fact + " "
                    print(f"   - {actual_memory.fact[:80]}...")
            elif hasattr(memory, 'fact') and memory.fact:
                retrieved_text += memory.fact + " "
                print(f"   - {memory.fact[:80]}...")

        # Check for expected keywords
        found_keywords = []
        missing_keywords = []

        for keyword in expected:
            if keyword.lower() in retrieved_text.lower():
                found_keywords.append(keyword)
            else:
                missing_keywords.append(keyword)

        # Evaluate result
        if len(missing_keywords) == 0:
            print(f"✅ PASS: All expected keywords found")
            passed += 1
        else:
            print(f"⚠️  PARTIAL: {len(found_keywords)}/{len(expected)} keywords found")
            print(f"   Missing: {', '.join(missing_keywords)}")
            # Count as pass if most keywords found
            if len(found_keywords) >= len(expected) * 0.6:
                passed += 1
            else:
                failed += 1

        print(f"   Found: {', '.join(found_keywords[:5])}...")  # Show first 5

    except Exception as e:
        print(f"❌ FAIL: {e}")
        failed += 1

    print()

# Summary
print("=" * 70)
print("📊 TEST SUMMARY")
print("=" * 70)
print(f"Total Tests: {len(test_queries)}")
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print(f"Success Rate: {(passed/len(test_queries)*100):.1f}%")
print()

if failed == 0:
    print("✅ ALL TESTS PASSED - Memory Bank is ready!")
    print()
    print("Next steps:")
    print("1. Proceed with Task 6.3: Agent Integration")
    print("2. Add PreloadMemoryTool to agronomist agent")
else:
    print("⚠️  SOME TESTS FAILED")
    print("Possible issues:")
    print("1. Memories not fully generated yet (try again in 30 seconds)")
    print("2. Knowledge not loaded (run: python load_pesticide_knowledge.py)")

print("=" * 70)

sys.exit(0 if failed == 0 else 1)
