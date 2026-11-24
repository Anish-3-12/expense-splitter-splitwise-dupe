import json
import re
import urllib.request
import urllib.error
from typing import Optional, Dict, Any
from app.core.config import settings
from app.core.logging import logger

class OllamaProvider:
    """
    Reusable Ollama Provider for local LLM inference.
    Uses native standard library urllib for fast, low-overhead asynchronous/synchronous calls.
    Respects hardware limits (~6 GB RAM machine).
    """

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None, timeout: Optional[int] = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = timeout or settings.INFERENCE_TIMEOUT

    async def health_check(self) -> Dict[str, Any]:
        """
        Queries Ollama /api/tags to verify daemon is running and model is loaded.
        """
        try:
            url = f"{self.base_url}/api/tags"
            req = urllib.request.Request(url, headers={"User-Agent": "SplitwiseAI/1.0"})
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    models = [m.get("name") for m in data.get("models", [])]
                    model_found = any(self.model in m or m in self.model for m in models)
                    return {
                        "status": "healthy" if model_found else "degraded",
                        "daemon_connected": True,
                        "installed_models": models,
                        "configured_model": self.model,
                        "model_available": model_found
                    }
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return {
                "status": "unhealthy",
                "daemon_connected": False,
                "error": str(e),
                "configured_model": self.model,
                "model_available": False
            }

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generates text completion from Ollama.
        """
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        if system_prompt:
            payload["system"] = system_prompt

        return self._execute_request(payload)

    async def generate_structured(
        self,
        prompt: str,
        response_schema: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates structured JSON response from Ollama, using schema-constrained grammar.
        Includes robust JSON extraction, error recovery, and parsing.
        """
        schema_desc = f"\nRequired JSON Schema:\n{json.dumps(response_schema, indent=2)}" if response_schema else ""
        enhanced_system = (system_prompt or "") + "\nYou MUST return only valid, well-formed JSON conforming strictly to the requested schema. Do not include explanatory conversational text outside the JSON."
        full_prompt = prompt + schema_desc if response_schema else prompt

        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": full_prompt,
            "system": enhanced_system,
            "stream": False,
            "format": response_schema if response_schema else "json"
        }

        raw_output = self._execute_request(payload)
        return self._extract_json(raw_output)

    def _execute_request(self, payload: Dict[str, Any]) -> str:
        """
        Internal execution helper with timeout and error handling.
        """
        url = f"{self.base_url}/api/generate"
        encoded_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=encoded_data,
            headers={"Content-Type": "application/json", "User-Agent": "SplitwiseAI/1.0"}
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                if response.status == 200:
                    resp_json = json.loads(response.read().decode("utf-8"))
                    return resp_json.get("response", "").strip()
                else:
                    raise RuntimeError(f"Ollama returned HTTP status {response.status}")
        except urllib.error.URLError as e:
            logger.error(f"Cannot connect to Ollama at {self.base_url}: {e}")
            raise RuntimeError(f"Ollama service unavailable at {self.base_url}: {e}")
        except TimeoutError:
            logger.error(f"Ollama inference timed out after {self.timeout}s")
            raise TimeoutError(f"Inference timed out after {self.timeout}s")

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """
        Extracts and parses JSON from model output, handling potential markdown wrappers.
        """
        text = text.strip()
        # Direct parse attempt
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try markdown code block regex ```json ... ```
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # Try matching outermost curly braces {...}
        brace_match = re.search(r"\{[\s\S]*\}", text)
        if brace_match:
            try:
                return json.loads(brace_match.group(0).strip())
            except json.JSONDecodeError:
                pass

        logger.error(f"Failed to parse structured JSON from output: {text[:200]}")
        raise ValueError(f"Model output could not be parsed as JSON: {text[:200]}")

ollama_provider = OllamaProvider()
