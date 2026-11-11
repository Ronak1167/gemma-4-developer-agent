import hashlib
import re
import stat
import tempfile
import zipfile
from pathlib import Path

import yaml


def include_constructor(loader, node):
    return f"!include {node.value}"


yaml.add_constructor("!include", include_constructor, Loader=yaml.SafeLoader)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main():
    root = Path(__file__).resolve().parent.parent
    archive = root / "dist" / "submission-final.zip"
    sources = {
        "agent.yaml": root / "agent" / "agent.yaml",
        "eval_config.yaml": root / "agent" / "eval_config.yaml",
        "configs/sampling.yaml": root / "agent" / "configs" / "sampling.yaml",
        "prompts/system.md": root / "agent" / "prompts" / "system.md",
    }
    expected_names = list(sources)
    assert archive.is_file(), f"Missing archive: {archive}"

    archive_bytes = archive.read_bytes()
    print("=== READ-ONLY FINAL SUBMISSION AUDIT ===")
    print(f"Archive size: {len(archive_bytes)} bytes")
    print(f"Archive SHA-256: {sha256(archive_bytes)}")

    with zipfile.ZipFile(archive, "r") as zf:
        infos = zf.infolist()
        names = [x.filename for x in infos]
        assert names == expected_names, f"Unexpected archive entries/order: {names}"
        assert len(names) == len(set(names)), "Duplicate archive entry detected"
        assert zf.testzip() is None, "ZIP CRC validation failed"
        total_size = 0
        for info in infos:
            path = Path(info.filename)
            assert not path.is_absolute() and ".." not in path.parts, f"Unsafe archive path: {info.filename}"
            mode = (info.external_attr >> 16) & 0xFFFF
            assert not stat.S_ISLNK(mode), f"Symlink entry is not allowed: {info.filename}"
            total_size += info.file_size
            expected = sources[info.filename].read_bytes()
            actual = zf.read(info.filename)
            assert actual == expected, f"Archive bytes do not match current source: {info.filename}"
            print(f"[PASS] {info.filename}: {len(actual)} bytes; SHA-256 {sha256(actual)}")
        assert total_size < 3 * 1024**3, f"Unpacked size exceeds 3 GiB: {total_size}"

        with tempfile.TemporaryDirectory() as td:
            zf.extractall(td)
            tmp = Path(td)
            cfg = yaml.safe_load((tmp / "agent.yaml").read_text(encoding="utf-8"))
            sampling = yaml.safe_load((tmp / "configs/sampling.yaml").read_text(encoding="utf-8"))
            assert cfg.get("name") == "gemma4_swe_agent"
            assert cfg.get("model") in ("gemma-4-31b-it-qat-w4a16-ct", "gemma-4-12b-it-qat-w4a16-ct")
            assert cfg.get("instruction") == "!include prompts/system.md"
            assert cfg.get("generate_content_config") == "!include configs/sampling.yaml"
            eval_cfg = yaml.safe_load((tmp / "eval_config.yaml").read_text(encoding="utf-8"))
            assert eval_cfg == {"evaluation": {"timeout_seconds": 300, "max_tool_calls": 28, "max_time_minutes": 5, "max_turns": 200}}
            tool_names = [str(x).split()[0] for x in cfg.get("tools", [])]
            expected_tools = [
                "run_command", "submit_patch", "get_status", "read_file", "edit_file",
                "write_file", "get_code_neighbors", "search_similar_code", "get_code_subgraph",
            ]
            assert tool_names == expected_tools, f"Unexpected tool declaration: {tool_names}"
            assert sampling.get("temperature") in (0.1, 0.2)
            assert sampling.get("top_p") == 0.95
            assert sampling.get("max_output_tokens") in (4096, 8192)
            thinking = sampling.get("thinking_config", {})
            assert thinking.get("thinking_budget") in (1024, 2048)
            assert thinking.get("include_thoughts") is False

            # Screen for high-confidence credential formats; generic words like 'token' are not secrets.
            scan_files = [tmp / "agent.yaml", tmp / "eval_config.yaml", tmp / "configs/sampling.yaml", tmp / "prompts/system.md"]
            patterns = [
                re.compile(r"ghp_[A-Za-z0-9]{20,}"),
                re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
                re.compile(r"AKIA[0-9A-Z]{16}"),
                re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
                re.compile(r"sk-[A-Za-z0-9]{24,}"),
            ]
            for path in scan_files:
                content = path.read_text(encoding="utf-8")
                for pattern in patterns:
                    assert not pattern.search(content), f"Possible credential detected in {path.name}: {pattern.pattern}"

    print(f"[PASS] Exact archive structure, CRC, safe paths, and {total_size} unpacked bytes")
    print("[PASS] Current source bytes exactly match archive contents")
    print("[PASS] ADK config, includes, model, nine tools, sampling, and official eval_config budgets")
    print("[PASS] High-confidence credential scan")
    print("No files were modified by this audit.")


if __name__ == "__main__":
    main()


