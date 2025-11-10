from __future__ import annotations

import argparse
import json
import logging
import os
import time
from typing import Any, Dict, Iterable, List, Tuple

from dotenv import load_dotenv
from langchain.docstore.document import Document
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from pinecone.exceptions import ServiceException

from casestudy.utils.document_builder import build_documents
from casestudy.app.core.config import get_settings as get_app_settings
from casestudy.app.db.database import get_mongo_client as get_app_mongo_client

# ---------------------------------------------------------------------------- #
#                               ENV CONFIGURATION                              #
# ---------------------------------------------------------------------------- #

load_dotenv()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "asia-southeast1-gcp")
PINECONE_SCENE_INDEX = os.getenv("PINECONE_SCENE_INDEX", "casestudy-scene")
PINECONE_PERSONA_INDEX = os.getenv("PINECONE_PERSONA_INDEX", "casestudy-persona")
PINECONE_POLICY_INDEX = os.getenv("PINECONE_POLICY_INDEX", "casestudy-policy")
PINECONE_TEXT_KEY = os.getenv("PINECONE_TEXT_KEY", "text")

_pinecone_client: Pinecone | None = None

INDEX_NAME_BY_LABEL = {
    "scene": PINECONE_SCENE_INDEX,
    "persona": PINECONE_PERSONA_INDEX,
    "policy": PINECONE_POLICY_INDEX,
}

DEFAULT_NAMESPACE = "default"
BATCH_SIZE_DEFAULT = 64

CASE_ID: str | None = None

# ---------------------------------------------------------------------------- #
#                              CORE CONFIGURATION                              #
# ---------------------------------------------------------------------------- #

def configure_paths(case_id: str) -> None:
    """Chỉ cần ghi nhận case_id hiện tại để dùng làm namespace Pinecone."""
    global CASE_ID
    CASE_ID = case_id
    logger.info(f"Đã cấu hình namespace: {case_id}")


def _ensure_configured() -> None:
    if CASE_ID is None:
        raise RuntimeError("Semantic namespace chưa được cấu hình. Hãy gọi configure_paths(case_id) trước.")


