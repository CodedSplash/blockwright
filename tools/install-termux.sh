#!/bin/sh
# Install blockwright in Termux (Android).
#
#     pkg install git
#     git clone https://github.com/CodedSplash/blockwright
#     sh blockwright/tools/install-termux.sh
#
# There are no tree-sitter wheels for Termux, so the parsers are compiled on
# the device with clang; it takes a couple of minutes.
set -e

DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
BIN="${PREFIX:-/data/data/com.termux/files/usr}/bin"

if [ ! -d "$BIN" ]; then
    echo "Похоже, это не Termux: каталога $BIN нет." >&2
    echo "В обычном Linux используйте ./blockwright.sh" >&2
    exit 1
fi

echo "==> Ставлю Python и компилятор"
pkg install -y python clang

echo "==> Собираю парсеры tree-sitter (несколько минут)"
python -m pip install --upgrade pip wheel
python -m pip install -r "$DIR/requirements.txt"

echo "==> Проверяю"
cd "$DIR"
python -m blockwright examples -o "$HOME/blockwright-demo" --no-ui -q
echo "    схемы: $HOME/blockwright-demo"

echo "==> Делаю команду blockwright"
cat > "$BIN/blockwright" <<EOF
#!/bin/sh
cd "$DIR" && exec python -m blockwright "\$@"
EOF
chmod +x "$BIN/blockwright"

cat <<'EOF'

Готово. Теперь:

    blockwright                 выбор исходников прямо в консоли
    blockwright ~/storage/shared/projects/lab1
    blockwright . --ui-lang en --theme dark

Чтобы видеть файлы телефона, один раз выполните termux-setup-storage —
после этого папки доступны в ~/storage/shared.

Альбом index.html открывается кнопкой в конце работы (termux-open) и
полностью работает пальцем: перетаскивание блоков, правка, экспорт PNG.
EOF
