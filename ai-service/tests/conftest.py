import pytest
from app.providers.ollama_provider import ollama_provider

@pytest.fixture(autouse=True)
def mock_ollama_provider_for_unit_tests(monkeypatch):
    """
    By default, mock Ollama inference during unit tests to ensure fast, deterministic testing
    without external network or heavy local GPU/CPU load, as instructed in Part 13.
    """
    async def mock_health_check():
        return {
            "status": "healthy",
            "daemon_connected": True,
            "installed_models": ["qwen2.5:1.5b"],
            "configured_model": "qwen2.5:1.5b",
            "model_available": True
        }

    async def mock_generate_structured(prompt, response_schema=None, system_prompt=None):
        prompt_lower = prompt.lower()
        sys_lower = (system_prompt or "").lower()

        # 1. Receipt extraction
        if "receipt" in sys_lower or "ocr text" in prompt_lower:
            return {
                "merchant": "Pizza Palace Restaurant",
                "receipt_date": "2026-03-15",
                "currency": "INR",
                "subtotal": 600.00,
                "tax": 50.00,
                "total": 650.00,
                "items": [
                    {
                        "description": "Pizza Margherita",
                        "quantity": 1,
                        "unit_price": 450.00,
                        "line_total": 450.00
                    },
                    {
                        "description": "Garlic Bread",
                        "quantity": 1,
                        "unit_price": 150.00,
                        "line_total": 150.00
                    },
                    {
                        "description": "Coke",
                        "quantity": 1,
                        "unit_price": 50.00,
                        "line_total": 50.00
                    }
                ]
            }

        # 2. Categorization
        if "categor" in sys_lower or "categorize" in prompt_lower:
            return {"category": "Food & Dining", "confidence": 0.95}

        # 3. Natural language splitting
        return {
            "allocations": [
                {
                    "item_id": "item-1",
                    "item_description": "Pizza",
                    "participant_ids": [1, 2],
                    "split_type": "EQUAL"
                }
            ],
            "unresolved_references": [],
            "clarification_required": False,
            "clarification_question": None
        }

    async def mock_generate(prompt, system_prompt=None):
        return "Mock Ollama Response"

    monkeypatch.setattr(ollama_provider, "health_check", mock_health_check)
    monkeypatch.setattr(ollama_provider, "generate_structured", mock_generate_structured)
    monkeypatch.setattr(ollama_provider, "generate", mock_generate)
