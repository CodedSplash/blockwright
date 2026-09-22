# Third-party notices

blockwright itself is released under the [MIT license](LICENSE). The repository
and the prebuilt binaries also carry the components below, each under its own
license.

| Component | Where | License |
|-----------|-------|---------|
| [py-tree-sitter](https://github.com/tree-sitter/py-tree-sitter) | `vendor/<platform>/cpXY/tree_sitter`, binaries | MIT |
| [tree-sitter-c](https://github.com/tree-sitter/tree-sitter-c) | `vendor/<platform>/common/tree_sitter_c`, binaries | MIT |
| [tree-sitter-cpp](https://github.com/tree-sitter/tree-sitter-cpp) | `vendor/<platform>/common/tree_sitter_cpp`, binaries | MIT |
| [libavoid-js](https://github.com/Aksem/libavoid-js) 0.5.0-beta.5, a WebAssembly build of libavoid from [Adaptagrams](https://github.com/mjwybrow/adaptagrams) | `vendor/web/libavoid`, inlined into every generated `index.html`, binaries | LGPL-2.1-or-later |
| [CPython](https://www.python.org) | binaries only | Python Software Foundation License Version 2 |
| [PyInstaller](https://pyinstaller.org) bootloader | binaries only | GPL-2.0-or-later with the bootloader exception |

## libavoid-js

libavoid-js is used as a separate module and can be replaced: `libavoid.wasm` is
unmodified from the npm package, and `libavoid.js` differs from the package's
`dist/index.js` only in how it is loaded (a classic script instead of an ES
module), as described in [vendor/web/libavoid/README.md](vendor/web/libavoid/README.md).
`python tools/vendor.py --web` fetches the package again and verifies its
checksum. The full license text is in
[vendor/web/libavoid/LICENSE](vendor/web/libavoid/LICENSE).

## CPython and PyInstaller

The single-file binaries bundle a CPython interpreter, covered by the
[PSF License Agreement](https://docs.python.org/3/license.html), and the
PyInstaller bootloader, whose
[license](https://github.com/pyinstaller/pyinstaller/blob/develop/COPYING.txt)
allows distributing it with programs under any license.

## MIT license texts

### py-tree-sitter

Copyright (c) 2019 Max Brunsfeld, GitHub

### tree-sitter-c, tree-sitter-cpp

Copyright (c) 2014 Max Brunsfeld

The following terms apply to each of the MIT-licensed components above:

```text
The MIT License (MIT)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
