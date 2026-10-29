"""OpenAI and OpenAI-compatible (Groq, OpenRouter, Ollama, LM Studio, ...) adapter."""

import logging
from typing import Any, Dict, Optional

import openai

from . import ProviderAuthError, ProviderConfigError, ProviderModelError, TextResponse

logger = logging.getLogger(__name__)

# Reasoning models spend part of the completion budget on hidden reasoning
OPENAI_MAX_COMPLETION_TOKENS = 16000

# Seconds per request; local models on modest hardware get longer
REQUEST_TIMEOUT = 180.0
COMPATIBLE_REQUEST_TIMEOUT = 300.0


class OpenAIProvider:
    def __init__(self, api_key: str, model: str, base_url: Optional[str] = None):
        timeout = COMPATIBLE_REQUEST_TIMEOUT if base_url else REQUEST_TIMEOUT
        # Rate-limit retries are handled by the analyzer, so the SDK retries only once
        self.client = openai.OpenAI(api_key=api_key, base_url=base_url, timeout=timeout, max_retries=1)
        self.model = model
        self.base_url = base_url

    def generate_content(self, prompt: str, generation_config: Optional[Dict[str, Any]] = None) -> TextResponse:
        config = generation_config or {}
        params = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
        }
        if self.base_url:
            # Compatible servers widely support the classic parameters
            params["max_tokens"] = config.get("max_output_tokens", 8192)
            if "temperature" in config:
                params["temperature"] = config["temperature"]
        else:
            # Current OpenAI models take max_completion_tokens and only the default temperature
            params["max_completion_tokens"] = max(config.get("max_output_tokens", 0), OPENAI_MAX_COMPLETION_TOKENS)

        provider_name = "The AI server" if self.base_url else "OpenAI"
        try:
            response = self.client.chat.completions.create(**params)
        except (openai.AuthenticationError, openai.PermissionDeniedError) as e:
            raise ProviderAuthError(f"{provider_name} rejected the API key. Check the key you entered.") from e
        except openai.NotFoundError as e:
            raise ProviderModelError(f"Model '{self.model}' was not found. Check the model name.") from e
        except openai.APIConnectionError as e:
            if self.base_url:
                raise ProviderConfigError(f"Could not connect to {self.base_url}. Check the base URL and that the server is running.") from e
            raise

        choice = response.choices[0] if response.choices else None
        text = (choice.message.content if choice and choice.message else None) or ""
        if not text:
            finish_reason = choice.finish_reason if choice else None
            text = f"⚠️ The model returned no text (finish reason: {finish_reason})."
        return TextResponse(text)
