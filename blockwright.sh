#!/bin/sh
# blockwright launcher for Linux and macOS.
#   ./blockwright.sh          pick sources in the terminal
#   ./blockwright.sh <path>   build charts right away
DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

PY=""
for c in python3 python; do
    if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
done
if [ -z "$PY" ]; then
    echo "Не найден Python 3. Установите его: sudo apt install python3" >&2
    exit 1
fi

cd "$DIR" || exit 1
exec "$PY" -m blockwright "$@"