def normalize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Chuyển mọi giá trị phức tạp sang chuỗi JSON để đảm bảo tương thích Pinecone."""
    normalized: Dict[str, Any] = {}
    for key, value in metadata.items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            normalized[key] = value
        else:
            normalized[key] = json.dumps(value, ensure_ascii=False)
    return normalized


# ---------------------------------------------------------------------------- #
#                              MAIN SYNC FUNCTION                              #
# ---------------------------------------------------------------------------- #

def sync_case_to_pinecone(
    case_id: str,
    *,
    batch_size: int = BATCH_SIZE_DEFAULT,
    force_rebuild: bool = False,
) -> Dict[str, int]:
    """
    Đọc dữ liệu case từ MongoDB, embedding bằng OpenAI và đẩy lên Pinecone theo từng index.
    """
    _ensure_configured()
    documents_map = _build_documents_from_mongo(case_id)
    namespace = case_id
    stats: Dict[str, int] = {}
    pinecone_client = _get_pinecone_client()

    for label, documents in documents_map.items():
        index_name = INDEX_NAME_BY_LABEL.get(label)
        if not index_name:
            logger.warning(f"Bỏ qua label '{label}' (chưa cấu hình index).")
            continue
        if not documents:
            logger.info(f"Không có tài liệu nào cho nhóm '{label}'.")
            stats[label] = 0
            continue

        index = pinecone_client.Index(index_name)
        if force_rebuild:
            logger.info(f"🧹 Xóa namespace '{namespace}' trong index '{index_name}'...")
            index.delete(namespace=namespace, delete_all=True)

        inserted = _upsert_documents(
            index=index,
            namespace=namespace,
            label=label,
            documents=documents,
            batch_size=batch_size,
        )
        stats[label] = inserted

    if not stats:
        raise RuntimeError("Chưa cấu hình Pinecone index cho bất kỳ nhóm tài liệu nào.")
    return stats


# ---------------------------------------------------------------------------- #
#                           BUILD DOCUMENTS FROM MONGO                         #
# ---------------------------------------------------------------------------- #

def _build_documents_from_mongo(case_id: str) -> Dict[str, List[Document]]:
    context, personas, skeleton = _fetch_case_payload(case_id)
    documents_map = build_documents(context, personas, skeleton)
    total_docs = sum(len(items) for items in documents_map.values())
    if total_docs == 0:
        raise ValueError(f"Không có tài liệu nào để index cho case_id '{case_id}'.")
    logger.info(f"Đã tạo {total_docs} documents từ MongoDB cho case '{case_id}'.")
    return documents_map


def _fetch_case_payload(case_id: str) -> Tuple[Dict, List[Dict], Dict]:
    client = get_app_mongo_client()
    if client is None:
        raise RuntimeError("Không thể khởi tạo Mongo client để đọc dữ liệu case.")

    settings = get_app_settings()
    db = client[settings.mongo_db]

    context = db.contexts.find_one({"case_id": case_id}, {"_id": 0})
    if not context:
        raise ValueError(f"Không tìm thấy context cho case_id '{case_id}'.")

    personas = list(db.personas.find({"case_id": case_id}, {"_id": 0}))
    skeleton = db.skeletons.find_one({"case_id": case_id}, {"_id": 0})
    if not skeleton:
        raise ValueError(f"Không tìm thấy skeleton cho case_id '{case_id}'.")

    return context, personas, skeleton


# ---------------------------------------------------------------------------- #
#                         UPSERT DOCUMENTS TO PINECONE                         #
# ---------------------------------------------------------------------------- #

def _upsert_documents(
    *,
    index,
    namespace: str,
    label: str,
    documents: List[Document],
    batch_size: int,
    max_retries: int = 3,
    retry_delay: float = 2.5,
) -> int:
    """
    Upsert các Document lên Pinecone một cách an toàn, có retry và logging.
    Dùng PineconeVectorStore.add_documents() để đảm bảo đồng bộ embedding và metadata.
    """
    total_inserted = 0
    if not documents:
        return 0

    vector_store = PineconeVectorStore(
        index=index,
        embedding=embeddings,
        namespace=namespace,
        text_key=PINECONE_TEXT_KEY,
    )

    for offset, batch in _batched(documents, batch_size):
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(
                    f"[{label}] Upserting batch {offset // batch_size + 1} "
                    f"({len(batch)} docs) vào namespace '{namespace}'..."
                )
                vector_store.add_documents(batch)
                total_inserted += len(batch)
                break
            except ServiceException as e:
                logger.warning(
                    f"Lỗi mạng khi upsert batch {offset // batch_size + 1}: {e}. "
                    f"Thử lại ({attempt}/{max_retries})..."
                )
                time.sleep(retry_delay)
            except Exception as e:
                logger.error(
                    f"Lỗi nghiêm trọng khi upsert batch {offset // batch_size + 1}: {e}",
                    exc_info=True,
                )
                raise
    logger.info(f"✅ Đã upsert {total_inserted} vectors cho '{label}' (namespace={namespace})")
    return total_inserted


def _batched(items: List[Any], size: int) -> Iterable[Tuple[int, List[Any]]]:
    if size <= 0:
        size = BATCH_SIZE_DEFAULT
    for start in range(0, len(items), size):
        yield start, items[start : start + size]


# ---------------------------------------------------------------------------- #
#                           LOAD EXISTING INDICES                              #
# ---------------------------------------------------------------------------- #

def load_indices():
    _ensure_configured()
    namespace = CASE_ID or DEFAULT_NAMESPACE
    scene_store = _load_pinecone_vectorstore(PINECONE_SCENE_INDEX, namespace, "scene")
    persona_store = _load_pinecone_vectorstore(PINECONE_PERSONA_INDEX, namespace, "persona")
    policy_store = _load_pinecone_vectorstore(PINECONE_POLICY_INDEX, namespace, "policy")
    return scene_store, persona_store, policy_store


def _load_pinecone_vectorstore(index_name: str, namespace: str, label: str):
    if not index_name:
        raise RuntimeError(f"Chưa cấu hình Pinecone index cho '{label}'.")
    try:
        client = _get_pinecone_client()
        index = client.Index(index_name)
    except Exception as exc:
        raise RuntimeError(f"Không thể truy cập Pinecone index '{index_name}'.") from exc
    return PineconeVectorStore(
        index=index,
        embedding=embeddings,
        text_key=PINECONE_TEXT_KEY,
        namespace=namespace,
    )


# ---------------------------------------------------------------------------- #
#                            PINECONE CONNECTION                               #
# ---------------------------------------------------------------------------- #

def _get_pinecone_client() -> Pinecone:
    global _pinecone_client
    if _pinecone_client is not None:
        return _pinecone_client
    if not PINECONE_API_KEY:
        raise RuntimeError("Chưa cấu hình PINECONE_API_KEY.")
    client_kwargs = {"api_key": PINECONE_API_KEY}
    if PINECONE_ENVIRONMENT:
        client_kwargs["environment"] = PINECONE_ENVIRONMENT
    _pinecone_client = Pinecone(**client_kwargs)
    return _pinecone_client


# ---------------------------------------------------------------------------- #
#                                CLI ENTRYPOINT                                #
# ---------------------------------------------------------------------------- #

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Đồng bộ dữ liệu case lên Pinecone.")
    parser.add_argument("case_id", help="Case ID cần sync semantic memory.")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=BATCH_SIZE_DEFAULT,
        help=f"Số documents embed mỗi batch (mặc định {BATCH_SIZE_DEFAULT}).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Xóa namespace cũ trước khi upsert (delete_all).",
    )
    args = parser.parse_args()

    configure_paths(args.case_id)
    result = sync_case_to_pinecone(
        args.case_id,
        batch_size=args.batch_size,
        force_rebuild=args.force,
    )
    print(f"✅ Đồng bộ Pinecone thành công cho case '{args.case_id}': {result}")
