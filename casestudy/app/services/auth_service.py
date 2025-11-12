from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from typing import Any, Dict, Optional

import certifi
from bson.objectid import ObjectId
from pymongo import MongoClient
from pymongo.collection import Collection

from casestudy.app.core.config import get_settings
from casestudy.app.schemas.auth import LoginRequest, RegisterRequest


class AuthService:
    """Service đơn giản quản lý đăng ký/đăng nhập qua MongoDB."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.collection, self.session_collection = self._create_collections()

    def _create_collections(self) -> tuple[Collection, Collection]:
        tls_kwargs: Dict[str, Any] = {}
        try:
            if "mongodb+srv://" in self.settings.mongo_uri:
                tls_kwargs = {"tls": True, "tlsCAFile": certifi.where()}
        except Exception:
            tls_kwargs = {}

        client = MongoClient(
            self.settings.mongo_uri,
            serverSelectionTimeoutMS=self.settings.mongo_timeout_ms,
            **tls_kwargs,
        )
        db = client[self.settings.mongo_user_db]
        return db["member"], db["SessionOwner"]

    @staticmethod
    def _hash_password(raw_password: str) -> str:
        return hashlib.sha256(raw_password.encode("utf-8")).hexdigest()

    def register_member(self, payload: RegisterRequest) -> str:
        if payload.password != payload.password_confirm:
            raise ValueError("Password và xác nhận password không khớp.")

        email = payload.email.lower()
        if self.collection.find_one({"email": email}):
            raise ValueError("Email đã được đăng ký trên hệ thống.")

        document = {
            "email": email,
            "password": payload.password,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        self.collection.insert_one(document)
        return document["email"]

    def authenticate_member(self, payload: LoginRequest) -> Dict[str, Any]:
        email = payload.email.lower()
        document: Optional[Dict[str, Any]] = self.collection.find_one({"email": email})
        if not document:
            raise ValueError("Email hoặc password chưa đúng.")

        stored_plain = document.get("password")
        stored_hash = document.get("password_hash")

        password_ok = False
        if stored_plain is not None:
            password_ok = stored_plain == payload.password
        elif stored_hash is not None:
            password_ok = stored_hash == self._hash_password(payload.password)

        if not password_ok:
            raise ValueError("Email hoặc password chưa đúng.")

        return document

    def append_session_owner(self, user_id: str, session_id: str) -> bool:
        if not ObjectId.is_valid(user_id):
            raise ValueError("Invalid user id.")
        if not session_id or not session_id.strip():
            raise ValueError("Invalid session id.")

        now = datetime.now(timezone.utc)
        result = self.session_collection.update_one(
            {"user_id": ObjectId(user_id)},
            {
                "$setOnInsert": {
                    "user_id": ObjectId(user_id),
                    "created_at": now,
                },
                "$addToSet": {"session_ids": session_id},
                "$set": {"updated_at": now},
            },
            upsert=True,
        )
        return result.matched_count > 0 or result.upserted_id is not None
