"""Apply pre-retry path discovery enhancements to kaggle_smoke_test.ipynb.

Ensures:
1. Cell 2 validates required wheels in candidates and fallback before selection.
2. Cell 2 uses resilient candidate paths for TASK_WHEELS_DIR.
3. Cell 3 uses resilient candidate paths and recursive fallback for DATA_DIR.
4. Cell 5 uses resilient recursive fallback for baseline submission files.
5. Cell 7 validates config.json and model.safetensors in candidates and fallback before selection.
6. Cell 8 hardens server cleanup in finally block.
7. AUTHORIZE_GPU_SMOKE_TEST remains strictly False.
"""

import json
from pathlib import Path


def patch_notebook():
    nb_path = Path("experiments/kaggle_smoke_test.ipynb")
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)

    cells = nb["cells"]

    # 1. Verify Cell 1 gate is False
    c1_source = "".join(cells[1]["source"])
    assert "AUTHORIZE_GPU_SMOKE_TEST = False" in c1_source, "Cell 1 gate is not False!"

    # 2. Patch Cell 2: Wheelhouse & Task Wheels discovery
    c2_code = '''# OFFLINE RUNTIME BOOTSTRAP: official competition wheelhouse (Python 3.12 image).
import glob, importlib, logging, os, shutil, subprocess, sys
from pathlib import Path
assert sys.version_info[:2] == (3, 12), f"Expected official Python 3.12 runtime, got {sys.version.split()[0]}. Refusing incompatible cp312 wheelhouse."
os.environ.update({'TRANSFORMERS_NO_TF':'1','TRANSFORMERS_NO_FLAX':'1','TRANSFORMERS_OFFLINE':'1','HF_HUB_OFFLINE':'1','HF_DATASETS_OFFLINE':'1','PIP_NO_INDEX':'1','VLLM_NO_USAGE_STATS':'1','VLLM_WORKER_MULTIPROC_METHOD':'spawn','VLLM_ENGINE_READY_TIMEOUT_S':'1200','VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS':'1','NCCL_DEBUG':'WARN','LITELLM_LOCAL_MODEL_COST_MAP':'True','LITELLM_TELEMETRY':'False','LITELLM_LOG':'WARNING','OPENAI_API_KEY':'EMPTY','LOCAL_API_KEY':'EMPTY','PYTORCH_CUDA_ALLOC_CONF':'expandable_segments:True','OTEL_SDK_DISABLED':'true','OTEL_PYTHON_DISABLED':'true'})
def configure_logging():
    for name in ('LiteLLM','LiteLLM Router','LiteLLM Proxy','litellm','httpx','httpcore','openai','urllib3','opentelemetry','opentelemetry.context'):
        lg=logging.getLogger(name); lg.setLevel(logging.WARNING)
        if 'litellm' in name.lower(): lg.propagate=False; lg.handlers.clear()
configure_logging()

required_wheels = {
    'vllm-0.19.1-cp38-abi3-manylinux_2_31_x86_64.whl',
    'swegemma-0.2.11-py3-none-any.whl',
    'adk_submission-0.2.13-py3-none-any.whl',
    'adk_eval_core-0.1.0-py3-none-any.whl',
}

def is_valid_wheelhouse(d: Path) -> bool:
    if not d.is_dir():
        return False
    available = {p.name for p in d.glob('*.whl')}
    return required_wheels <= available

CANDIDATE_WHEELHOUSE_DIRS = [
    Path('/kaggle/input/gemma-4-developer-agent-wheelhouse'),
    Path('/kaggle/input/datasets/metric/gemma-4-developer-agent-wheelhouse'),
    Path('/kaggle/input/metric/gemma-4-developer-agent-wheelhouse'),
]
WHEELHOUSE_DIR = None
for candidate in CANDIDATE_WHEELHOUSE_DIRS:
    if is_valid_wheelhouse(candidate):
        WHEELHOUSE_DIR = candidate
        break
if WHEELHOUSE_DIR is None and Path('/kaggle/input').is_dir():
    for match in Path('/kaggle/input').rglob('*wheelhouse*'):
        if is_valid_wheelhouse(match):
            WHEELHOUSE_DIR = match
            break

if WHEELHOUSE_DIR is None:
    available_mounts = [str(p) for p in Path('/kaggle/input').iterdir()] if Path('/kaggle/input').is_dir() else []
    raise AssertionError(
        f"Official wheelhouse dataset not mounted or missing required wheels {sorted(required_wheels)}. "
        f"Checked candidates: {CANDIDATE_WHEELHOUSE_DIRS}. Available mounts under /kaggle/input: {available_mounts}"
    )

print(f"Resolved official wheelhouse directory: {WHEELHOUSE_DIR}")
for pattern in ('/usr/local/lib/python*/dist-packages/*cutlass*.pth','/usr/local/lib/python*/site-packages/*cutlass*.pth'):
    for pth in glob.glob(pattern):
        try: os.unlink(pth)
        except OSError: pass
tmp_whl=Path('/tmp/wheelhouse'); tmp_whl.mkdir(parents=True,exist_ok=True)
for wheel in WHEELHOUSE_DIR.glob('*.whl'):
    if 'cutlass' in wheel.name.lower(): continue
    target_name=wheel.name.replace('cu128','+cu128') if ('cu128' in wheel.name and '+' not in wheel.name) else wheel.name
    target=tmp_whl/target_name
    if not target.exists():
        try: os.symlink(wheel,target)
        except OSError: shutil.copyfile(wheel,target)
wheels=sorted(str(p) for p in tmp_whl.glob('*.whl'))
assert wheels, 'No compatible wheels discovered.'
print(f'Installing {len(wheels)} offline wheels from {WHEELHOUSE_DIR}...')
subprocess.run([sys.executable,'-m','pip','install','-q','--no-deps','--force-reinstall',*wheels],check=True)
importlib.invalidate_caches(); configure_logging()
print('Official inference wheelhouse installation complete.')

# The SWE-Gemma subprocess sandbox inherits host site-packages and skips automatic
# dependency installation. Seed pytest into the host environment from competition wheels.
required_test_wheels = {
    'pytest-9.1.1-py3-none-any.whl',
    'pluggy-1.6.0-py3-none-any.whl',
    'iniconfig-2.3.0-py3-none-any.whl',
    'packaging-26.3-py3-none-any.whl',
    'pygments-2.21.0-py3-none-any.whl',
}

def is_valid_task_wheels(d: Path) -> bool:
    if not d.is_dir():
        return False
    available = {p.name for p in d.glob('*.whl')}
    return required_test_wheels <= available

CANDIDATE_TASK_WHEELS_DIRS = [
    Path('/kaggle/input/competitions/gemma-4-developer-agent/wheels'),
    Path('/kaggle/input/gemma-4-developer-agent/wheels'),
    Path('./starter/wheels'),
    Path('../starter/wheels'),
]
TASK_WHEELS_DIR = None
for candidate in CANDIDATE_TASK_WHEELS_DIRS:
    if is_valid_task_wheels(candidate):
        TASK_WHEELS_DIR = candidate
        break
if TASK_WHEELS_DIR is None and Path('/kaggle/input').is_dir():
    for match in Path('/kaggle/input').rglob('wheels'):
        if is_valid_task_wheels(match):
            TASK_WHEELS_DIR = match
            break

if TASK_WHEELS_DIR is None:
    available_mounts = [str(p) for p in Path('/kaggle/input').iterdir()] if Path('/kaggle/input').is_dir() else []
    raise AssertionError(
        f"Competition task wheel cache missing or missing required test wheels {sorted(required_test_wheels)}. "
        f"Checked candidates: {CANDIDATE_TASK_WHEELS_DIRS}. Available mounts: {available_mounts}"
    )

print(f"Resolved competition task wheels directory: {TASK_WHEELS_DIR}")
subprocess.run(
    [
        sys.executable, '-m', 'pip', 'install', '-q', '--no-index',
        f'--find-links={TASK_WHEELS_DIR}', 'pytest==9.1.1',
    ],
    check=True,
)
importlib.invalidate_caches()
import pytest
assert pytest.__version__ == '9.1.1', f'Expected pytest 9.1.1, got {pytest.__version__}'
print(f'Offline host test runner installed and verified: pytest {pytest.__version__}')
'''
    cells[2]["source"] = [line + "\n" for line in c2_code.strip().split("\n")]
    cells[2]["source"][-1] = cells[2]["source"][-1].rstrip("\n")

    # 3. Patch Cell 3: DATA_DIR candidate search + fallback
    c3_code = '''# 2. Resolving Competition Input Datasets & Artifacts
from pathlib import Path

def is_valid_data_dir(d: Path) -> bool:
    return d.is_dir() and (d / "tasks.jsonl").is_file() and (d / "snapshots").is_dir()

CANDIDATE_DATA_DIRS = [
    Path("/kaggle/input/competitions/gemma-4-developer-agent"),
    Path("/kaggle/input/gemma-4-developer-agent"),
    Path("./starter"),
    Path("../starter"),
]

DATA_DIR = None
for p in CANDIDATE_DATA_DIRS:
    if is_valid_data_dir(p):
        DATA_DIR = p
        break

if DATA_DIR is None and Path("/kaggle/input").is_dir():
    for match in Path("/kaggle/input").rglob("tasks.jsonl"):
        if is_valid_data_dir(match.parent):
            DATA_DIR = match.parent
            break

if DATA_DIR is None:
    available_mounts = [str(p) for p in Path("/kaggle/input").iterdir()] if Path("/kaggle/input").is_dir() else []
    raise AssertionError(
        f"Competition data directory not found in candidates: {CANDIDATE_DATA_DIRS}. "
        f"Available mounts under /kaggle/input: {available_mounts}"
    )

print(f"Found Competition Data Directory: {DATA_DIR}")

# Verify core competition directories
tasks_file = DATA_DIR / "tasks.jsonl"
wheels_dir = DATA_DIR / "wheels"
snapshots_dir = DATA_DIR / "snapshots"
graphs_dir = DATA_DIR / "graphs"
embeddings_dir = DATA_DIR / "embeddings"

print(f"  tasks.jsonl:    {tasks_file.exists()} ({tasks_file.stat().st_size if tasks_file.exists() else 0} bytes)")
print(f"  wheels dir:     {wheels_dir.exists()}")
print(f"  snapshots dir:  {snapshots_dir.exists()}")
print(f"  graphs dir:     {graphs_dir.exists()}")
print(f"  embeddings dir: {embeddings_dir.exists()}")
assert tasks_file.exists(), f"Missing tasks.jsonl at {tasks_file}"
assert snapshots_dir.exists(), f"Missing snapshots directory at {snapshots_dir}"
'''
    cells[3]["source"] = [line + "\n" for line in c3_code.strip().split("\n")]
    cells[3]["source"][-1] = cells[3]["source"][-1].rstrip("\n")

    # 4. Patch Cell 5: Staging baseline submission with fallback
    c5_source = "".join(cells[5]["source"])
    # In Cell 5, after CANDIDATE_DATASET_DIRS check, add recursive search if MOUNTED_DIR is None
    if "for match in Path(\"/kaggle/input\").rglob(\"agent.yaml\"):" not in c5_source:
        old_part = """    MOUNTED_DIR = next(
        (d for d in CANDIDATE_DATASET_DIRS if d.is_dir() and (d / "agent.yaml").is_file()),
        None,
    )
    assert MOUNTED_DIR is not None, ("""
        new_part = """    MOUNTED_DIR = next(
        (d for d in CANDIDATE_DATASET_DIRS if d.is_dir() and (d / "agent.yaml").is_file()),
        None,
    )
    if MOUNTED_DIR is None and Path("/kaggle/input").is_dir():
        for match in Path("/kaggle/input").rglob("agent.yaml"):
            if (match.parent / "configs" / "sampling.yaml").is_file():
                MOUNTED_DIR = match.parent
                break
    assert MOUNTED_DIR is not None, ("""
        assert old_part in c5_source, "Target block in Cell 5 not found!"
        c5_source = c5_source.replace(old_part, new_part)
        cells[5]["source"] = [line + "\n" for line in c5_source.strip().split("\n")]
        cells[5]["source"][-1] = cells[5]["source"][-1].rstrip("\n")

    # 5. Patch Cell 7: Model discovery with config.json and model.safetensors validation
    c7_source = "".join(cells[7]["source"])
    old_c7_model_block = """MODEL_NAME = "gemma-4-12b-it-qat-w4a16-ct"
CANDIDATE_MODEL_PATHS = [
    Path(f"/kaggle/input/models/google/gemma-4/other/{MODEL_NAME}/2"),
    Path(f"/kaggle/input/models/google/gemma-4/Other/{MODEL_NAME}/2"),
    Path(f"/kaggle/input/gemma-4/other/{MODEL_NAME}/2"),
    Path(f"/kaggle/input/gemma-4/Other/{MODEL_NAME}/2"),
]
MODEL_PATH = None
for candidate in CANDIDATE_MODEL_PATHS:
    if candidate.exists():
        MODEL_PATH = candidate
        break
if MODEL_PATH is None and Path("/kaggle/input").is_dir():
    for match in Path("/kaggle/input").rglob(f"*{MODEL_NAME}*"):
        if match.is_dir():
            MODEL_PATH = match
            break
assert MODEL_PATH is not None and MODEL_PATH.exists(), f"Attached Gemma 4 model input is missing in candidate paths for: {MODEL_NAME}" """

    new_c7_model_block = """MODEL_NAME = "gemma-4-12b-it-qat-w4a16-ct"

def is_valid_model_dir(d: Path) -> bool:
    return d.is_dir() and (d / "config.json").is_file() and ((d / "model.safetensors").is_file() or any(d.glob("*.safetensors")))

CANDIDATE_MODEL_PATHS = [
    Path(f"/kaggle/input/models/google/gemma-4/Other/{MODEL_NAME}/2"),
    Path(f"/kaggle/input/models/google/gemma-4/other/{MODEL_NAME}/2"),
    Path(f"/kaggle/input/models/google/gemma-4/Other/{MODEL_NAME}"),
    Path(f"/kaggle/input/models/google/gemma-4/other/{MODEL_NAME}"),
    Path(f"/kaggle/input/gemma-4/Other/{MODEL_NAME}/2"),
    Path(f"/kaggle/input/gemma-4/other/{MODEL_NAME}/2"),
    Path(f"/kaggle/input/gemma-4/Other/{MODEL_NAME}"),
    Path(f"/kaggle/input/gemma-4/other/{MODEL_NAME}"),
    Path(f"/kaggle/input/{MODEL_NAME}/2"),
    Path(f"/kaggle/input/{MODEL_NAME}"),
]
MODEL_PATH = None
for candidate in CANDIDATE_MODEL_PATHS:
    if is_valid_model_dir(candidate):
        MODEL_PATH = candidate
        break
if MODEL_PATH is None and Path("/kaggle/input").is_dir():
    for match in Path("/kaggle/input").rglob("config.json"):
        parent = match.parent
        if MODEL_NAME.lower() in str(parent).lower() and is_valid_model_dir(parent):
            MODEL_PATH = parent
            break

if MODEL_PATH is None:
    available_mounts = [str(p) for p in Path("/kaggle/input").iterdir()] if Path("/kaggle/input").is_dir() else []
    raise AssertionError(
        f"Attached Gemma 4 model input missing required files (config.json, model.safetensors) for: {MODEL_NAME}. "
        f"Checked candidates: {[str(c) for c in CANDIDATE_MODEL_PATHS]}. Available mounts under /kaggle/input: {available_mounts}"
    )

assert (MODEL_PATH / "config.json").is_file(), f"Missing config.json in {MODEL_PATH}"
print(f"Resolved verified Gemma 4 model directory: {MODEL_PATH}")"""

    # We match flexibly on the model block in Cell 7
    lines_c7 = c7_source.split("\n")
    start_idx = None
    end_idx = None
    for i, line in enumerate(lines_c7):
        if 'MODEL_NAME = "gemma-4-12b-it-qat-w4a16-ct"' in line:
            start_idx = i
        if start_idx is not None and "assert MODEL_PATH is not None" in line:
            end_idx = i + 1
            break
    assert start_idx is not None and end_idx is not None, "Could not find model block in Cell 7"
    lines_c7[start_idx:end_idx] = new_c7_model_block.split("\n")
    cells[7]["source"] = [l + "\n" for l in lines_c7]
    cells[7]["source"][-1] = cells[7]["source"][-1].rstrip("\n")

    # 6. Patch Cell 8: Robust finally cleanup
    c8_source = "".join(cells[8]["source"])
    old_cleanup = """finally:
    if server_instance is not None:
        server_instance.stop()
        print("[CLEANUP] vLLM server stopped.")"""
    new_cleanup = """finally:
    srv = globals().get("server_instance") or locals().get("server_instance")
    if srv is not None:
        try:
            srv.stop()
            print("[CLEANUP] vLLM server stopped.")
        except Exception as e:
            print(f"[CLEANUP ERROR] Error stopping vLLM server: {e}")"""
    assert old_cleanup in c8_source, "Target cleanup block in Cell 8 not found"
    c8_source = c8_source.replace(old_cleanup, new_cleanup)
    cells[8]["source"] = [l + "\n" for l in c8_source.strip().split("\n")]
    cells[8]["source"][-1] = cells[8]["source"][-1].rstrip("\n")

    # Write back to experiments and dist
    for dest in [
        Path("experiments/kaggle_smoke_test.ipynb"),
        Path("dist/kaggle_kernel/kaggle_smoke_test.ipynb"),
    ]:
        with open(dest, "w", encoding="utf-8") as out:
            json.dump(nb, out, indent=1)
        print(f"Successfully updated {dest}")

if __name__ == "__main__":
    patch_notebook()
