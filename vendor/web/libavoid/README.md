# libavoid-js 0.5.0-beta.5

Ортогональная трассировка линий для редактора схем (index.html).

* Исходники: https://github.com/Aksem/libavoid-js — порт libavoid из
  Adaptagrams (https://github.com/mjwybrow/adaptagrams) в WebAssembly.
* Лицензия: LGPL-2.1-or-later, текст — в файле LICENSE рядом.
* libavoid.wasm — без изменений из npm-пакета libavoid-js@0.5.0-beta.5.
* libavoid.js — dist/index.js того же пакета, переделанный из ES-модуля в
  обычный скрипт: `import.meta.url` заменён, вместо `export` выставлена
  глобальная фабрика `AvoidModule`. Иначе модуль не грузится со страницы,
  открытой как file://.

Пересобрать: `python tools/vendor.py --web`.
