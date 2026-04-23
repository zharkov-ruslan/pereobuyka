from pereobuyka.bot.handlers.ask import extract_ask_text


def test_extract_ask_text_basic() -> None:
    assert extract_ask_text("/ask привет") == "привет"


def test_extract_ask_text_with_bot_suffix() -> None:
    assert extract_ask_text("/ask@pereobuyka_bot что по ценам?") == "что по ценам?"


def test_extract_ask_text_empty() -> None:
    assert extract_ask_text("/ask") is None
    assert extract_ask_text("/ask   ") is None
