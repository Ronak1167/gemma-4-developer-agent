"""Pre-retry non-GPU path validation test suite.

Simulates Kaggle filesystem mount layouts and verifies that:
1. All supported Kaggle layouts are correctly discovered.
2. Incomplete or empty directories are strictly rejected.
3. Multiple candidates are prioritized in exact candidate preference order.
4. Ambiguous nested directory matches resolve to the directory containing actual artifacts.
5. Missing mounts produce clear, actionable error diagnostics.
"""

import os
import shutil
import tempfile
from pathlib import Path

REQUIRED_WHEELS = {
    "vllm-0.19.1-cp38-abi3-manylinux_2_31_x86_64.whl",
    "swegemma-0.2.11-py3-none-any.whl",
    "adk_submission-0.2.13-py3-none-any.whl",
    "adk_eval_core-0.1.0-py3-none-any.whl",
}

REQUIRED_TEST_WHEELS = {
    "pytest-9.1.1-py3-none-any.whl",
    "pluggy-1.6.0-py3-none-any.whl",
    "iniconfig-2.3.0-py3-none-any.whl",
    "packaging-26.3-py3-none-any.whl",
    "pygments-2.21.0-py3-none-any.whl",
}

REQUIRED_MODEL_FILES = {
    "config.json",
    "model.safetensors",
    "generation_config.json",
    "tokenizer.json",
    "tokenizer_config.json",
}

REQUIRED_SUBMISSION_FILES = {
    "agent.yaml",
    "configs/sampling.yaml",
    "prompts/system.md",
}


# --- Discovery Logic Functions (under audit) ---

def is_valid_wheelhouse(d: Path) -> bool:
    if not d.is_dir():
        return False
    available = {p.name for p in d.glob("*.whl")}
    return REQUIRED_WHEELS <= available


def resolve_wheelhouse_dir(input_root: Path) -> Path:
    candidates = [
        input_root / "gemma-4-developer-agent-wheelhouse",
        input_root / "datasets" / "metric" / "gemma-4-developer-agent-wheelhouse",
        input_root / "metric" / "gemma-4-developer-agent-wheelhouse",
    ]
    for c in candidates:
        if is_valid_wheelhouse(c):
            return c
    # Recursive fallback
    if input_root.is_dir():
        for match in input_root.rglob("*wheelhouse*"):
            if is_valid_wheelhouse(match):
                return match
    available = [p.name for p in input_root.iterdir()] if input_root.is_dir() else []
    raise AssertionError(
        f"Official wheelhouse dataset not mounted or missing required wheels {sorted(REQUIRED_WHEELS)}. "
        f"Checked candidates: {[str(c) for c in candidates]}. Available mounts under {input_root}: {available}"
    )


def is_valid_task_wheels(d: Path) -> bool:
    if not d.is_dir():
        return False
    available = {p.name for p in d.glob("*.whl")}
    return REQUIRED_TEST_WHEELS <= available


def resolve_task_wheels_dir(input_root: Path) -> Path:
    candidates = [
        input_root / "competitions" / "gemma-4-developer-agent" / "wheels",
        input_root / "gemma-4-developer-agent" / "wheels",
    ]
    for c in candidates:
        if is_valid_task_wheels(c):
            return c
    if input_root.is_dir():
        for match in input_root.rglob("wheels"):
            if is_valid_task_wheels(match):
                return match
    available = [p.name for p in input_root.iterdir()] if input_root.is_dir() else []
    raise AssertionError(
        f"Competition task wheels cache missing or incomplete. "
        f"Checked candidates: {[str(c) for c in candidates]}. Available mounts under {input_root}: {available}"
    )


def is_valid_model_dir(d: Path) -> bool:
    if not d.is_dir():
        return False
    return (d / "config.json").is_file() and (d / "model.safetensors").is_file()


def resolve_model_dir(input_root: Path, model_name: str) -> Path:
    candidates = [
        input_root / "models" / "google" / "gemma-4" / "Other" / model_name / "2",
        input_root / "models" / "google" / "gemma-4" / "other" / model_name / "2",
        input_root / "models" / "google" / "gemma-4" / "Other" / model_name,
        input_root / "models" / "google" / "gemma-4" / "other" / model_name,
        input_root / "gemma-4" / "Other" / model_name / "2",
        input_root / "gemma-4" / "other" / model_name / "2",
        input_root / "gemma-4" / "Other" / model_name,
        input_root / "gemma-4" / "other" / model_name,
        input_root / model_name / "2",
        input_root / model_name,
    ]
    for c in candidates:
        if is_valid_model_dir(c):
            return c
    if input_root.is_dir():
        for match in input_root.rglob("config.json"):
            parent = match.parent
            if model_name.lower() in str(parent).lower() and is_valid_model_dir(parent):
                return parent
    available = [p.name for p in input_root.iterdir()] if input_root.is_dir() else []
    raise AssertionError(
        f"Attached Gemma 4 model input is missing required files (config.json, model.safetensors) for: {model_name}. "
        f"Checked candidates: {[str(c) for c in candidates]}. Available mounts under {input_root}: {available}"
    )


