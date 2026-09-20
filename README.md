<div align="center">

<img src="docs/banner.png" width="840" alt="blockwright — flowcharts from C/C++ source code">

<p>
  <strong>Turn C and C++ source code into GOST&nbsp;19.701-90 flowcharts.</strong><br>
  Vector SVG for your report — and a real diagram editor in the browser.
</p>

<p>
  <a href="https://github.com/CodedSplash/blockwright/actions/workflows/ci.yml"><img src="https://github.com/CodedSplash/blockwright/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <img src="https://img.shields.io/badge/license-MIT-0a7ea4?style=flat-square" alt="MIT license">
  <img src="https://img.shields.io/badge/python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux-546e7a?style=flat-square" alt="Windows and Linux">
  <img src="https://img.shields.io/badge/setup-not%20required-2ea44f?style=flat-square" alt="No setup required">
  <img src="https://img.shields.io/badge/parser-tree--sitter-ff7043?style=flat-square" alt="tree-sitter">
</p>

<p>
  <b>English</b> · <a href="README.ru.md">Русский</a>
</p>

<img src="docs/editor.png" width="880" alt="Browser editor with a generated flowchart">

</div>

---

## What it does

`blockwright` reads your sources, parses them with the real
[tree-sitter](https://tree-sitter.github.io) grammars for C and C++, and draws a
flowchart for every function it finds — as a standalone `.svg` and as an album
page you can actually edit.

> **Note on language.** Diagram labels and the interface are in Russian, because
> the tool targets GOST 19.701-90 — the flowchart standard used in Russian
> engineering coursework. The code, CLI and this documentation are in English.

## Highlights

- **It understands the language, not the text.** Classes, templates, namespaces,
  overloads, range-`for`, `switch` with fallthrough, `goto`, `try/catch` —
  handled through the actual syntax tree, never regular expressions.
- **Whole projects.** Directories are walked recursively, the language of every
  file is detected automatically, and a file that fails one grammar is retried
  with the other.
- **Readable block text.** `cout << "Score #" << i << ": "` becomes
  `Вывод: Score #{i}:`, and `printf("Total: %d\n", s)` becomes `Вывод: Total: {s}`
  — string literals and values are woven into one sentence instead of a pile of
  quotes and commas.
- **A real editor, not a picture.** Drag blocks, reshape connectors, re-attach
  arrows, add shapes from a palette, draw a chart from scratch, undo, export.
- **Report ready.** SVG drops into Word as vector, PNG goes straight to the
  clipboard, every diagram is captioned `Рисунок N — …`.
- **Figma friendly.** Arrows are real polygons and shapes sit in named groups,
  so the SVG opens as a clean layer tree instead of anonymous paths.
- **Portable.** Copy the folder and run it — parsers ship with the repository.
  Or build a single executable for Windows and Linux.

<div align="center">
  <img src="docs/example-switch.png" width="620" alt="Generated flowchart for a switch statement">
</div>

## Quick start

```bash
git clone https://github.com/CodedSplash/blockwright.git
cd blockwright
python -m blockwright examples --open
```

Python 3.10+ is the only requirement — parsers are bundled, nothing to install.

| Platform | Launcher |
|----------|----------|
| Windows  | double-click `blockwright.bat` |
| Linux / macOS | `chmod +x blockwright.sh` once, then `./blockwright.sh` |

Output lands in a `блок-схемы` folder next to the sources:

```
блок-схемы/
├── index.html           album + editor with every diagram
├── grades__main.svg     one file per function
├── grades__verdict.svg
└── grades__average.svg
```

## Interactive picker

Run it with no arguments and you get a file navigator in the terminal: `→` enters
a folder, `←` goes up, `Space` marks a file — or a whole folder, recursively. The
function list on the right updates as you go, and any function can be switched
off. Mouse and keyboard both work.

```text
  Блок-схемы C / C++   ·   выбор исходников
 Папка: ~/projects/blockwright                     отмечено файлов: 1

 ФАЙЛЫ И ПАПКИ                     ФУНКЦИИ  3 из 3
 ❯ ↑ ..  на уровень выше           ❯ ◉ verdict            grades.cpp:12
   ▸ examples/  1/1                  ◉ average            grades.cpp:29
   ▸ docs/      0/0                  ◉ main               grades.cpp:38

╭── Настройки ──────────────────────────────────────────────────────────╮
│ f цикл for ........ как в коде      w ширина текста ... 38            │
│ i ввод-вывод ...... связной фразой  p растр PNG ....... не делать     │
│ r return .......... авто            s префикс std:: ... убирать       │
╰───────────────────────────────────────────────────────────────────────╯
 ↑↓ выбор  Space отметить  → в папку  ← наверх  Tab панель  a/n все/снять
 / поиск  Enter ПОСТРОИТЬ  q выход
```

Settings toggle with single letters and are remembered between runs.

## Command line

```bash
python -m blockwright "Lab 1"                      # one folder
python -m blockwright . -o out --open              # whole tree, open the album
python -m blockwright . --only main --only *Queue* # pick functions by pattern
python -m blockwright . --png 3                    # also render raster at ×3
python -m blockwright . --list                     # just list what was found
```

<details>
<summary><b>All options</b></summary>

| Option | Meaning |
|--------|---------|
| `-o, --out DIR` | where to write the result |
| `--only PATTERN`, `--exclude PATTERN` | filter functions by name (repeatable) |
| `--lang {auto,c,cpp}` | force the grammar |
| `--for-style {auto,hexagon,decision}` | how `for` loops are drawn |
| `--io-style {pretty,list,code}` | text inside I/O blocks |
| `--return-style {auto,value,end}` | how `return` is labelled |
| `--png [SCALE]` | also save `.png` (default ×2, needs Chrome or Edge) |
| `--keep-std` | keep the `std::` prefix |
| `--width N` | characters per line inside a block (default 38) |
| `--plain-begin` | write “Начало” instead of the function signature |
| `-i, --interactive` | open the picker even when a path is given |
| `--no-ui` | never open the picker (for scripts and CI) |
| `--no-svg`, `--no-html` | skip individual files / the album |
| `--no-recursive` | do not descend into subfolders |
| `--list` | list functions and exit |
| `-q, --quiet` | less output |

</details>

## The editor

`index.html` is not an image — the model of every diagram is embedded in the
page and the browser redraws it with the same algorithm the Python side uses.

- Blocks drag, handles resize them. **Connectors stay attached**: an endpoint
  travels with its own block, always meets it along the side normal, and never
  tears off the block at the other end.
- Clicking a connector reveals its nodes — drag them, add new ones, or drop an
  endpoint onto another block to re-attach it. *Reroute* rebuilds the path.
- Palette on the left: **Select** (V), **Connector** (C), **Label** (T) and the
  seven GOST block types (keys `1`–`7`).
- `Ctrl+Z` / `Ctrl+Shift+Z`, `Ctrl+D`, `Del`, arrow keys to nudge, `Alt` to
  ignore the grid, `Shift` to extend the selection.
- **＋** starts an empty chart, so you can draw an algorithm that has no code yet.
- **Проект…** exports every edit and custom chart as one `.json`; **Открыть**
  loads it back. Edits live in the browser and never touch your files.

## How code maps to blocks

| Construct | Block |
|-----------|-------|
| function entry | terminator with the signature (`Начало` for `main`) |
| expression, assignment, declaration | process |
| `cout <<`, `cin >>`, `printf`, `scanf`, `getline` | input/output parallelogram |
| call to a function from the same project | predefined process |
| `if / else`, `else if` | decision with `Да` / `Нет` branches |
| `switch` | decision with one column per `case`, fallthrough drawn explicitly |
| counting `for` | preparation hexagon: `i = 0, n - 1` |
| general `for` | init block + decision + step block |
| `for (auto x : v)` | preparation hexagon “для каждого x из v” |
| `while`, `do … while` | decision with a feedback line |
| `break`, `continue` | line to the loop exit / to the condition |
| `return` | terminator `Возврат …` or `Конец` |
| `goto`, label | on-page connector |
| `throw`, `try / catch` | terminator `Исключение: …`, decision for the handler |

<div align="center">
  <img src="docs/example-main.png" width="430" alt="Generated flowchart for main()">
</div>

## Standalone executable

```bash
pip install pyinstaller
python build.py
```

Produces `dist/blockwright.exe` (Windows, ~9 MB) or `dist/blockwright` (Linux),
with Python and the parsers inside — copy it anywhere and run. Build on the
system you are targeting; WSL works for the Linux binary.

## Project layout

```text
blockwright/
├── __main__.py     entry point, activates the bundled parsers
├── parse.py        file discovery, grammar choice, function extraction
├── build.py        syntax tree  →  intermediate representation
├── model.py        IR structures
├── layout.py       structural layout: coordinates of shapes and lines
├── render.py       SVG output and the model handed to the editor
├── album.py        the whole browser album/editor
├── tui.py          terminal picker
├── png.py          raster export via headless Chrome/Edge
└── text.py         text wrapping and measurement
tools/vendor.py     rebuild the bundled parsers
build.py            single-file build
```

## How it works

Layout is **structural**: every construct places itself and returns a frame with
its entry on top and its exit at the bottom, both on the same vertical spine, so
blocks stack without overlaps. `break` and `continue` escape sideways through
free lanes and are closed by the loop that owns them.

The editor receives the model rather than a picture and renders it with the same
algorithm — the two outputs were diffed and agree to within 0.01 px, so editing a
block in the browser yields exactly the SVG a rebuild would produce.

## License

[MIT](LICENSE). The parsers under `vendor/` belong to the tree-sitter project and
are distributed under the same license.
