"""Anthropic Claude adapter."""

import logging
from typing import Any, Dict, Optional

import anthropic

from . import ProviderAuthError, ProviderModelError, TextResponse

logger = logging.getLogger(__name__)

# Models that accept the server-side refusal fallback (fallbacks="default")
SERVER_FALLBACK_MODELS = {"claude-fable-5-1", "claude-opus-5-5", "claude-opus-5", "claude-sonnet-5-5"}

# Models that accept output_config.effort
EFFORT_MODELS = SERVER_FALLBACK_MODELS | {
    "claude-fable-5", "claude-haiku-5-5", "claude-sonnet-5",
    "claude-opus-4-8", "claude-opus-4-7", "claude-opus-4-6", "claude-sonnet-4-6",
}

# Non-streaming requests stay comfortably under SDK HTTP timeouts at this size
MAX_TOKENS = 16000

# Seconds per request
REQUEST_TIMEOUT = 300.0


class AnthropicProvider:
    def __init__(self, api_key: str, model: str):
        # Rate-limit retries are handled by the analyzer, so the SDK retries only once
        self.client = anthropic.Anthropic(api_key=api_key, timeout=REQUEST_TIMEOUT, max_retries=1)
        self.model = model

    def generate_content(self, prompt: str, generation_config: Optional[Dict[str, Any]] = None) -> TextResponse:
        # Sampling settings (temperature/top_p/top_k) from generation_config are intentionally not sent:
        # current Claude models reject them. Thinking is left at the model default (adaptive).
        params = {
            "model": self.model,
            "max_tokens": MAX_TOKENS,
            "messages": [{"role": "user", "content": prompt}],
        }
        if self.model in EFFORT_MODELS:
            params["output_config"] = {"effort": "medium"}

        try:
            if self.model in SERVER_FALLBACK_MODELS:
                response = self.client.beta.messages.create(
                    **params,
                    betas=["server-side-fallback-2026-07-01"],
                    fallbacks="default",
                )
            else:
                response = self.client.messages.create(**params)
        except (anthropic.AuthenticationError, anthropic.PermissionDeniedError) as e:
            raise ProviderAuthError("Anthropic rejected the API key. Check the key you entered.") from e
        except anthropic.NotFoundError as e:
            raise ProviderModelError(f"Claude model '{self.model}' was not found. Check the model name.") from e

        if response.stop_reason == "refusal":
            category = getattr(response.stop_details, "category", None) if response.stop_details else None
            return TextResponse(f"⚠️ Claude declined this request (category: {category}).")

        text = "".join(block.text for block in response.content if block.type == "text")
        if response.stop_reason == "max_tokens":
            text += "\n\n⚠️ Response was cut off at the length limit."
        return TextResponse(text)
