"""
LLM provider adapters.

Every provider exposes the same small interface used by the analyzer:

    provider.generate_content(prompt, generation_config=None) -> response with a .text string

so the analysis prompts work unchanged whichever model answers them.
"""

import os
from typing import Optional


class ProviderConfigError(Exception):
    """A configuration problem that retrying won't fix (bad key, unknown model, unreachable server)."""


class ProviderAuthError(ProviderConfigError):
    """The provider rejected the API key."""


class ProviderModelError(ProviderConfigError):
    """The requested model doesn't exist or isn't available to this key."""


class TextResponse:
    """Minimal response object with the .text attribute the analyzer reads."""

    def __init__(self, text: str):
        self.text = text


PROVIDERS = {
    "gemini": {
        "label": "Google Gemini",
        "default_model": "gemini-flash-latest",
        "key_env": "GOOGLE_API_KEY",
        "key_url": "https://aistudio.google.com/app/apikey",
    },
    "openai": {
        "label": "OpenAI",
        "default_model": "gpt-5-mini",
        "key_env": "OPENAI_API_KEY",
        "key_url": "https://platform.openai.com/api-keys",
    },
    "anthropic": {
        "label": "Anthropic Claude",
        "default_model": "claude-opus-5-5",
        "key_env": "ANTHROPIC_API_KEY",
        "key_url": "https://platform.claude.com/settings/keys",
    },
    # Presets for free-tier OpenAI-compatible services, so users only need to paste a key
    "groq": {
        "label": "Groq (free tier)",
        "default_model": "llama-3.3-70b-versatile",
        "key_env": "GROQ_API_KEY",
        "key_url": "https://console.groq.com/keys",
        "base_url": "https://api.groq.com/openai/v1",
    },
    "openrouter": {
        "label": "OpenRouter (free models)",
        # Routes to whichever free model is available, so it survives OpenRouter rotating its free list
        "default_model": "openrouter/free",
        "key_env": "OPENROUTER_API_KEY",
        "key_url": "https://openrouter.ai/settings/keys",
        "base_url": "https://openrouter.ai/api/v1",
    },
    "openai_compatible": {
        "label": "OpenAI-compatible",
        "default_model": "",
        "key_env": None,
        "key_url": None,
    },
}

PLACEHOLDER_KEYS = {"", "your_google_api_key_here", "your_api_key_here"}


def get_builtin_key(provider: str) -> Optional[str]:
    """Return the host-configured key for a provider from Streamlit secrets or the environment."""
    key_env = PROVIDERS[provider]["key_env"]
    if not key_env:
        return None
    key = None
    try:
        import streamlit as st
        key = st.secrets.get(key_env)
    except Exception:
        pass
    key = key or os.getenv(key_env)
    return None if not key or key in PLACEHOLDER_KEYS else key


def create_provider(provider: str, api_key: Optional[str], model: Optional[str], base_url: Optional[str] = None):
    """Build the adapter for a provider. Imports are lazy so unused SDKs needn't be installed."""
    if provider == "gemini":
        from .gemini_provider import GeminiProvider
        return GeminiProvider(api_key, model)
    if provider == "openai":
        from .openai_provider import OpenAIProvider
        return OpenAIProvider(api_key, model or PROVIDERS["openai"]["default_model"])
    if PROVIDERS.get(provider, {}).get("base_url"):
        from .openai_provider import OpenAIProvider
        info = PROVIDERS[provider]
        return OpenAIProvider(api_key, model or info["default_model"], base_url=info["base_url"],
                              server_name=info["label"].split(" (")[0])
    if provider == "openai_compatible":
        from .openai_provider import OpenAIProvider
        if not base_url:
            raise ProviderConfigError("Enter the base URL of your OpenAI-compatible server.")
        if not model:
            raise ProviderConfigError("Enter the model name to use on your OpenAI-compatible server.")
        return OpenAIProvider(api_key or "not-needed", model, base_url=base_url)
    if provider == "anthropic":
        from .anthropic_provider import AnthropicProvider
        return AnthropicProvider(api_key, model or PROVIDERS["anthropic"]["default_model"])
    raise ProviderConfigError(f"Unknown AI provider: {provider}")
