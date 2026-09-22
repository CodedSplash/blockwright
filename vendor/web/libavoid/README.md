# libavoid-js 0.5.0-beta.5

Orthogonal connector routing for the chart editor (index.html).

* Source: https://github.com/Aksem/libavoid-js, a WebAssembly port of libavoid
  from Adaptagrams (https://github.com/mjwybrow/adaptagrams).
* License: LGPL-2.1-or-later, see LICENSE next to this file.
* libavoid.wasm is unmodified from the npm package libavoid-js@0.5.0-beta.5.
* libavoid.js is dist/index.js of the same package turned from an ES module
  into a classic script: `import.meta.url` is replaced and a global
  `AvoidModule` factory is exposed instead of `export`, because modules do not
  load from a page opened as file://.

Rebuild with `python tools/vendor.py --web`.
