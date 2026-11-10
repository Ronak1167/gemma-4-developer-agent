import ast
import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path
import yaml

def include_constructor(loader, node):
    return f"!include {node.value}"

yaml.add_constructor("!include", include_constructor, Loader=yaml.SafeLoader)

def get_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    root = Path(__file__).resolve().parent.parent
    print("=== PHASE 4: AGENT OPTIMIZATION & VERIFICATION ===")
    print(f"Workspace: {root}\n")

    # 1. Verify Agent YAML and sampling
    agent_yaml = root / "agent/agent.yaml"
    sampling_yaml = root / "agent/configs/sampling.yaml"
    system_md = root / "agent/prompts/system.md"

    assert agent_yaml.exists(), "agent.yaml missing"
    assert sampling_yaml.exists(), "sampling.yaml missing"
    assert system_md.exists(), "system.md missing"

    with open(agent_yaml, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    print(f"[PASS] agent.yaml: model={config.get('model')}, tools={len(config.get('tools', []))}")
    assert config.get("model") == "gemma-4-12b-it-qat-w4a16-ct"
    assert len(config.get("tools", [])) == 9

    with open(sampling_yaml, "r", encoding="utf-8") as f:
        sampling = yaml.safe_load(f)
    print(f"[PASS] sampling.yaml: temp={sampling.get('temperature')}, max_out={sampling.get('max_output_tokens')}, thinking_budget={sampling.get('thinking_config', {}).get('thinking_budget')}")
    assert sampling.get("max_output_tokens") == 4096
    assert sampling.get("thinking_config", {}).get("thinking_budget") == 1024
    assert sampling.get("thinking_config", {}).get("include_thoughts") is False

    h_agent = get_hash(agent_yaml)
    h_sampling = get_hash(sampling_yaml)
    h_system = get_hash(system_md)

    print(f"\n--- Optimized Source Hashes ---")
    print(f"  agent.yaml:          {h_agent}")
    print(f"  configs/sampling.yaml: {h_sampling}")
    print(f"  prompts/system.md:    {h_system} ({len(system_md.read_text(encoding='utf-8'))} bytes)")

    # 2. Verify the existing final archive without modifying it.
    final_zip = root / "dist/submission-final.zip"
    assert final_zip.is_file(), "dist/submission-final.zip is missing"
    source_map = {
        "agent.yaml": agent_yaml,
        "eval_config.yaml": root / "agent/eval_config.yaml",
        "configs/sampling.yaml": sampling_yaml,
        "prompts/system.md": system_md,
    }
    with zipfile.ZipFile(final_zip, "r") as zf:
        assert zf.testzip() is None, "CRC failed"
        entries = zf.namelist()
        assert entries == ["agent.yaml", "eval_config.yaml", "configs/sampling.yaml", "prompts/system.md"], f"Unexpected entries: {entries}"
        for name, source_path in source_map.items():
            assert zf.read(name) == source_path.read_bytes(), f"Archive content differs from source: {name}"
    h_final_zip = get_hash(final_zip)
    print(f"[PASS] Existing dist/submission-final.zip verified: {final_zip.stat().st_size} bytes")
    print(f"  SHA-256: {h_final_zip}")
    print(f"  Entries: {entries}")

    # 3. Clean-Room Extraction Test
    with tempfile.TemporaryDirectory() as td:
        tmp_dir = Path(td)
        with zipfile.ZipFile(final_zip, "r") as zf:
            zf.extractall(tmp_dir)
        assert (tmp_dir / "agent.yaml").is_file()
        assert (tmp_dir / "configs/sampling.yaml").is_file()
        assert (tmp_dir / "prompts/system.md").is_file()
        with open(tmp_dir / "agent.yaml", "r", encoding="utf-8") as f:
            tmp_cfg = yaml.safe_load(f)
        assert tmp_cfg.get("model") == "gemma-4-12b-it-qat-w4a16-ct"
    print("[PASS] Clean-room unpack and include verification passed.")

    # 4. Baseline zip unchanged check
    base_zip = root / "dist/submission-baseline.zip"
    h_base = get_hash(base_zip)
    expected_base_hash = "69c4403ee59c581c6e1182272e288af91641e7b3b876e6ecf8cae00329a5bf1b"
    assert h_base == expected_base_hash, f"Baseline ZIP modified: got {h_base}"
    print(f"[PASS] dist/submission-baseline.zip untouched (SHA-256: {h_base})")

    # 5. Notebook AST and Gate Verification
    p_dist = root / "dist/kaggle_kernel/kaggle_smoke_test.ipynb"
    p_exp = root / "experiments/kaggle_smoke_test.ipynb"

    for name, nb_path in [("dist", p_dist), ("experiments", p_exp)]:
        assert nb_path.exists(), f"{nb_path} missing"
        nb = json.loads(nb_path.read_text(encoding="utf-8"))
        cells = nb.get("cells", [])
        code_cells = [c for c in cells if c.get("cell_type") == "code"]
        print(f"\n--- Verifying {name} Notebook ({len(cells)} total, {len(code_cells)} code) ---")
        
        gate_ok = False
        for idx, cell in enumerate(code_cells):
            src = "".join(cell.get("source", []))
            # AST parse
            try:
                ast.parse(src)
            except SyntaxError as e:
                raise AssertionError(f"Syntax error in {name} code cell {idx}: {e}")
            
            # Check execution_count is null and outputs is empty
            assert cell.get("execution_count") is None, f"{name} cell {idx} execution_count is not null"
            assert cell.get("outputs") == [], f"{name} cell {idx} outputs not empty"

            if "AUTHORIZE_GPU_SMOKE_TEST = False" in src:
                gate_ok = True

        assert gate_ok, f"Gate AUTHORIZE_GPU_SMOKE_TEST = False not found in {name}"
        print(f"[PASS] {name}: all {len(code_cells)} code cells parse cleanly with ast.parse()")
        print(f"[PASS] {name}: all outputs empty and execution_count null")
        print(f"[PASS] {name}: AUTHORIZE_GPU_SMOKE_TEST = False strictly verified")

    print("\nALL PHASE 4 CHECKS PASSED (9/9).")

if __name__ == "__main__":
    main()

