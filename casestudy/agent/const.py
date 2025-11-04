from pathlib import Path

DEFAULT_CASE_ID = "drowning_pool_001"
DEFAULT_MODEL_NAME = "gpt-4o-mini"

LOGIC_MEMORY_DIRNAME = "logic_memory"
SEMANTIC_MEMORY_DIRNAME = "semantic_memory"
RUNTIME_STATE_DIRNAME = "runtime_state"
RUNTIME_STATE_FILENAME = "runtime_state.json"

CASESTUDY_ROOT = Path(__file__).resolve().parents[1]
AGENT_CASE_ROOT = CASESTUDY_ROOT / "agent" / "cases"


def get_case_dir(case_id: str = DEFAULT_CASE_ID) -> Path:
    return CASESTUDY_ROOT / "cases" / case_id


def get_logic_memory_dir(case_id: str = DEFAULT_CASE_ID) -> Path:
    return get_case_dir(case_id) / LOGIC_MEMORY_DIRNAME


def get_runtime_state_dir(case_id: str = DEFAULT_CASE_ID) -> Path:
    return AGENT_CASE_ROOT / case_id / RUNTIME_STATE_DIRNAME


def get_runtime_state_path(case_id: str = DEFAULT_CASE_ID) -> Path:
    return get_runtime_state_dir(case_id) / RUNTIME_STATE_FILENAME
