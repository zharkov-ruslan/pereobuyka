"""Локальный запуск Telegram-бота из src-layout без установки пакета."""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    project_root = Path(__file__).resolve().parent
    src_path = project_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    from pereobuyka.main import main as bot_main

    bot_main()


if __name__ == "__main__":
    main()
