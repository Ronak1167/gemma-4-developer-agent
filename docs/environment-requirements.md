# Gemma 4 Developer Agent — Environment Requirements

## Kaggle Notebook Runtime

| Component | Value | Source |
|---|---|---|
| Python | 3.13 (sandbox) | HARNESS_README.md |
| GPU | 2× NVIDIA Tesla T4 (16 GB each) | Kaggle accelerator |
| Docker image | `swebench-sandbox:latest` (or competition-specific) | To verify |
| Network (sandbox) | ISOLATED (`network_mode: none`) | HARNESS_README.md |
| `/wheels/` | Pre-compiled offline wheels (read-only mount) | HARNESS_README.md |
| pytest timeout | ~300 seconds per task | Community reports |
| Total runtime budget | ~12 hours | Community reports |

## Python Packages — Kaggle Environment

```
# Core Harness
google-adk          # adk-python — exact version: TBD from dataset requirements.txt
vllm                # OR llama-cpp-python for model serving

# Model Inference
torch               # GPU inference
transformers        # Gemma tokenizer
peft                # Optional: LoRA adapter loading

# Data
networkx            # Code graph traversal
numpy               # Embedding arrays
pandas              # submission.parquet
pyarrow             # Parquet I/O

# Evaluation (pre-installed in sandbox)
pytest
git
```

## Python Packages — Local Development (Windows)

```
# requirements-local.txt

# Data analysis
pandas>=2.0
pyarrow>=14.0
networkx>=3.0
numpy>=1.24
matplotlib>=3.7
seaborn>=0.12

# YAML tooling
pyyaml>=6.0

# Task file reading
jsonlines>=3.1

# Optional: local model testing (E2B only if GPU available)
# torch>=2.0
# transformers>=4.40
# bitsandbytes  # quantization
```

## Installation (Local)

```powershell
# Windows PowerShell
cd C:\Users\Ronak Jain\.gemini\antigravity\scratch\gemma4-agent

python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install --upgrade pip
pip install pandas pyarrow networkx numpy matplotlib seaborn pyyaml jsonlines
```

## Git Configuration (Windows — Critical for Patches)

```bash
# MUST configure to avoid CRLF in generated patches
git config --global core.autocrlf false
git config --global core.eol lf
```

## Kaggle CLI Setup

```bash
pip install kaggle

# Place kaggle.json at:  C:\Users\Ronak Jain\.kaggle\kaggle.json
# Format: {"username": "...", "key": "..."}

# Verify
kaggle competitions list --search gemma
```

## Known Version Pinning Risks

| Package | Risk | Mitigation |
|---|---|---|
| `adk-python` | Breaking changes in continuation/session handling | Pin to exact version from competition dataset |
| `pytest` | Python 3.13 compatibility gaps | Use competition-specified version |
| `pydantic` v1 vs v2 | Some repos use v1 APIs | Offline wheelhouse handles per-repo |
| `torch` | CUDA version mismatch with T4 | Use Kaggle pre-installed version |
| `bitsandbytes` | Windows support limited | Do NOT use for local dev on Windows |

