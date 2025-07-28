#!/usr/bin/env python3
"""Test script to isolate Gemini embedding issue."""

import asyncio

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.config.llama_index_config import get_llama_index_config


async def test_gemini_embedding():
    """Test Gemini embedding functionality."""
    try:
        print("🔧 Testing Gemini embedding configuration...")

        # Create config
        config = get_llama_index_config()
        print("✓ Config created successfully")
        print(f"  GEMINI_API_KEY: {'***' + config.gemini_api_key[-4:] if config.gemini_api_key else 'NOT SET'}")

        # Get embedding model
        embed_model = config.get_embedding_model()
        print(f"✓ Embedding model created: {type(embed_model)}")

        # Test simple embedding
        test_text = "This is a test document for legal analysis."
        print(f"🧪 Testing embedding generation for: '{test_text}'")

        embedding = await embed_model.aget_text_embedding(test_text)
        print("✅ Embedding generated successfully!")
        print(f"   Embedding dimension: {len(embedding)}")
        print(f"   First 5 values: {embedding[:5]}")

        return True

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return False

async def main():
    """Main function."""
    print("Starting Gemini embedding test...")
    success = await test_gemini_embedding()

    if success:
        print("✅ Test completed successfully!")
    else:
        print("❌ Test failed!")

    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)
