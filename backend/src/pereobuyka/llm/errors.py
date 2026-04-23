"""Ошибки LLM-слоя (OpenRouter / оркестратор консультации)."""


class ConsultationProviderError(Exception):
    """Провайдер LLM недоступен, таймаут или иная сетевая/инфраструктурная проблема."""

    def __init__(self, message: str = "LLM провайдер временно недоступен") -> None:
        super().__init__(message)


class ConsultationOrchestrationError(Exception):
    """Внутренняя ошибка оркестрации (не для утечки наружу)."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
