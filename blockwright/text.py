"""Работа с текстом внутри блоков: измерение и перенос строк.

Внутри блоков используется моноширинный шрифт — это даёт точное
измерение ширины текста (ширина символа = 0.6 * кегль) и, как следствие,
геометрически корректную вёрстку схемы без «наезда» текста на границы.
"""

import re

FONT_MONO = "Consolas, 'Cascadia Mono', 'DejaVu Sans Mono', 'Courier New', monospace"
FONT_UI = "Segoe UI, 'Noto Sans', Arial, sans-serif"

CHAR_RATIO = 0.6  # ширина глифа моноширинного шрифта относительно кегля


def text_width(s: str, size: float) -> float:
    return len(s) * size * CHAR_RATIO


def normalize(s: str) -> str:
    """Схлопывает переводы строк и лишние пробелы."""
    s = s.replace("\r", " ").replace("\n", " ").replace("\t", " ")
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\s*,\s*", ", ", s)
    return s.strip()


_SOFT_BREAK = re.compile(r"(?<=[,;])|(?<=\))(?=\s*[&|+\-*/%<>=?:])|(?<=[&|])(?=\s)")


def _hard_split(token: str, width: int):
    """Режет слишком длинный токен по «мягким» местам либо жёстко."""
    parts, cur = [], ""
    for piece in re.split(r"(?<=[,;.:_>])", token):
        if not piece:
            continue
        if cur and len(cur) + len(piece) > width:
            parts.append(cur)
            cur = piece
        else:
            cur += piece
    if cur:
        parts.append(cur)
    out = []
    for p in parts:
        while len(p) > width:
            out.append(p[:width])
            p = p[width:]
        if p:
            out.append(p)
    return out or [token]


def wrap_text(text: str, width: int):
    """Разбивает строку на несколько строк не длиннее `width` символов."""
    text = normalize(text)
    if not text:
        return [""]
    if len(text) <= width:
        return [text]
    words = text.split(" ")
    lines, cur = [], ""
    for w in words:
        if len(w) > width:
            if cur:
                lines.append(cur)
                cur = ""
            chunks = _hard_split(w, width)
            lines.extend(chunks[:-1])
            cur = chunks[-1]
            continue
        cand = w if not cur else cur + " " + w
        if len(cand) <= width:
            cur = cand
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def xml_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
