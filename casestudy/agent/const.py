from pathlib import Path

DEFAULT_CASE_ID = "drowning_pool_001"
DEFAULT_MODEL_NAME = "gpt-4o-mini"

RUNTIME_STATE_DIRNAME = "runtime_state"
RUNTIME_STATE_FILENAME = "runtime_state.json"

CASESTUDY_ROOT = Path(__file__).resolve().parents[1]
AGENT_CASE_ROOT = CASESTUDY_ROOT / "agent" / "cases"


def get_runtime_state_dir(case_id: str = DEFAULT_CASE_ID) -> Path:
    """
    Thư mục lưu cache runtime state cho từng case/session.
    """
    return AGENT_CASE_ROOT / case_id / RUNTIME_STATE_DIRNAME


def get_runtime_state_path(case_id: str = DEFAULT_CASE_ID) -> Path:
    return get_runtime_state_dir(case_id) / RUNTIME_STATE_FILENAME