"""Командный интерфейс утилиты построения блок-схем."""

import argparse
import fnmatch
import json
import os
import re
import sys
import webbrowser
from dataclasses import dataclass

from . import __version__
from . import parse as P
from . import png as PNG
from .album import render_html
from .build import Builder
from .layout import layout_function
from .render import frame_to_dict, render_svg


@dataclass
class Opts:
    max_chars: int = 38
    keep_std: bool = False
    io_style: str = "pretty"       # pretty | list | code
    for_style: str = "auto"        # auto | hexagon | decision
    return_style: str = "auto"     # auto | value | end
    lang: str = "ru"               # язык подписей на схеме
    yes_label: str = "Да"
    no_label: str = "Нет"
    begin_label: str = "Начало"
    end_label: str = "Конец"
    default_label: str = "иначе"
    plain_begin: bool = False


CHART_WORDS = {
    "ru": {"yes": "Да", "no": "Нет", "begin": "Начало", "end": "Конец",
           "default": "иначе"},
    "en": {"yes": "Yes", "no": "No", "begin": "Begin", "end": "End",
           "default": "else"},
}


_BAD = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def rel_path(path, base):
    """Путь относительно базовой папки; на другом диске — как есть."""
    try:
        rel = os.path.relpath(path, base)
    except ValueError:                       # другой диск в Windows
        rel = path
    if rel.startswith(".." + os.sep) or rel.startswith("../"):
        rel = os.path.basename(path)
    return rel.replace("\\", "/")


def safe_name(s, limit=90):
    s = _BAD.sub("_", s).strip(" .")
    s = re.sub(r"\s+", "_", s)
    return s[:limit] or "diagram"


def build_parser():
    ap = argparse.ArgumentParser(
        prog="blockwright",
        description="Построение блок-схем (ГОСТ 19.701-90) по исходному коду C и C++. "
                    "Разбор кода выполняется парсерами tree-sitter.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Примеры:\n"
               "  python -m blockwright \"Лабораторная работа №1\"\n"
               "  python -m blockwright src -o out --only main --only *Queue*\n"
               "  python -m blockwright . --for-style decision --io-style code\n",
    )
    ap.add_argument("paths", nargs="*", default=[],
                    help="файлы или папки с исходниками; если не указать — "
                         "откроется интерактивный выбор в консоли")
    ap.add_argument("-i", "--interactive", action="store_true",
                    help="открыть интерактивный выбор, даже если путь указан")
    ap.add_argument("--no-ui", action="store_true",
                    help="не открывать интерактивный выбор (для скриптов)")
    ap.add_argument("-o", "--out", default=None,
                    help="папка для результата (по умолчанию <путь>/блок-схемы)")
    ap.add_argument("--only", action="append", default=[], metavar="ШАБЛОН",
                    help="строить только функции, подходящие под шаблон (можно повторять)")
    ap.add_argument("--exclude", action="append", default=[], metavar="ШАБЛОН",
                    help="пропустить функции по шаблону")
    ap.add_argument("--lang", choices=["auto", "c", "cpp"], default="auto",
                    help="принудительно задать язык (по умолчанию определяется сам)")
    ap.add_argument("--for-style", choices=["auto", "hexagon", "decision"], default="auto",
                    help="оформление for: шестиугольник «подготовка» или явные блоки")
    ap.add_argument("--io-style", choices=["pretty", "list", "natural", "code"],
                    default="pretty",
                    help="текст ввода-вывода: pretty — связная фраза «Вывод: Итого {n} шт.», "
                         "list — перечисление через запятую, code — исходный текст")
    ap.add_argument("--return-style", choices=["auto", "value", "end"], default="auto",
                    help="оформление return: auto — «Конец» для return без значения "
                         "и для return 0 в main, value — всегда «Возврат …», "
                         "end — всегда «Конец»")
    ap.add_argument("--theme", choices=["light", "dark"], default=None,
                    help="палитра схем и альбома: светлая или тёмная")
    ap.add_argument("--ui-lang", choices=["ru", "en"], default=None,
                    dest="ui_lang", help="язык интерфейса альбома и консоли")
    ap.add_argument("--keep-std", action="store_true",
                    help="не убирать префикс std:: из текста блоков")
    ap.add_argument("--width", type=int, default=38, metavar="N",
                    help="максимальная длина строки текста в блоке (по умолчанию 38)")
    ap.add_argument("--plain-begin", action="store_true",
                    help="в стартовом блоке писать «Начало» вместо сигнатуры функции")
    ap.add_argument("--list", action="store_true", dest="list_only",
                    help="только перечислить найденные функции, ничего не строить")
    ap.add_argument("--png", nargs="?", type=float, const=2.0, default=None,
                    metavar="МАСШТАБ",
                    help="дополнительно сохранить растровые .png (по умолчанию ×2); "
                         "нужен установленный Edge или Chrome")
    ap.add_argument("--no-svg", action="store_true", help="не сохранять отдельные .svg")
    ap.add_argument("--no-html", action="store_true", help="не собирать index.html")
    ap.add_argument("--no-recursive", action="store_true",
                    help="не заходить во вложенные папки")
    ap.add_argument("--open", action="store_true",
                    help="открыть готовый index.html в браузере")
    ap.add_argument("-q", "--quiet", action="store_true", help="меньше сообщений")
    ap.add_argument("-V", "--version", action="version",
                    version=f"blockwright {__version__}")
    return ap


