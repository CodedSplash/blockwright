#!/bin/sh
# blockwright — блок-схемы по коду C/C++ (Linux, macOS).
#   ./blockwright.sh          -> выбор исходников в консоли
#   ./blockwright.sh <путь>   -> сразу построить схемы
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
