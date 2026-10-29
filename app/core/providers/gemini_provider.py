"""Google Gemini adapter (google-genai SDK) with automatic fallback when a model is retired."""

import logging
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import errors as genai_errors

from . import ProviderAuthError

logger = logging.getLogger(__name__)


class GeminiProvider:
    """
    Thin wrapper around the google-genai client that keeps the
    model.generate_content(prompt, generation_config=...) / response.text interface
    used throughout GeminiAnalyzer, and falls back to another model when one is retired.
    """

    # Tried in order after any configured model; aliases keep working as Google releases new models
    FALLBACK_MODELS = ["gemini-flash-latest", "gemini-2.5-flash", "gemini-2.0-flash"]

    # Model that last worked, shared across instances so later requests skip retired models
    _resolved_model: Optional[str] = None

    def __init__(self, api_key: str, preferred_model: Optional[str] = None):
        self.client = genai.Client(api_key=api_key)
        candidates = [preferred_model] if preferred_model else []
        candidates += self.FALLBACK_MODELS
        self.candidates = [m.removeprefix("models/") for m in dict.fromkeys(candidates)]

    def _models_to_try(self) -> List[str]:
        if GeminiProvider._resolved_model:
            return [GeminiProvider._resolved_model]
        return self.candidates

    def _discover_flash_model(self) -> Optional[str]:
        """Ask the API for any available Flash model when none of the known names work."""
        try:
            for model in self.client.models.list():
                name = model.name.removeprefix("models/")
                actions = getattr(model, "supported_actions", None) or []
                if "flash" in name and "generateContent" in actions and name not in self.candidates:
                    return name
        except Exception as e:
            logger.warning(f"Could not list Gemini models: {e}")
        return None

    def generate_content(self, prompt: str, generation_config: Optional[Dict[str, Any]] = None):
        models = self._models_to_try()
        last_error = None

        for attempt_discovery in (False, True):
            if attempt_discovery:
                discovered = self._discover_flash_model()
                if not discovered:
                    break
                models = [discovered]

            for model in models:
                try:
                    response = self.client.models.generate_content(
                        model=model, contents=prompt, config=generation_config
                    )
                    if GeminiProvider._resolved_model != model:
                        logger.info(f"Using Gemini model: {model}")
                        GeminiProvider._resolved_model = model
                    return GeminiResponse(response)
                except genai_errors.ClientError as e:
                    message = str(e)
                    if e.code in (401, 403) or "API_KEY_INVALID" in message or "API key not valid" in message:
                        raise ProviderAuthError(
                            "Gemini rejected the API key. Check the key you entered, or GOOGLE_API_KEY in your secrets or .env file."
                        ) from e
                    if e.code == 404 or "not found" in message.lower() or "not supported" in message.lower():
                        logger.warning(f"Gemini model {model} unavailable, trying next: {message[:200]}")
                        if GeminiProvider._resolved_model == model:
                            GeminiProvider._resolved_model = None
                        last_error = e
                        continue
                    raise

        raise Exception(f"No available Gemini model found. Last error: {last_error}")


class GeminiResponse:
    """Response wrapper whose .text is always a string, as the analyzer methods expect."""

    def __init__(self, response):
        self._response = response

    @property
    def text(self) -> str:
        text = self._response.text
        if text:
            return text
        finish_reason = None
        try:
            finish_reason = self._response.candidates[0].finish_reason
        except (AttributeError, IndexError, TypeError):
            pass
        return f"⚠️ Gemini returned no text (finish reason: {finish_reason}). Try again or reduce the document size."
