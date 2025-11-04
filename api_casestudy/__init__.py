from __future__ import annotations

"""
api_casestudy package
=====================

Chứa service FastAPI độc lập để quản lý dữ liệu CaseStudy từ MongoDB và
xây dựng semantic store phục vụ tác vụ truy vấn.
"""

__all__ = ["create_app"]

from .main import create_app  # noqa: E402
