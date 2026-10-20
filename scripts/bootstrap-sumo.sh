#!/usr/bin/env bash
set -euo pipefail
project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
vault_root="${RIKISHI_VAULT_ROOT:-$(cd "$project_root/../../../.." && pwd)}"
mount_point="$(df -P "$vault_root" | awk 'END {print $NF}')"
if [[ "$mount_point" != "$vault_root" ]]; then
    printf 'GitVault must be mounted: %s\n' "$vault_root" >&2
    exit 1
fi
export RIKISHI_VAULT_ROOT="$vault_root"
export TMPDIR="$vault_root/Local/caches/rikishi/tmp"
export UV_CACHE_DIR="$vault_root/Local/caches/rikishi/uv"
export UV_PYTHON_INSTALL_DIR="$vault_root/Local/runtimes/uv-python"
export UV_LINK_MODE=copy
mkdir -p "$TMPDIR" "$UV_CACHE_DIR"
cd "$project_root"
exec uv run python scripts/runtime-bootstrap.py "$@"
