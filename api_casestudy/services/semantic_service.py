from __future__ import annotations

import shutil
from pathlib import Path
from typing import Dict, List, Tuple

from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

from api_casestudy.core.config import get_settings
from api_casestudy.db import get_mongo_client
from api_casestudy.pipelines import build_semantic_documents
from api_casestudy.schemas import (
    SemanticBuildRequest,
    SemanticBuildResponse,
    SemanticQueryRequest,
    SemanticQueryResponse,
    SemanticResultChunk,
)


class SemanticService:
    """
    Chứa nghiệp vụ tạo và truy vấn semantic store cho từng case.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self._embeddings = OpenAIEmbeddings(model=self.settings.embedding_model)

    def build_semantic_store(self, payload: SemanticBuildRequest) -> SemanticBuildResponse:
        context, personas, skeleton = self._fetch_case_payload(payload.case_id)
        documents_map = build_semantic_documents(context, personas, skeleton)
        total_docs = sum(len(chunk) for chunk in documents_map.values())
        if not total_docs:
            raise ValueError("Không có dữ liệu nào để xây dựng semantic store.")

        persist_dir = self._case_vector_dir(payload.case_id)
        if payload.force_rebuild and persist_dir.exists():
            shutil.rmtree(persist_dir)
        persist_dir.mkdir(parents=True, exist_ok=True)

        for index_name, docs in documents_map.items():
            index_dir = persist_dir / f"{index_name}_index"
            if index_dir.exists():
                shutil.rmtree(index_dir)
            if not docs:
                continue
            index_dir.mkdir(parents=True, exist_ok=True)
            Chroma.from_documents(
                documents=docs,
                embedding=self._embeddings,
                persist_directory=str(index_dir),
            )

        return SemanticBuildResponse(
            case_id=payload.case_id,
            documents_indexed=total_docs,
            vector_store_path=str(persist_dir),
            embedding_model=self.settings.embedding_model,
        )

    def query(self, payload: SemanticQueryRequest) -> SemanticQueryResponse:
        persist_dir = self._case_vector_dir(payload.case_id)
        if not persist_dir.exists():
            raise ValueError(
                f"Chưa có semantic store cho case '{payload.case_id}'. "
                "Hãy gọi endpoint build trước."
            )

        indices: Dict[str, Chroma] = {}
        for index_name in ("scene", "persona", "policy"):
            index_dir = persist_dir / f"{index_name}_index"
            if index_dir.exists():
                indices[index_name] = Chroma(
                    persist_directory=str(index_dir),
                    embedding_function=self._embeddings,
                )

        if not indices:
            raise ValueError(
                f"Semantic store cho case '{payload.case_id}' chưa được khởi tạo đầy đủ."
            )

        combined: List[Tuple[str, float, Dict]] = []
        for index_name, store in indices.items():
            results = store.similarity_search_with_score(payload.question, k=payload.top_k)
            for document, score in results:
                metadata = dict(document.metadata or {})
                metadata.setdefault("index", index_name)
                combined.append((document.page_content, score, metadata))

        if not combined:
            return SemanticQueryResponse(
                case_id=payload.case_id,
                question=payload.question,
                top_k=payload.top_k,
                results=[],
            )

        combined.sort(key=lambda item: item[1])
        top_hits = combined[: payload.top_k]
        chunks: List[SemanticResultChunk] = [
            SemanticResultChunk(
                text=content,
                score=score,
                metadata=metadata,
            )
            for content, score, metadata in top_hits
        ]

        return SemanticQueryResponse(
            case_id=payload.case_id,
            question=payload.question,
            top_k=payload.top_k,
            results=chunks,
        )

    def ensure_store(self, case_id: str, *, force_rebuild: bool = False) -> None:
        """
        Đảm bảo semantic store tồn tại; rebuild khi cần.
        """
        persist_dir = self._case_vector_dir(case_id)
        if persist_dir.exists() and not force_rebuild:
            return
        request = SemanticBuildRequest(case_id=case_id, force_rebuild=force_rebuild)
        self.build_semantic_store(request)

    def _fetch_case_payload(self, case_id: str) -> Tuple[dict, List[dict], dict]:
        client = get_mongo_client()
        db = client[self.settings.mongo_db]

        context = db.contexts.find_one({"case_id": case_id}, {"_id": 0})
        if not context:
            raise ValueError(f"Không tìm thấy context cho case_id '{case_id}'.")
        personas = list(db.personas.find({"case_id": case_id}, {"_id": 0}))
        skeleton = db.skeletons.find_one({"case_id": case_id}, {"_id": 0})
        if not skeleton:
            raise ValueError(f"Không tìm thấy skeleton cho case_id '{case_id}'.")

        return context, personas, skeleton

    def _case_vector_dir(self, case_id: str) -> Path:
        return self.settings.semantic_data_dir / case_id / "semantic_memory"
