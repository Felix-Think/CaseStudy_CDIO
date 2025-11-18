from __future__ import annotations

import json
import copy
from typing import Any, Dict, List, Optional

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

SUCCESS_LEVEL_SCORES = [5, 4, 3, 2, 1]


def _normalize_levels(levels_data: Optional[List[Any]], fallback_description: str) -> List[Dict[str, Any]]:
    level_map: Dict[int, str] = {}
    for level in levels_data or []:
        if not isinstance(level, dict):
            continue
        score_value = level.get("score")
        try:
            score = int(score_value)
        except (TypeError, ValueError):
            continue
        descriptor = str(level.get("descriptor", "")).strip()
        if descriptor:
            level_map[score] = descriptor

    normalized_levels: List[Dict[str, Any]] = []
    for score in SUCCESS_LEVEL_SCORES:
        normalized_levels.append({"score": score, "descriptor": level_map.get(score, "")})

    if not any(entry["descriptor"] for entry in normalized_levels):
        normalized_levels[0]["descriptor"] = fallback_description or "Đạt yêu cầu cao nhất."

    return normalized_levels


def normalize_success_criteria(raw_criteria: Optional[List[Any]]) -> List[Dict[str, Any]]:
    """
    Convert raw success criteria (strings or rubric dicts) into a consistent rubric structure.
    """
    if not raw_criteria:
        return []

    normalized: List[Dict[str, Any]] = []
    for idx, criterion in enumerate(raw_criteria, start=1):
        if isinstance(criterion, dict):
            description = str(criterion.get("description", "")).strip()
            levels_data = criterion.get("levels")
        else:
            description = str(criterion or "").strip()
            levels_data = None

        if not description and not levels_data:
            continue

        normalized.append(
            {
                "description": description or f"Tiêu chí {idx}",
                "levels": _normalize_levels(levels_data, description),
            }
        )
    return normalized


def format_rubric_for_prompt(rubric: List[Dict[str, Any]]) -> str:
    """
    Render rubric data into a readable prompt segment for the evaluator LLM.
    """
    blocks: List[str] = []
    for idx, criterion in enumerate(rubric, start=1):
        lines = [f"{idx}. {criterion['description']}"]
        detailed_levels = 0
        for level in criterion.get("levels", []):
            descriptor = str(level.get("descriptor", "")).strip()
            if not descriptor:
                continue
            detailed_levels += 1
            lines.append(f"   - Điểm {level.get('score')}: {descriptor}")
        if detailed_levels == 0:
            lines.append("   - Không có mô tả chi tiết; đánh giá dựa trên mô tả tổng quan.")
        blocks.append("\n".join(lines))
    return "\n".join(blocks)


def score_to_status(score: Optional[int]) -> str:
    if score is None:
        return "not_met"
    if score >= 4:
        return "satisfied"
    if score >= 2:
        return "partial"
    return "not_met"


def create_action_evaluator_chain(
    llm,
    *,
    parse_error_fallback: str = "pending",
) -> Runnable:
    """
    Evaluate learner actions against canon event success criteria using an LLM.

    The evaluator asks the language model to review the learner turn and score each
    rubric-based criterion from 1 to 5, accompanied by a short analysis. A score of 4-5
    marks the criterion as `satisfied`, 2-3 as `partial`, and 1 as `not_met`. Criteria
    that are satisfied are removed from the outstanding list; the rest remain for future
    attempts. When every criterion is satisfied, the event passes.

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
                    "Bạn là giám khảo sử dụng rubric 5 mức để chấm điểm từng tiêu chí. "
                    "Chỉ trả về JSON thuần theo mẫu (hãy thay dữ liệu cho đúng tình huống thực tế):\n"
                    "{{\n"
                    '  "evaluations": [\n'
                    '    {{"id": 1, "score": 5, "analysis": "Hành động đáp ứng đầy đủ mô tả mức 5 vì."}},\n'
                    '    {{"id": 2, "score": 3, "analysis": "Mới thực hiện được một phần yêu cầu."}}\n'
                    "  ]\n"
                    "}}\n"
                    "Quy định:\n"
                    "- id là số thứ tự tiêu chí.\n"
                    "- score là số nguyên 1-5, dựa trên rubric được cung cấp.\n"
                    "- analysis giải thích ngắn (≤25 từ) vì sao đạt điểm đó.\n"
                    "Không thêm văn bản ngoài JSON."
                ),
            ),
            (
                "human",
                (
                    "Hành động của học viên:\n"
                    "{user_action}\n\n"
                    "Rubric tiêu chí thành công:\n"
                    "{success_criteria}\n\n"
                    "Hướng dẫn: Dựa trên rubric, hãy chấm điểm 1-5 cho từng tiêu chí "
                    "và cung cấp phân tích ngắn gọn lý do.\n"
                ),
            ),
        ]
    )

    parser = StrOutputParser()
    chain = prompt | llm | parser

    def evaluate(payload: Dict[str, Any]) -> Dict[str, Any]:
        user_action = (payload.get("user_action") or "").strip()
        success_criteria_input: Optional[List[Any]] = payload.get("success_criteria")
        if success_criteria_input is None:
            # Backwards compatibility with older payloads.
            success_criteria_input = payload.get("required_actions", [])

        rubric_criteria = normalize_success_criteria(success_criteria_input)

        if not rubric_criteria:
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
                "remaining_success_criteria": rubric_criteria,
                "scores": [],
            }

        rubric_text = format_rubric_for_prompt(rubric_criteria)

        response = chain.invoke(
            {
                "user_action": user_action,
                "success_criteria": rubric_text,
            }
        )
        try:
            parsed = json.loads(response)
        except json.JSONDecodeError:
            parsed = {}

        evaluations = parsed.get("evaluations", []) if isinstance(parsed, dict) else []
        evaluation_map: Dict[int, Dict[str, Any]] = {}
        for item in evaluations:
            if not isinstance(item, dict):
                continue

            raw_idx = item.get("id")
            try:
                idx = int(raw_idx)
            except (TypeError, ValueError):
                continue

            raw_score = item.get("score")
            try:
                score = int(raw_score)
            except (TypeError, ValueError):
                continue

            score = max(min(score, SUCCESS_LEVEL_SCORES[0]), SUCCESS_LEVEL_SCORES[-1])
            analysis = str(item.get("analysis", "")).strip()
            evaluation_map[idx] = {"score": score, "analysis": analysis}

        if not evaluation_map:
            return {
                "status": parse_error_fallback,
                "matched_actions": [],
                "satisfied_success_criteria": [],
                "partial_success_criteria": [],
                "remaining_success_criteria": rubric_criteria,
                "scores": [],
            }

        satisfied: List[str] = []
        partial: List[str] = []
        remaining: List[Dict[str, Any]] = []
        scores: List[Dict[str, Any]] = []

        for idx, criterion in enumerate(rubric_criteria, start=1):
            eval_result = evaluation_map.get(idx) or {}
            score_value = eval_result.get("score")
            analysis_value = eval_result.get("analysis", "")
            status_value = score_to_status(score_value)

            scores.append(
                {
                    "id": idx,
                    "criterion": criterion["description"],
                    "score": score_value,
                    "analysis": analysis_value,
                }
            )

            if status_value == "satisfied":
                satisfied.append(criterion["description"])
            elif status_value == "partial":
                partial.append(criterion["description"])
                score_numeric = score_value if isinstance(score_value, int) else None
                if score_numeric is None or score_numeric < 3:
                    remaining.append(copy.deepcopy(criterion))
            else:
                remaining.append(copy.deepcopy(criterion))

        if not remaining:
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
