#!/usr/bin/env bash
# Download Qwen2.5-1.5B-Instruct GGUF into ToDeploy/models/
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p models
OUT="models/qwen2.5-1.5b-instruct-q4_k_m.gguf"
URL="https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf"
if [[ -f "$OUT" ]]; then
  echo "Already present: $OUT"
  exit 0
fi
echo "Downloading → $OUT"
if command -v wget >/dev/null; then
  wget -O "$OUT" "$URL"
elif command -v curl >/dev/null; then
  curl -L -o "$OUT" "$URL"
else
  echo "Need wget or curl" >&2
  exit 1
fi
echo "Done. export LLM_MODEL_PATH=$PWD/$OUT"
