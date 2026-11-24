import asyncio
import os
import sys

# Ensure ai-service root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.providers.ollama_provider import OllamaProvider

async def main():
    print("--- 1. Testing OllamaProvider initialization & Health Check ---")
    provider = OllamaProvider()
    health = await provider.health_check()
    print("Health response:", health)
    if health.get("status") != "healthy":
        print("FAIL: Ollama is not available!")
        sys.exit(1)

    print("\n--- 2. Testing Live Text Generation ---")
    text_res = await provider.generate(
        prompt="Explain what an expense splitter does in one sentence.",
        system_prompt="Be extremely concise."
    )
    print("Text response:\n", text_res)

    print("\n--- 3. Testing Live Structured JSON Generation ---")
    schema = {
        "type": "object",
        "properties": {
            "merchant": {"type": "string"},
            "total": {"type": "number"},
            "currency": {"type": "string"}
        },
        "required": ["merchant", "total", "currency"]
    }
    json_res = await provider.generate_structured(
        prompt="Extract: Supermarket Receipt from Whole Foods on 2026-05-10. Total paid: 45.50 USD.",
        response_schema=schema,
        system_prompt="You are a data extractor. Return JSON matching the schema."
    )
    print("Structured JSON response:", json_res)
    assert isinstance(json_res, dict), "Result must be a dict"
    assert "total" in json_res, "Result must contain 'total'"
    print("\n[SUCCESS] Live Ollama Qwen inference verified!")

if __name__ == "__main__":
    asyncio.run(main())
