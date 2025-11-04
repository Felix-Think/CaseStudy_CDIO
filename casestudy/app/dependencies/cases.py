from __future__ import annotations

from functools import lru_cache

from casestudy.app.services.case_service import CaseService


@lru_cache
def get_case_service() -> CaseService:
    return CaseService()
