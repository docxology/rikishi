#!/usr/bin/env bash
export RIKISHI_ROOT="${RIKISHI_ROOT:-$PWD}"
export RIKISHI_VAULT_ROOT="${RIKISHI_VAULT_ROOT:-$(cd "${RIKISHI_ROOT}/../../../.." && pwd)}"
if [[ ! -d "${RIKISHI_VAULT_ROOT}/Username" ]] || ! mount | rg --fixed-strings --quiet -- " on ${RIKISHI_VAULT_ROOT} "; then
  printf '%s\n' 'GitVault is not mounted; refusing local replacement storage.' >&2
  if [[ "${BASH_SOURCE:-}" != "$0" ]]; then return 1; else exit 1; fi
fi
export RIKISHI_CACHE_ROOT="${RIKISHI_CACHE_ROOT:-${RIKISHI_VAULT_ROOT}/Local/caches/rikishi}"
export TMPDIR="${RIKISHI_CACHE_ROOT}/tmp"
export UV_CACHE_DIR="${RIKISHI_CACHE_ROOT}/uv"
export UV_PYTHON_INSTALL_DIR="${UV_PYTHON_INSTALL_DIR:-${RIKISHI_VAULT_ROOT}/Local/runtimes/uv-python}"
export UV_LINK_MODE=copy
export MPLCONFIGDIR="${RIKISHI_CACHE_ROOT}/matplotlib"
export XDG_CACHE_HOME="${RIKISHI_CACHE_ROOT}/xdg"
mkdir -p "$TMPDIR" "$UV_CACHE_DIR" "$MPLCONFIGDIR" "$XDG_CACHE_HOME"
