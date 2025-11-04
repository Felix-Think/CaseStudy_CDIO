from __future__ import annotations

import argparse
from typing import Optional

from casestudy.agent import LogicMemory, RuntimeState, build_case_study_graph
from casestudy.agent.const import DEFAULT_CASE_ID


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Chạy CaseStudy LangGraph với hành động người học."
    )
    parser.add_argument(
        "--case-id",
        default=DEFAULT_CASE_ID,
        help="Case ID cần chạy (mặc định: drowning_pool_001).",
    )
    parser.add_argument(
        "--event",
        default=None,
        help="Canon Event bắt đầu (nếu bỏ trống sẽ lấy event đầu tiên).",
    )
    parser.add_argument(
        "--user-action",
        dest="user_action",
        default=None,
        help="Mô tả hành động của học viên (tùy chọn).",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Tên model OpenAI tuỳ chọn (mặc định theo cấu hình const.py).",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Bỏ qua trạng thái đã lưu và khởi tạo mới.",
    )
    return parser.parse_args()


def invoke_graph_once(
    graph,
    state: RuntimeState,
    *,
    reset_state: bool = False,
    start_event: Optional[str] = None,
) -> RuntimeState:
    config = {"reset_state": reset_state}
    if start_event:
        config["start_event"] = start_event

    result = graph.invoke(state, config=config)
    if isinstance(result, dict):
        return RuntimeState.from_serialized(result)
    return result


def render_state(state: RuntimeState) -> None:
    print("\n=== CaseStudy Engine ===")
    print(f"Canon Event hiện tại: {state.current_event}")
    current_status = state.event_summary.get(state.current_event, "pending")
    print(f"Trạng thái đánh giá: {current_status}")

    remaining_key = f"{state.current_event}_remaining_success_criteria"
    completed_key = f"{state.current_event}_completed_success_criteria"
    partial_key = f"{state.current_event}_partial"
    scores_key = f"{state.current_event}_scores"

    remaining = state.event_summary.get(remaining_key, [])
    completed = state.event_summary.get(completed_key, [])
    partial = state.event_summary.get(partial_key, [])
    scores = state.event_summary.get(scores_key, [])

    print("\n[Success Criteria Debug]")
    if completed:
        print("- Đã đạt:")
        for item in completed:
            print(f"  • {item}")
    if partial:
        print("- Cần chú ý:")
        for item in partial:
            print(f"  • {item}")
    if remaining:
        print("- Còn lại:")
        for item in remaining:
            print(f"  • {item}")
    if not any([completed, partial, remaining]):
        print("  (Không có tiêu chí nào — đã đạt hoặc không được cấu hình.)")

    if scores:
        print("- Phản hồi chi tiết:")
        for criterion, verdict in scores:
            print(f"  • {criterion} => {verdict}")

    if state.scene_summary:
        print("\n[Scene Summary]")
        print(state.scene_summary)

    persona_dialogue = state.event_summary.get("_last_persona_dialogue") or []
    if persona_dialogue:
        print("\n[Persona Dialogue]")
        for line in persona_dialogue:
            speaker = line.get("speaker", "NPC")
            content = line.get("content", "").strip()
            if content:
                print(f"- {speaker}: {content}")

    if state.ai_reply:
        print("\n[AI Facilitator]")
        print(state.ai_reply)

    if state.policy_flags:
        print("\n[Policy Flags]")
        for flag in state.policy_flags:
            policy_id = flag.get("policy_id", "policy")
            policy_text = flag.get("policy_text", "")
            print(f"- {policy_id}: {policy_text}")


def main() -> None:
    args = parse_args()
    logic_memory = LogicMemory.load(args.case_id)
    graph = build_case_study_graph(case_id=args.case_id, model_name=args.model)

    initial_event = args.event or logic_memory.first_event or "CE1"
    state = RuntimeState.initialize(
        logic_memory=logic_memory,
        start_event=initial_event,
        user_action=args.user_action,
    )

    state = invoke_graph_once(
        graph,
        state,
        reset_state=args.reset,
        start_event=args.event,
    )

    render_state(state)

    if args.user_action:
        return

    print(
        "\nNhập hành động của học viên (gõ 'quit' để kết thúc). "
        "Mỗi hành động sẽ tiếp tục tiến trình hiện tại."
    )

    while True:
        try:
            user_input = input("\n[Hành động] > ").strip()
        except EOFError:
            break

        if not user_input:
            continue
        if user_input.lower() in {"quit", "exit", "stop"}:
            break

        state.user_action = user_input
        state = invoke_graph_once(graph, state, reset_state=False)
        render_state(state)


if __name__ == "__main__":
    main()
