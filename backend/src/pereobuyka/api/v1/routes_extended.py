"""Сборка маршрутов этапа 1: auth, клиент, консультация, админ."""

from __future__ import annotations

from fastapi import APIRouter

from pereobuyka.api.v1.endpoints import admin, admin_web, auth, client, consultation

router = APIRouter()
router.include_router(auth.router)
router.include_router(client.router)
router.include_router(consultation.router)
router.include_router(admin.router)
router.include_router(admin_web.router)
