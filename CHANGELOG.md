# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project adheres to [Semantic Versioning](https://semver.org/).

## [1.3.0] — 2026-09-22

### Changed

- **Connectors in the editor are routed by libavoid** (Adaptagrams, the router
  behind Inkscape's connectors) instead of the hand-written code that bent,
  doubled back and tore off when blocks moved. Paths are orthogonal, go around
  blocks, meet each block square to its side and separate when they run side by
  side. A line that a block merely brushes keeps its course and detours locally;
  joints between line pieces follow the reroute; dragging a whole construct just
  moves its lines; and every drag is computed from the state at its start, so
  bringing a block back restores the original lines exactly.
- *Reroute* and the Connector tool let the router choose the sides (out of the
  bottom or a side, into the top or a side); decision exits keep their
  Yes/No sides.

### Added

- `vendor/web/libavoid`: libavoid-js 0.5.0-beta.5 as WebAssembly, inlined into
  `index.html` (≈ 0.7 MB), so the album stays a single offline file that works
  from `file://` on Windows, Linux and Android. The single-file binary carries it
  too. `python tools/vendor.py --web` fetches it again, verifying the checksum;
  Node.js is not needed. Without the folder, or in a browser without
  WebAssembly, the editor falls back to the old router.

### Fixed

- Moving a block no longer snaps a group apart: the block under the cursor
  snaps to the grid and the rest of the selection follows by the same offset.

## [1.2.0] — 2026-09-22

### Added

- **Binaries built by CI.** Tagging a release now builds `blockwright` on
  three targets in parallel — Windows x64, Linux x86-64 (glibc 2.35+) and
  Linux ARM64 — and attaches them to the GitHub release.
- **Android support through Termux.** `tools/install-termux.sh` installs
  Python and clang, compiles the tree-sitter parsers from source (no wheels
  exist for Android) and registers a `blockwright` command. The album opens
  through `termux-open`, and the editor works with touch.
- Every push also builds the single-file binary on Windows and Linux and runs
  it against the bundled example, so a broken build is caught immediately.

### Changed

- `tools/vendor.py` can fetch optional platforms on demand
  (`--only linux_aarch64`, `--only macos_arm64`) without bloating the repo.

## [1.1.0] — 2026-09-20

### Added

- **Light and dark theme** for the editor and the charts themselves. The
  browser palette matches `blockwright/render.py`, so the exported SVG and PNG
  look exactly like the canvas. Command line: `--theme {light,dark}`.
- **Russian and English interface** everywhere — album, terminal picker and the
  words drawn on the charts (`Начало`/`Begin`, `Вывод:`/`Output:`, `Да`/`Yes`).
  Switch with the RU/EN button, the `l` key in the picker or `--ui-lang`.
- **Rename any chart** from the toolbar (✎ or a double click on the name);
  the new name reaches the caption, the tree and the exported file name.
- **Title checkbox** next to the export buttons: turn it off to get a bare
  chart without the heading in the SVG/PNG.
- **Responsive layout**: on narrow screens the chart list collapses behind a
  ☰ button, the inspector floats over the canvas and the toolbar wraps.
- English demo `examples/grades.en.cpp` for building English charts.

### Changed

- The header no longer repeats “ГОСТ 19.701-90”; it shows the chart count.
- Preferences remembered between runs now include language and theme.

### Fixed

- The `default` branch of a `switch` is recognised by structure instead of the
  label text, so an English chart no longer grew an extra “else” lane.

## [1.0.0] — 2026-09-20

First public release.

### Added

- **Parsing.** C and C++ sources are read with the real tree-sitter grammars:
  classes, templates, namespaces, overloads, range-`for`, `switch` with
  fallthrough, `goto`, `try/catch`. Directories are walked recursively and the
  grammar for each file is chosen automatically.
- **Layout.** Structural placement — every construct positions itself and
  returns a frame with entry and exit on one vertical spine. `break` and
  `continue` escape through free side lanes and are closed by their own loop.
- **SVG output** in GOST 19.701-90 notation, with named layer groups and real
  polygon arrowheads so the file opens cleanly in Figma and Word.
- **Readable block text**: string literals and values are woven into one
  sentence, `printf` format specifiers are replaced by their arguments.
- **Browser album and editor**: drag blocks, edit connector nodes, re-attach
  arrows, shape palette, charts from scratch, undo/redo, SVG/PNG export,
  clipboard copy, printing, project export to JSON.
- **Terminal picker**: file navigator with recursive marking, live function
  list, settings that persist between runs; mouse and keyboard.
- **PNG export** through headless Chrome or Edge — no extra libraries.
- **Portable mode**: parsers for Windows x64 and Linux x86-64 (CPython
  3.10–3.14) ship with the repository, so no installation is required.
- **Single-file build** via PyInstaller for Windows and Linux.

[1.3.0]: https://github.com/CodedSplash/blockwright/releases/tag/v1.3.0
[1.2.0]: https://github.com/CodedSplash/blockwright/releases/tag/v1.2.0
[1.1.0]: https://github.com/CodedSplash/blockwright/releases/tag/v1.1.0
[1.0.0]: https://github.com/CodedSplash/blockwright/releases/tag/v1.0.0
