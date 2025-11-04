from __future__ import annotations

from typing import Any, Dict

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from ..const import DEFAULT_CASE_ID


def create_scene_summary_chain(
    scene_retriever,
    llm,
    *,
    case_id: str = DEFAULT_CASE_ID,
) -> Runnable:
    """
    Build a concise scene summarisation chain that works for any case study.

    The prompt focuses on what the trainee needs to know (environment,
    resources, risks) without overfitting to the sample drowning scenario.
    Nó cũng cập nhật bối cảnh dựa trên hành động mới nhất của học viên.
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "Bạn là điều phối viên huấn luyện mô phỏng. "
                    "Hãy tóm tắt bối cảnh cho một case study y khoa dạng mô phỏng."
                ),
            ),
            (
                "human",
                (
                    "Case ID: {case_id}\n"
                    "Canon Event: {event_title}\n"
                    "Mô tả ngắn gọn từ logic memory: {event_description}\n\n"
                    "Tóm tắt hiện tại (nếu có): {previous_summary}\n"
                    "Hành động mới nhất của học viên: {user_action}\n\n"
                    "Thông tin bổ sung từ Semantic Memory:\n{documents}\n\n"
                    "Yêu cầu: Viết 3-4 câu tiếng Việt, thể hiện rõ môi trường, "
                    "rủi ro đáng chú ý và nguồn lực hiện có cho học viên. "
                    "Nếu hành động của học viên làm thay đổi bối cảnh (ngăn ngừa rủi ro, "
                    "huy động nguồn lực, trấn an nhân vật...), hãy cập nhật mô tả tương ứng. "
                    "Nếu không ảnh hưởng đáng kể, chỉ xác nhận trạng thái hiện tại."
                ),
            ),
        ]
    )
    chain = prompt | llm | StrOutputParser()

    def summarize(payload: Dict[str, Any]) -> str:
        query_parts = [
            payload.get("query"),
            payload.get("event_description"),
            payload.get("user_action"),
        ]
        query = " ".join(part for part in query_parts if part) or ""
        documents = scene_retriever.invoke(query)
        formatted_docs = "\n".join(f"- {doc.page_content}" for doc in documents) or "- Không tìm thấy dữ liệu."

        return chain.invoke(
            {
                "case_id": case_id,
                "event_title": payload.get("event_title", "Sự kiện"),
                "event_description": payload.get("event_description", ""),
                "documents": formatted_docs,
                "previous_summary": payload.get("previous_summary", "Chưa có dữ liệu."),
                "user_action": payload.get("user_action", "Chưa ghi nhận."),
            }
        )

    return summarize
