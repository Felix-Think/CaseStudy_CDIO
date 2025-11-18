from __future__ import annotations

from functools import lru_cache

from casestudy.app.services.case_service import CaseService
from casestudy.app.services.case_draft_service import CaseDraftService


@lru_cache
def get_case_service() -> CaseService:
    return CaseService()


@lru_cache
def get_case_draft_service() -> CaseDraftService:
    return CaseDraftService()