def is_valid_competition_data(d: Path) -> bool:
    if not d.is_dir():
        return False
    return (d / "tasks.jsonl").is_file() and (d / "snapshots").is_dir()


def resolve_competition_data_dir(input_root: Path) -> Path:
    candidates = [
        input_root / "competitions" / "gemma-4-developer-agent",
        input_root / "gemma-4-developer-agent",
    ]
    for c in candidates:
        if is_valid_competition_data(c):
            return c
    if input_root.is_dir():
        for match in input_root.rglob("tasks.jsonl"):
            if is_valid_competition_data(match.parent):
                return match.parent
    available = [p.name for p in input_root.iterdir()] if input_root.is_dir() else []
    raise AssertionError(
        f"Competition data directory not found in: {[str(c) for c in candidates]}. "
        f"Available mounts under {input_root}: {available}"
    )


# --- Helper to populate mock trees ---

def create_mock_wheelhouse(path: Path, incomplete: bool = False):
    path.mkdir(parents=True, exist_ok=True)
    wheels = list(REQUIRED_WHEELS)
    if incomplete:
        wheels = wheels[:2]  # Missing required wheels
    for whl in wheels:
        (path / whl).write_bytes(b"mock_wheel")


def create_mock_task_wheels(path: Path, incomplete: bool = False):
    path.mkdir(parents=True, exist_ok=True)
    wheels = list(REQUIRED_TEST_WHEELS)
    if incomplete:
        wheels = wheels[:2]
    for whl in wheels:
        (path / whl).write_bytes(b"mock_wheel")


def create_mock_model(path: Path, incomplete: bool = False):
    path.mkdir(parents=True, exist_ok=True)
    files = list(REQUIRED_MODEL_FILES)
    if incomplete:
        files = ["README.md"]  # No config.json, no model.safetensors
    for fname in files:
        (path / fname).write_bytes(b"mock_content")


def create_mock_competition(path: Path, incomplete: bool = False):
    path.mkdir(parents=True, exist_ok=True)
    if not incomplete:
        (path / "tasks.jsonl").write_text("{\"instance_id\": \"rich_4077\"}\n", encoding="utf-8")
        (path / "snapshots").mkdir(parents=True, exist_ok=True)
        (path / "graphs").mkdir(parents=True, exist_ok=True)
        (path / "embeddings").mkdir(parents=True, exist_ok=True)
        (path / "wheels").mkdir(parents=True, exist_ok=True)
        create_mock_task_wheels(path / "wheels")


# --- Test Cases ---