def match_name(name, base, only, exclude):
    if only and not any(fnmatch.fnmatch(name, p) or fnmatch.fnmatch(base, p)
                        for p in only):
        return False
    if exclude and any(fnmatch.fnmatch(name, p) or fnmatch.fnmatch(base, p)
                       for p in exclude):
        return False
    return True


PREFS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     ".blockwright-prefs.json")


def load_prefs():
    try:
        with open(PREFS, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def save_prefs(cfg):
    keep = {k: cfg[k] for k in ("for_style", "io_style", "return_style",
                                "width", "png", "keep_std", "ui_lang",
                                "theme") if k in cfg}
    keep["root"] = cfg.get("root", "")
    try:
        with open(PREFS, "w", encoding="utf-8") as fh:
            json.dump(keep, fh, ensure_ascii=False, indent=1)
    except OSError:
        pass


def run_picker(args):
    """Интерактивный выбор; правит args на месте. False — отменено."""
    from . import tui
    prefs = load_prefs()
    start = args.paths[0] if args.paths else prefs.get("root") or os.getcwd()
    if not os.path.isdir(start):
        start = os.path.dirname(os.path.abspath(start)) or os.getcwd()
    cfg = {k: prefs[k] for k in tui.DEFAULTS if k in prefs}
    cfg.setdefault("ui_lang", args.ui_lang)
    res = tui.run(start, cfg)
    if res is None:
        return None
    if res is False:
        return False
    res["theme"] = args.theme
    save_prefs(res)
    args.paths = res["paths"]
    if res["only"]:
        args.only = res["only"]
    args.for_style = res["for_style"]
    args.io_style = res["io_style"]
    args.return_style = res["return_style"]
    args.width = res["width"]
    args.keep_std = res["keep_std"]
    args.png = float(res["png"]) if res["png"] else None
    args.ui_lang = res.get("ui_lang", args.ui_lang)
    args.open = True
    return True


def main(argv=None):
    args = build_parser().parse_args(argv)
    prefs = load_prefs()
    # ключ командной строки важнее запомненного выбора
    args.ui_lang = args.ui_lang or prefs.get("ui_lang") or "ru"
    args.theme = args.theme or prefs.get("theme") or "light"
    from_ui = False
    if not args.no_ui and not args.list_only and (args.interactive or not args.paths):
        state = run_picker(args)
        if state is False:
            return 0
        from_ui = state is True
        if state is None and not args.paths:
            print("Не указан путь. Пример: python -m blockwright \"Лабораторная работа №1\"",
                  file=sys.stderr)
            return 2
    paths = args.paths or ["."]
    io_style = "list" if args.io_style == "natural" else args.io_style
    words = CHART_WORDS.get(args.ui_lang, CHART_WORDS["ru"])
    opts = Opts(max_chars=max(16, args.width), keep_std=args.keep_std,
                io_style=io_style, for_style=args.for_style,
                return_style=args.return_style, plain_begin=args.plain_begin,
                lang=args.ui_lang, yes_label=words["yes"], no_label=words["no"],
                begin_label=words["begin"], end_label=words["end"],
                default_label=words["default"])

    files = P.discover(paths, recursive=not args.no_recursive)
    if not files:
        print("Исходные файлы (.c/.cpp/.h/.hpp) не найдены.", file=sys.stderr)
        return 2

    root = os.path.abspath(paths[0])
    if os.path.isfile(root):
        root = os.path.dirname(root)
    # общая папка всех найденных файлов — для коротких подписей в схемах
    base_dir = root
    try:
        common = os.path.commonpath(files)
        base_dir = common if os.path.isdir(common) else os.path.dirname(common)
    except ValueError:
        pass
    out_dir = os.path.abspath(args.out) if args.out else os.path.join(root, "блок-схемы")
    if not args.list_only:
        os.makedirs(out_dir, exist_ok=True)

    def log(*a):
        if not args.quiet:
            print(*a)

    # первый проход — собрать имена пользовательских функций во всём проекте
    parsed = []
    known = set()
    for path in files:
        try:
            with open(path, "rb") as fh:
                src = fh.read()
        except OSError as e:
            print(f"  ! {path}: {e}", file=sys.stderr)
            continue
        text = src.decode("utf-8", "replace")
        lang = P.guess_language(path, text, None if args.lang == "auto" else args.lang)
        tree, lang, errs = P.parse_source(src, lang)
        known |= P.collect_known_names(src, tree.root_node)
        parsed.append((path, src, tree, lang, errs))

    entries = []
    svg_files = []
    used = set()
    total_funcs = 0
    for path, src, tree, lang, errs in parsed:
        rel = rel_path(path, base_dir)
        if errs:
            log(f"  ~ {rel}: разобран с {errs} ошибочн. участк. "
                f"(схемы строятся по распознанной части)")
        builder = Builder(src, opts, known)
        funcs = P.collect_functions(src, tree.root_node)
        made = 0
        for node in funcs:
            info = P.describe_function(src, node)
            if not match_name(info["name"], info["base"], args.only, args.exclude):
                continue
            total_funcs += 1
            if args.list_only:
                print(f"{rel}:{info['line']}: {info['name']}  —  {info['signature']}")
                made += 1
                continue
            fn_body = builder.build_body(info["body"], is_main=info["base"] == "main")
            from .model import Function
            short = (opts.begin_label if info["base"] == "main" else info["short"])
            fn = Function(name=info["name"], signature=info["signature"],
                          short=short, file=path, rel=rel,
                          line=info["line"], lang=lang, body=fn_body)
            try:
                frame = layout_function(fn, opts)
            except Exception as e:                       # noqa: BLE001
                print(f"  ! {rel}:{fn.line} {fn.name}: ошибка разметки — {e}",
                      file=sys.stderr)
                continue
            title = f"{fn.name} — {rel}"
            stem = safe_name(f"{os.path.splitext(rel)[0].replace('/', '_')}__{fn.name}")
            uniq, k = stem, 2
            while uniq in used:
                uniq = f"{stem}_{k}"
                k += 1
            used.add(uniq)

            model = frame_to_dict(frame, opts)
            if not args.no_svg or args.png is not None:
                svg_path = os.path.join(out_dir, uniq + ".svg")
                with open(svg_path, "w", encoding="utf-8") as fh:
                    fh.write(render_svg(frame, title=title, standalone=True,
                                        name=fn.name, theme=args.theme))
                svg_files.append(svg_path)
            entries.append({
                "rel": rel, "name": fn.name, "signature": fn.signature,
                "line": fn.line, "anchor": safe_name(uniq).replace(" ", "_"),
                "model": model,
            })
            made += 1
        if not args.list_only:
            log(f"  {rel}: функций — {made} [{lang}]")

    if args.list_only:
        print(f"\nВсего функций: {total_funcs}")
        return 0

    if not entries:
        print("Не найдено ни одной функции, подходящей под условия.", file=sys.stderr)
        return 1

    if args.png is not None:
        browser = PNG.find_browser()
        if not browser:
            print("  ! PNG пропущен: не найден Edge или Chrome", file=sys.stderr)
        else:
            ok = 0
            for svg_path in svg_files:
                png_path = os.path.splitext(svg_path)[0] + ".png"
                if PNG.convert(svg_path, png_path, scale=args.png, browser=browser):
                    ok += 1
            log(f"  PNG ×{args.png:g}: {ok} из {len(svg_files)}")
            if args.no_svg:
                for svg_path in svg_files:
                    try:
                        os.remove(svg_path)
                    except OSError:
                        pass

    index = None
    if not args.no_html:
        index = os.path.join(out_dir, "index.html")
        folder = os.path.basename(base_dir) or base_dir
        head = "Flowcharts" if args.ui_lang == "en" else "Блок-схемы"
        with open(index, "w", encoding="utf-8") as fh:
            fh.write(render_html(entries, title=f"{head}: {folder}", folder=folder,
                                 lang=args.ui_lang, theme=args.theme))

    log(f"\nГотово: {len(entries)} блок-схем -> {out_dir}")
    if index:
        log(f"Альбом схем: {index}")
        if args.open:
            webbrowser.open("file:///" + os.path.abspath(index).replace("\\", "/"))
    if from_ui:
        from . import tui
        tui.pause("Альбом открыт в браузере. Нажмите любую клавишу, чтобы закрыть…")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
