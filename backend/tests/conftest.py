"""Pytest-фикстуры: TestClient, авторизация, сброс хранилища."""

from collections.abc import Generator
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from pereobuyka.api.v1.deps import get_current_user
from pereobuyka.main import app
from pereobuyka.storage import memory as mem

FAKE_USER_ID = UUID("00000000-0000-0000-0000-000000000099")


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    """Создать TestClient один раз за сессию."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_override() -> Generator[UUID, None, None]:
    """Подменить get_current_user так, чтобы возвращался FAKE_USER_ID."""
    app.dependency_overrides[get_current_user] = lambda: FAKE_USER_ID
    yield FAKE_USER_ID
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture(autouse=True)
def reset_storage() -> Generator[None, None, None]:
    """Очищать in-memory записи до и после каждого теста."""
    mem.reset_appointments()
    yield
    mem.reset_appointments()