def run_tests():
    test_results = []
    
    # TEST 1: User-kernel layout (standard /kaggle/input/<slug>)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # Setup standard user kernel paths
        whl_dir = root / "gemma-4-developer-agent-wheelhouse"
        comp_dir = root / "gemma-4-developer-agent"
        model_dir = root / "models" / "google" / "gemma-4" / "Other" / "gemma-4-12b-it-qat-w4a16-ct" / "2"
        
        create_mock_wheelhouse(whl_dir)
        create_mock_competition(comp_dir)
        create_mock_model(model_dir)
        
        # Verify discovery
        assert resolve_wheelhouse_dir(root) == whl_dir
        assert resolve_task_wheels_dir(root) == comp_dir / "wheels"
        assert resolve_competition_data_dir(root) == comp_dir
        assert resolve_model_dir(root, "gemma-4-12b-it-qat-w4a16-ct") == model_dir
        test_results.append(("Test 1: User-kernel standard layout", "PASS"))

    # TEST 2: Kaggle staff/creator layout (/kaggle/input/datasets/metric/..., /kaggle/input/competitions/...)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        whl_dir = root / "datasets" / "metric" / "gemma-4-developer-agent-wheelhouse"
        comp_dir = root / "competitions" / "gemma-4-developer-agent"
        model_dir = root / "models" / "google" / "gemma-4" / "other" / "gemma-4-12b-it-qat-w4a16-ct" / "2"
        
        create_mock_wheelhouse(whl_dir)
        create_mock_competition(comp_dir)
        create_mock_model(model_dir)
        
        assert resolve_wheelhouse_dir(root) == whl_dir
        assert resolve_task_wheels_dir(root) == comp_dir / "wheels"
        assert resolve_competition_data_dir(root) == comp_dir
        assert resolve_model_dir(root, "gemma-4-12b-it-qat-w4a16-ct") == model_dir
        test_results.append(("Test 2: Staff/creator mount layout", "PASS"))

    # TEST 3: Incomplete wheelhouse rejection
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        whl_dir = root / "gemma-4-developer-agent-wheelhouse"
        create_mock_wheelhouse(whl_dir, incomplete=True)
        try:
            resolve_wheelhouse_dir(root)
            test_results.append(("Test 3: Reject incomplete wheelhouse", "FAIL - Accepted incomplete wheelhouse"))
        except AssertionError as e:
            assert "Missing required wheels" in str(e) or "missing required wheels" in str(e)
            test_results.append(("Test 3: Reject incomplete wheelhouse", "PASS"))

    # TEST 4: Empty directory rejection
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        whl_dir = root / "gemma-4-developer-agent-wheelhouse"
        whl_dir.mkdir(parents=True)
        try:
            resolve_wheelhouse_dir(root)
            test_results.append(("Test 4: Reject empty wheelhouse directory", "FAIL - Accepted empty directory"))
        except AssertionError:
            test_results.append(("Test 4: Reject empty wheelhouse directory", "PASS"))

    # TEST 5: Candidate order preference (if both user layout and fallback exist, pick candidate 1)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        whl_1 = root / "gemma-4-developer-agent-wheelhouse"
        whl_2 = root / "datasets" / "metric" / "gemma-4-developer-agent-wheelhouse"
        create_mock_wheelhouse(whl_1)
        create_mock_wheelhouse(whl_2)
        assert resolve_wheelhouse_dir(root) == whl_1
        test_results.append(("Test 5: Candidate order preference", "PASS"))

    # TEST 6: Ambiguous parent model directory (parent matches MODEL_NAME but only child /2 has config.json)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        parent_dir = root / "models" / "google" / "gemma-4" / "Other" / "gemma-4-12b-it-qat-w4a16-ct"
        child_dir = parent_dir / "2"
        parent_dir.mkdir(parents=True)
        # Parent has NO config.json, child has config.json & safetensors
        create_mock_model(child_dir)
        resolved = resolve_model_dir(root, "gemma-4-12b-it-qat-w4a16-ct")
        assert resolved == child_dir, f"Resolved {resolved}, expected child {child_dir}"
        test_results.append(("Test 6: Ambiguous parent vs versioned child model", "PASS"))

    # TEST 7: Unversioned model mount (/kaggle/input/gemma-4-12b-it-qat-w4a16-ct with config.json)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        model_dir = root / "gemma-4-12b-it-qat-w4a16-ct"
        create_mock_model(model_dir)
        resolved = resolve_model_dir(root, "gemma-4-12b-it-qat-w4a16-ct")
        assert resolved == model_dir
        test_results.append(("Test 7: Unversioned flat model mount", "PASS"))

    # TEST 8: Missing model produces informative diagnostic listing mounts
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "unrelated_dataset").mkdir(parents=True)
        try:
            resolve_model_dir(root, "gemma-4-12b-it-qat-w4a16-ct")
            test_results.append(("Test 8: Missing model diagnostic", "FAIL - Did not raise"))
        except AssertionError as e:
            assert "unrelated_dataset" in str(e)
            test_results.append(("Test 8: Missing model diagnostic", "PASS"))

    # TEST 9: Nested arbitrary mount discovered via recursive fallback
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        nested_whl = root / "deeply" / "nested" / "path" / "gemma-4-developer-agent-wheelhouse"
        create_mock_wheelhouse(nested_whl)
        assert resolve_wheelhouse_dir(root) == nested_whl
        test_results.append(("Test 9: Deeply nested wheelhouse discovery via fallback", "PASS"))

    print("\n=== Pre-Retry Path Discovery Test Results ===")
    for name, status in test_results:
        print(f"[{status}] {name}")
    assert all(status == "PASS" for _, status in test_results), "One or more tests failed!"
    print("\nAll 9 non-GPU path discovery test cases PASSED!")

if __name__ == "__main__":
    run_tests()

