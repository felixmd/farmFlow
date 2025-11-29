"""
Setup script to create Vertex AI Agent Engine with Memory Bank

This script:
1. Creates an Agent Engine in Vertex AI with Memory Bank configuration
2. Returns the AGENT_ENGINE_ID that should be added to .env file
3. Verifies the engine was created successfully

Usage:
    python setup_agent_engine.py
"""

import os
import sys
from dotenv import load_dotenv
import vertexai

# Load environment variables
load_dotenv()

PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

if not PROJECT:
    print("❌ ERROR: GOOGLE_CLOUD_PROJECT not found in .env file!")
    print("Please set your GCP project ID in .env:")
    print("GOOGLE_CLOUD_PROJECT=your-project-id")
    sys.exit(1)

print("=" * 60)
print("🚀 VERTEX AI AGENT ENGINE SETUP")
print("=" * 60)
print(f"Project: {PROJECT}")
print(f"Location: {LOCATION}")
print()

# Set environment variable for Vertex AI
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"

try:
    # Initialize Vertex AI client
    print("📡 Initializing Vertex AI client...")
    client = vertexai.Client(project=PROJECT, location=LOCATION)
    print("✅ Connected to Vertex AI")
    print()

    # Create Agent Engine with Memory Bank
    print("🏗️  Creating Agent Engine with Memory Bank...")
    print("   (This may take 30-60 seconds...)")
    print()

    agent_engine = client.agent_engines.create(
        config={
            "context_spec": {
                "memory_bank_config": {
                    "generation_config": {
                        "model": f"projects/{PROJECT}/locations/{LOCATION}/publishers/google/models/gemini-2.5-flash"
                    }
                }
            }
        }
    )

    # Extract Agent Engine ID
    agent_engine_id = agent_engine.api_resource.name.split("/")[-1]

    print("=" * 60)
    print("✅ SUCCESS! Agent Engine Created")
    print("=" * 60)
    print(f"Agent Engine ID: {agent_engine_id}")
    print(f"Full Resource Name: {agent_engine.api_resource.name}")
    print()
    print("📝 Next Steps:")
    print("1. Add this line to your .env file:")
    print(f"   AGENT_ENGINE_ID={agent_engine_id}")
    print()
    print("2. Verify it's set correctly:")
    print("   cat .env | grep AGENT_ENGINE_ID")
    print()
    print("3. Continue with Task 6.2: Load Pesticide Knowledge")
    print("=" * 60)

    # Write to a temp file for easy copying
    with open(".agent_engine_id", "w") as f:
        f.write(agent_engine_id)
    print()
    print("💾 Agent Engine ID also saved to: .agent_engine_id")

except Exception as e:
    print("=" * 60)
    print("❌ FAILED TO CREATE AGENT ENGINE")
    print("=" * 60)
    print(f"Error: {e}")
    print()
    print("Common issues:")
    print("1. Vertex AI API not enabled:")
    print("   gcloud services enable aiplatform.googleapis.com --project=" + PROJECT)
    print()
    print("2. Authentication not configured:")
    print("   gcloud auth application-default login")
    print()
    print("3. Insufficient permissions:")
    print("   Your account needs 'Vertex AI User' role")
    print("=" * 60)
    sys.exit(1)
