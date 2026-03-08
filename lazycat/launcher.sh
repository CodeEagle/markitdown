#!/bin/sh
set -eu

mode="${1:-mcp}"

if [ "$#" -gt 0 ]; then
  shift
fi

case "$mode" in
  mcp)
    exec markitdown-mcp "$@"
    ;;
  web)
    exec python /app/lazycat/markitdown_web.py "$@"
    ;;
  *)
    exec "$mode" "$@"
    ;;
esac
