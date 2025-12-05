from __future__ import annotations

"""
api_casestudy package
=====================

Dịch vụ FastAPI độc lập điều phối agent hội thoại cho từng CaseStudy.
"""

__all__ = ["create_app"]

from .main import create_app  # noqa: E402
