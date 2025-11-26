from __future__ import annotations

from typing import Any, Dict, Iterable, List

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from ..const import DEFAULT_CASE_ID


def create_persona_digest_chain(
    persona_index,
    llm,
    *,
    case_id: str = DEFAULT_CASE_ID,
    top_k: int = 1,
) -> Runnable:
    """
    Build a chain that consolidates persona details into short operational digests.
    The prompt avoids assumptions about persona structure so it can adapt to
    future case studies.
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "Bạn đang chuẩn bị thông tin nhân vật cho một mô phỏng học viên. "
                    "Giữ giọng điệu trung lập, tập trung vào mục tiêu, hành vi và trạng thái cảm xúc."
                ),
            ),
            (
                "human",
                (
                    "Case ID: {case_id}\n"
                    "Danh sách mô tả nhân vật thu thập được:\n{documents}\n\n"
                    "Yêu cầu: Với mỗi persona_id, hãy tóm tắt 2 câu gồm:\n"
                    "- Bối cảnh/nghề nghiệp, mục tiêu chính đối với mô phỏng.\n"
                    "- Trạng thái cảm xúc ban đầu hoặc dấu hiệu hành vi quan trọng.\n"
                    "Định dạng:\n"
                    "- {{persona_id}}: <tóm tắt>. Cảm xúc: <emotion>."
                ),
            ),
        ]
    )
    chain = prompt | llm | StrOutputParser()

    def build_digest(payload: Dict[str, Any]) -> str:
        persona_ids: Iterable[str] = payload.get("persona_ids", [])
        documents: List[str] = []

        for persona_id in persona_ids:
            query = payload.get(
                "query_template",
                "Thông tin nhân vật {persona_id} trong mô phỏng",
            ).format(persona_id=persona_id)
            results = persona_index.similarity_search(query, k=1)
            if not results:
                documents.append(f"[{persona_id}] Không tìm thấy dữ liệu nhân vật.")
            else:
                for doc in results:
                    documents.append(
                        f"[{doc.metadata.get('persona_id', persona_id)}] {doc.page_content}"
                    )

        formatted_docs = "\n".join(documents) or "Không có dữ liệu nhân vật."
        return chain.invoke({"case_id": case_id, "documents": formatted_docs})

    return build_digest


def create_persona_dialogue_chain(
    llm,
    *,
    case_id: str = DEFAULT_CASE_ID,
) -> Runnable:
    """
    Generate short in-character dialogue snippets for active personas.
    Output must be JSON array with persona_id + utterance fields so downstream
    nodes can update the conversation history deterministically.
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "Bạn điều phối lời thoại cho các nhân vật (NPC) trong mô phỏng, ngữ cảnh mô phòng phải phải đúng với sự kiện hiện tại. "
                    "Hãy giữ giọng điệu và hành động phù hợp hồ sơ từng nhân vật, ngắn gọn "
                    "và tập trung vào tình huống hiện tại. Trả về JSON."
                ),
            ),
            (
                "human",
                (
                    "Case ID: {case_id}\n"
                    "Canon Event: {event_title}\n"
                    "Tóm tắt bối cảnh hiện tại: {scene_summary}\n"
                    "Hành động mới nhất của học viên: {user_action}\n"
                    "Danh sách nhân vật được phép phản hồi:\n{allowed_personas}\n"
                    "Trạng thái nhân vật: {persona_slate}\n"
                    "Đoạn hội thoại gần nhất:\n{recent_history}\n\n"
                    "Sau khi đã có trạng thái nhân vật khởi tạo thì phải dựa trên mức độ điểm hoàn thành mà thay đổi cảm xúc nhân vật cho phù hợp.\n"
                    "Yêu cầu:\n"
                    "- Chỉ tạo lời thoại cho các nhân vật có trong danh sách được phép.\n"
                    "- Lời thoại tạo ra phải phù hợp với bối cảnh, sự kiện, mức độ điểm hoàn thành và hành động của học viên.\n" 
                    "- Mỗi nhân vật tối đa 1-2 câu, ưu tiên hành vi hợp lý.\n"
                    "- Trả về emotion mới của nhân vật (nếu có thay đổi) để cập nhật trạng thái.\n"
                    "- Nếu không cần phản hồi, trả về mảng rỗng.\n"
                    
                    "- Phản hồi cuối cùng ở dạng JSON array: "
                    "[{{\"persona_id\": \"P1\", \"persona_name\": \"Tên\", \"utterance\": \"...\", \"emotion\": \"...\"}}]."
                ),
            ),
        ]
    )
    chain = prompt | llm | StrOutputParser()

    def generate(payload: Dict[str, Any]) -> str:
        return chain.invoke(
            {
                "case_id": case_id,
                "event_title": payload.get("event_title", "Sự kiện"),
                "scene_summary": payload.get("scene_summary", "Chưa có dữ liệu."),
                "user_action": payload.get("user_action", "Chưa ghi nhận."),
                "allowed_personas": payload.get("allowed_personas", "Không có nhân vật."),
                "persona_slate": payload.get("persona_slate", "Không có nhân vật."),
                "recent_history": payload.get("recent_history", "Chưa có hội thoại."),
            }
        )

    return generate
