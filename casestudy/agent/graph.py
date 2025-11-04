from __future__ import annotations

from typing import Optional

from langgraph.graph import END, StateGraph

from .chains import (
    create_action_evaluator_chain,
    create_chat_model,
    create_persona_digest_chain,
    create_persona_dialogue_chain,
    create_policy_lookup_chain,
    create_responder_chain,
    create_scene_summary_chain,
)
from .const import DEFAULT_CASE_ID
from .memory import LogicMemory
from .nodes import (
    build_action_node,
    build_egress_node,
    build_ingress_node,
    build_persona_dialogue_node,
    build_policy_node,
    build_responder_node,
    build_semantic_node,
    build_state_update_node,
    build_transition_node,
)
from .runtime_store import RuntimeStateStore
from .state import RuntimeState
from ..utils.semantic_extract import load_indices


class CaseStudyGraphBuilder:
    """
    Assemble the LangGraph flow from modular chain and node components.
    """

    def __init__(
        self,
        case_id: str = DEFAULT_CASE_ID,
        *,
        model_name: Optional[str] = None,
        llm=None,
    ) -> None:
        self.case_id = case_id
        self.logic_memory = LogicMemory.load(case_id)
        self.state_store = RuntimeStateStore(case_id)
        self.llm = llm or create_chat_model(model_name)

        try:
            scene_index, persona_index, policy_index = load_indices()
        except Exception as exc:
            raise RuntimeError(
                "Không thể tải Semantic Memory. Hãy chạy build_indices() trước."
            ) from exc

        self.scene_chain = create_scene_summary_chain(
            scene_index.as_retriever(search_kwargs={"k": 4}),
            self.llm,
            case_id=case_id,
        )
        self.persona_chain = create_persona_digest_chain(
            persona_index,
            self.llm,
            case_id=case_id,
        )
        self.persona_dialogue_chain = create_persona_dialogue_chain(
            self.llm,
            case_id=case_id,
        )
        self.policy_chain = create_policy_lookup_chain(policy_index)
        self.action_chain = create_action_evaluator_chain(llm=self.llm)
        self.responder_chain = create_responder_chain(self.llm, case_id=case_id)

    def build(self) -> StateGraph:
        graph = StateGraph(RuntimeState)

        default_event = self.logic_memory.first_event or "CE1"

        graph.add_node(
            "ingress",
            build_ingress_node(
                self.state_store,
                self.logic_memory,
                default_event=default_event,
            ),
        )
        graph.add_node(
            "semantic",
            build_semantic_node(
                self.logic_memory, self.scene_chain, self.persona_chain
            ),
        )
        graph.add_node(
            "persona",
            build_persona_dialogue_node(self.logic_memory, self.persona_dialogue_chain),
        )
        graph.add_node("policy", build_policy_node(self.policy_chain))
        graph.add_node(
            "action",
            build_action_node(self.logic_memory, self.action_chain),
        )
        graph.add_node(
            "transition",
            build_transition_node(self.logic_memory),
        )
        graph.add_node(
            "responder",
            build_responder_node(self.logic_memory, self.responder_chain),
        )
        graph.add_node("state_update", build_state_update_node())
        graph.add_node("egress", build_egress_node(self.state_store))

        graph.set_entry_point("ingress")
        graph.add_edge("ingress", "semantic")
        graph.add_edge("semantic", "persona")
        graph.add_edge("persona", "policy")
        graph.add_edge("policy", "action")
        graph.add_edge("action", "transition")
        graph.add_edge("transition", "responder")
        graph.add_edge("responder", "state_update")
        graph.add_edge("state_update", "egress")
        graph.add_edge("egress", END)

        return graph

    def compile(self):
        return self.build().compile()


def build_case_study_graph(
    case_id: str = DEFAULT_CASE_ID,
    *,
    model_name: Optional[str] = None,
    llm=None,
):
    builder = CaseStudyGraphBuilder(case_id=case_id, model_name=model_name, llm=llm)
    return builder.compile()
