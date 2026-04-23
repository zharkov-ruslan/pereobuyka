"""LLM-слой backend (OpenRouter)."""

from pereobuyka.llm.errors import ConsultationOrchestrationError, ConsultationProviderError
from pereobuyka.llm.openrouter_client import OpenRouterChatClient

__all__ = [
    "ConsultationOrchestrationError",
    "ConsultationProviderError",
    "OpenRouterChatClient",
]
