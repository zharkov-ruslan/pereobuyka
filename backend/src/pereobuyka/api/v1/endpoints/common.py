"""Общие типы зависимостей для эндпоинтов v1."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends

from pereobuyka.api.v1.deps import get_current_user

CurrentUser = Annotated[UUID, Depends(get_current_user)]
