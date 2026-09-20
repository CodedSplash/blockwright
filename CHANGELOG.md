# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project adheres to [Semantic Versioning](https://semver.org/).

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

[1.0.0]: https://github.com/CodedSplash/blockwright/releases/tag/v1.0.0
