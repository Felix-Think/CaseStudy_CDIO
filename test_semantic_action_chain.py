# file: demo_success_eval.py
from __future__ import annotations

import json

from casestudy.agent.chains.action import create_action_evaluator_chain
from casestudy.agent.chains.base import create_chat_model  # builds ChatOpenAI


def main() -> None:
    llm = create_chat_model(model_name="gpt-4o-mini")  # or whichever OpenAI model you prefer
    evaluate = create_action_evaluator_chain(llm=llm)

    payload = {
        "user_action": "Nhân viên cứu hộ hãy gọi ngay 115, yêu cầu mang theo AED và túi sơ cứu, báo địa chỉ hiện trường là số 123 Đường Lê Lợi, quận 1, TP.HCM. Nạn nhân bất tỉnh, không thở được.",
        "success_criteria": [
            "Kêu gọi ai gọi 115",
            "Yêu cầu mang AED hoặc túi sơ cứu đến hiện trường",
            "Báo tọa độ/địa chỉ và mô tả nạn nhân ngắn gọn",
        ],
    }

    result = evaluate(payload)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
