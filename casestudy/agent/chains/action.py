from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable


def create_action_evaluator_chain(
    llm,
    *,
    parse_error_fallback: str = "pending",
) -> Runnable:
    """
    Evaluate learner actions against canon event success criteria using an LLM.

    The evaluator asks the language model to review the learner turn and classify each
    numbered criterion as `satisfied`, `partial`, or `not_met`. Criteria marked
    `satisfied` are removed from the outstanding list; `partial` criteria remain but are
    surfaced for coaching feedback. When every criterion is satisfied, the event passes.

    Parameters
    ----------
    llm:
        Chat-oriented language model implementing the LangChain Runnable interface.
    parse_error_fallback:
        Status to emit when the LLM response cannot be parsed as the expected JSON
        schema. Defaults to `"pending"` so callers can retry with updated input.
    """

    if llm is None:
        raise ValueError("LLM instance is required for semantic evaluation.")

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "Bạn là giám khảo. Đánh giá từng tiêu chí theo suy luận ngữ nghĩa. "
                    "Chỉ trả về JSON thuần theo mẫu (ví dụ, hãy thay nội dung cho đúng dữ liệu thật):\n"
                    "{{\n"
                    '  "evaluations": [\n'
                    '    {{"id": 1, "status": "satisfied"}},\n'
                    '    {{"id": 2, "status": "partial"}},\n'
                    '    {{"id": 3, "status": "not_met"}}\n'
                    "  ]\n"
                    "}}\n"
                    "Ràng buộc:\n"
                    "- id là số nguyên dương.\n"
                    "- status chỉ được là một trong: satisfied, partial, not_met.\n"
                    "Không thêm văn bản ngoài JSON."
                ),
            ),
            (
                "human",
                (
                    "Hành động của học viên:\n"
                    "{user_action}\n\n"
                    "Tiêu chí thành công:\n"
                    "{success_criteria}\n\n"
                    "Đánh giá dựa trên ý nghĩa, không chỉ so trùng từ ngữ. "
                    "Nếu hành động đáp ứng đầy đủ tiêu chí → \"satisfied\". "
                    "Nếu mới đạt một phần → \"partial\". "
                    "Nếu chưa đáp ứng → \"not_met\".\n"
                ),
            ),
        ]
    )

    parser = StrOutputParser()
    chain = prompt | llm | parser

    def evaluate(payload: Dict[str, Any]) -> Dict[str, Any]:
        user_action = (payload.get("user_action") or "").strip()
        success_criteria: Optional[List[str]] = payload.get("success_criteria")
        if success_criteria is None:
            # Backwards compatibility with older payloads.
            success_criteria = payload.get("required_actions", [])

        success_criteria = list(success_criteria or [])

        if not success_criteria:
            return {
                "status": "pass",
                "matched_actions": [],
                "satisfied_success_criteria": [],
                "partial_success_criteria": [],
                "remaining_success_criteria": [],
                "scores": [],
            }

        if not user_action:
            return {
                "status": "pending",
                "matched_actions": [],
                "satisfied_success_criteria": [],
                "partial_success_criteria": [],
                "remaining_success_criteria": success_criteria,
                "scores": [],
            }

        numbered_criteria = "\n".join(
            f"{idx}. {criterion}" for idx, criterion in enumerate(success_criteria, start=1)
        )

        # try:
        response = chain.invoke(
            {
                "user_action": user_action,
                "success_criteria": numbered_criteria,
            }
        )
        parsed = json.loads(response)
        # except Exception:
        #     parsed = {}

        evaluations = parsed.get("evaluations", []) if isinstance(parsed, dict) else []
        status_map: Dict[int, str] = {}
        for item in evaluations:
            if not isinstance(item, dict):
                continue

            raw_idx = item.get("id")
            try:
                idx = int(raw_idx)
            except (TypeError, ValueError):
                continue

            status = str(item.get("status", "")).strip().lower()
            if status in {"satisfied", "partial", "not_met"}:
                status_map[idx] = status

        satisfied: List[str] = []
        partial: List[str] = []
        remaining: List[str] = []
        scores: List[Any] = []

        for idx, criterion in enumerate(success_criteria, start=1):
            status_value = status_map.get(idx, "not_met")
            scores.append((criterion, status_value))
            if status_value == "satisfied":
                satisfied.append(criterion)
            elif status_value == "partial":
                partial.append(criterion)
                remaining.append(criterion)
            else:
                remaining.append(criterion)

        if not status_map and success_criteria:
            status = parse_error_fallback
            scores = []
        elif not remaining:
            status = "pass"
        elif satisfied or partial:
            status = "needs_attention"
        else:
            status = "pending"

        return {
            "status": status,
            "matched_actions": satisfied,
            "satisfied_success_criteria": satisfied,
            "partial_success_criteria": partial,
            "remaining_success_criteria": remaining,
            "scores": scores,
        }

    return evaluate
