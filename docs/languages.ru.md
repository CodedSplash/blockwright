# Описание языка

[English](languages.md) · **Русский**

blockwright не знает ни одного языка программирования «из коробки». Всё, что
отличает C от Python или Pascal, лежит в **описании языка** — TOML-файле в
`blockwright/languages/`. Описание называет грамматику
[tree-sitter](https://tree-sitter.github.io/) и сопоставляет её узлы с
конструкциями блок-схемы: «`while_statement` — это цикл с предусловием,
условие в поле `condition`, тело в поле `body`». Остальное — разбор, раскладка
блоков, SVG, редактор — общее для всех языков.

Поэтому новый язык добавляется без правки кода: нужны грамматика и файл
описания. Для конструкций, которые таблицей не выразить, рядом с описанием
можно положить небольшой файл hooks на Python.

- [Что уже есть](#что-уже-есть)
- [Свой язык за пять шагов](#свой-язык-за-пять-шагов) — на примере Rust
- [Справочник по ключам](#справочник-по-ключам)
- [Границы подхода](#границы-подхода)

## Что уже есть

| Язык | Файл | Грамматика |
|------|------|-----------|
| C | `c.toml` | в комплекте |
| C++ | `cpp.toml` (на основе `c.toml`) | в комплекте |
| Python | `python.toml` | в комплекте |
| Java | `java.toml` | в комплекте |
| C# | `csharp.toml` | в комплекте |
| Go | `go.toml` | в комплекте |
| JavaScript | `javascript.toml` | в комплекте |
| Pascal | `pascal.toml` | `pip install tree-sitter-pascal` — грамматика под AGPL-3.0, поэтому не входит в комплект |

`python -m blockwright --langs` показывает все загруженные описания, их
расширения и то, установлена ли грамматика.

## Свой язык за пять шагов

Готовый результат этого раздела лежит в [`docs/example-rust/`](example-rust/):
описание, hooks и пример программы.

### 1. Найдите грамматику

Почти у каждого языка есть грамматика tree-sitter, обычно с колёсами на PyPI
под именем `tree-sitter-<язык>`:

```bash
pip install tree-sitter-rust
```

Модуль называется `tree_sitter_rust`, функция `language()` возвращает
грамматику. Если функция называется иначе (у TypeScript —
`language_typescript`), это указывается в описании.

### 2. Начните с трёх строк

```toml
# my-langs/rust.toml
name = "rust"
grammar = "tree_sitter_rust"
extensions = [".rs"]
```

Положите файл в любую папку и укажите её через `--lang-dir` (или в переменной
окружения `BLOCKWRIGHT_LANGS`, несколько папок через `;` в Windows и `:` в
Linux). Описание из такой папки заменяет встроенное с тем же `name`.

### 3. Посмотрите на дерево

```bash
python -m blockwright --lang-dir my-langs --tree main.rs
```

`--tree` печатает узлы с именами полей — это и есть словарь для описания:

```text
function_item
  name: identifier  «gcd»
  parameters: parameters
  body: block
    expression_statement
      while_expression
        condition: binary_expression
        body: block
          let_declaration
```

### 4. Сопоставьте узлы с конструкциями

```toml
[functions]
nodes = ["function_item"]          # что считать функцией; имя — в поле name
entry = ["main"]                   # у этой функции стартовый блок «Начало»

[statements]
block = "block"                    # просто последовательность операторов
expression_statement = "expression"
let_declaration = "simple"         # блок «процесс» с текстом узла
if_expression = { kind = "if", condition = "condition", then = "consequence", else = "alternative" }
else_clause = "block"
while_expression = { kind = "while", condition = "condition", body = "body" }
loop_expression = { kind = "while", body = "body" }      # без условия — «истина»
match_expression = { kind = "switch", value = "value", body = "body", default_labels = ["_"], cases = { match_arm = { labels = ["match_pattern"], body = "value" } } }
break_expression = "break"
continue_expression = "continue"
return_expression = "return"
```

Уже этого хватает для осмысленных схем. Узлы, которых нет в
`[statements]`, становятся блоками «процесс» со своим текстом, поэтому
описание можно наращивать постепенно.

### 5. Hooks для того, что не выражается таблицей

`println!("{} -> {}", i, f(i))` — макрос, и аргументы у него не разобраны
грамматикой: это сырые токены. Здесь нужен код:

```toml
hooks = "rust_hooks.py"

[statements]
macro_invocation = { hook = "macro" }
# сначала hook; если он вернёт None — обычный foreach
for_expression = { hook = "range_for", kind = "foreach", var = "pattern", iterable = "value", body = "body" }
```

```python
# rust_hooks.py
from blockwright import model as M

def macro(builder, node, rule):
    name = builder.t(builder.find(node, "macro"))
    if name == "println":
        ...
        return [M.Simple(M.IO, builder.L("out") + text)]
    return None        # остальные макросы — обычный блок «процесс»
```

Hook получает построитель, узел и правило. Он возвращает список элементов
схемы (`blockwright/model.py`) или `None`, если узел должно обработать правило.
У построителя есть всё нужное: `t(node)` (текст узла), `find(node, path)`,
`block(node)` и `stmt(node)` (построить вложенные операторы), `L(key)`
(слова на схеме), `counting_loop(var, start, end, step, body)`. Полный пример —
[`docs/example-rust/rust_hooks.py`](example-rust/rust_hooks.py).

Проверка:

```bash
pip install tree-sitter-rust
python -m blockwright --lang-dir docs/example-rust --lang rust docs/example-rust --open
```

> [!WARNING]
> Hooks — это код на Python, и он выполняется при загрузке описания.
> Подключайте через `--lang-dir` только папки, которым доверяете.

## Справочник по ключам

### Пути к узлам

Везде, где ключ указывает на часть узла (`condition = "condition"`), значение —
**путь**. Это один или несколько шагов через точку, каждый шаг:

- имя поля (`condition`, `body`);
- если поля с таким именем нет — тип дочернего узла (`for_clause`, `block`);
- `#N` — N-й именованный дочерний узел без поля (`#0` — первый).

Например, `for_clause.initializer` в Go: дочерний узел `for_clause`, у него
поле `initializer`.

### Верхний уровень

| Ключ | Смысл |
|------|-------|
| `name` | идентификатор языка для `--lang`; по умолчанию — имя файла |
| `title` | название для людей |
| `grammar` | модуль грамматики, `"tree_sitter_x"`, или `{ module = "…", function = "language_tsx" }` |
| `package` | имя пакета для подсказки `pip install` |
| `bundle` | `false` — не класть грамматику в `vendor/` и в бинарники |
| `extends` | имя описания, на котором строится это; таблицы сливаются по ключам, списки и значения заменяются |
| `extensions` | расширения файлов |
| `markers`, `priority` | выбор между языками с общим расширением (`.h`): у кого больше маркеров в тексте, при равенстве — выше `priority` |
| `retry` | какими грамматиками попробовать файл, если в этой синтаксические ошибки |
| `case_sensitive` | `false` — имена функций и ввода-вывода без учёта регистра (Pascal) |
| `separators` | разделители в составных именах: `["::"]`, `["."]` |
| `statement_end` | что убирать в конце текста блока (по умолчанию `;`) |
| `assign` | знак присваивания в блоках, которые blockwright пишет сам (`:=` в Pascal) |
| `strip` | регулярные выражения, удаляемые из текста блоков (`std::`); отключаются `--keep-std` |
| `skip`, `skip_pattern` | узлы, которые никогда не дают блоков: комментарии, ключевые слова-узлы (`^k[A-Z]` в Pascal) |
| `empty` | узлы, означающие «пусто», — например, пустое условие `for (;;)` |
| `conditions` | обёртки условий: `{ condition_clause = "value" }` |
| `words` | операторы, записанные идентификатором: `{ break = ["break"], return = ["exit"] }` |
| `hooks` | файл с hooks, путь относительно описания |

### `[functions]`

| Ключ | Смысл |
|------|-------|
| `nodes` | типы узлов-функций |
| `name` | путь к имени (по умолчанию `name`); пустая строка — искать по цепочке `declarator`, как в C |
| `requires` | для C: функция — это объявление, в цепочке `declarator` которого есть такой узел |
| `declarations` | объявления без тела (прототипы): из них берутся только имена |
| `names` | типы узлов, которые считаются именем |
| `body`, `parameters`, `signature` | пути к телу, списку параметров и заголовку |
| `parameter_nodes`, `ignore_parameters` | какие узлы считать параметрами и какие имена пропускать (`self`, `void`) |
| `scopes`, `scope_separator` | классы и пространства имён, чьё имя добавляется к имени функции |
| `entry` | имена точек входа: их схема начинается с «Начало» |
| `ok_exit` | значения `return` в точке входа, означающие обычное завершение (`0`) |
| `nested` | `true` — вложенные функции получают свои схемы |

### `[program]`

Код вне функций — скрипт Python, `begin … end.` в Pascal, top-level
statements в C# — становится отдельной схемой.

| Ключ | Смысл |
|------|-------|
| `node` | тип узла программы |
| `body` | путь к телу или список путей (берётся первый найденный) |
| `name` | путь к имени программы; иначе — имя файла |
| `skip` | что не считать кодом программы: импорты, определения |

Схема не строится, если в коде нет ничего, кроме присваиваний и вызовов своих
функций. Поэтому `if __name__ == "__main__": main()` отдельной схемы не даёт.

### `[statements]`

Ключ — тип узла, значение — вид конструкции: строка (`"break"`) или таблица
с `kind`. Можно задать список вариантов: выбирается первый, у которого путь
`when` находит узел. Так в Go один `for_statement` даёт четыре разных цикла.

| `kind` | Ключи | Что получается |
|--------|-------|----------------|
| `block` | `skip` | операторы подряд |
| `skip` | | ничего |
| `simple` | | блок «процесс» (или ввод, см. `io.assign`) |
| `expression` | `skip` | оператор-выражение: ввод-вывод, вызов своей функции или процесс |
| `if` | `condition`, `then`, `else`, `elif`, `init` | ветвление; `elif` — типы узлов цепочки `elif` |
| `while` | `condition`, `body`, `else` | цикл с предусловием |
| `do` | `condition`, `body`, `until` | цикл с постусловием; `until = true` — выход, когда условие истинно |
| `for` | `init`, `condition`, `update`, `body`, `else` | цикл в стиле C; счётный рисуется шестиугольником |
| `counting` | `var`, `start`, `end`, `step`, `descending`, `body` | счётный цикл (`for i := 1 to n`) |
| `foreach` | `var`, `iterable`, `body`, `else`, `range` | «для каждого»; `range = ["range"]` превращает `range(a, b)` в счётный |
| `switch` | `value`, `body`, `cases`, `fallthrough`, `default_labels`, `default_after` | выбор |
| `break`, `continue` | | переходы |
| `return`, `throw` | `value` | завершение |
| `goto`, `label` | `label` | соединители |
| `try` | `body`, `handlers`, `else`, `finally`, `catch_all` | обработка исключений |
| `inline` | `body` | заголовок-процесс и тело (`with`, `using`) |
| `hook` | `hook` | только hook |

Ключ `hook` можно добавить к любому виду: сначала вызывается hook, и если он
вернёт `None`, работает `kind`.

**`switch`.** `cases` — таблица «тип узла ветви → как её читать»:
`value` (путь к меткам), `labels` (типы узлов-меток, из текста убираются
`case`/`default` и двоеточие), `body` (путь к телу; иначе — всё, кроме меток),
`default = true` (ветвь «иначе»), `fallthrough` (своё значение для этого типа).
`fallthrough` у самого `switch`:

- `true` — как в C: ветвь без `break` проваливается в следующую, пустые
  `case` объединяются;
- `false` — никогда;
- строка — тип оператора, явно включающего провал (`fallthrough_statement` в Go).

`switch` без значения (`switch { case x > 0: … }` в Go) становится цепочкой
условий. `default_after` — тип токена, после которого идут операторы ветви
«иначе» (`kElse` в Pascal).

**`try`.** `handlers` — таблица «тип обработчика → `{ parameter, body }`».
`else`, `finally`, `catch_all` — пути к частям оператора. `catch_all` —
операторы, перехватывающие всё (Pascal `except … end` без `on`).

### `[calls]`

| Ключ | Смысл |
|------|-------|
| `nodes` | тип узла вызова → путь к списку аргументов: `{ call_expression = "arguments" }` |
| `callee` | путь к вызываемому; без него берётся текст до аргументов (`System.out.println`) |
| `callee_types` | вызов своей функции, только если вызываемое — узел этих типов (в C `obj.f()` не считается) |

Вызов функции, определённой в проекте, рисуется блоком «предопределённый
процесс».

### `[io]`

```toml
[io.output]
printf = { format = 0 }                  # формат в аргументе 0: "%d" → {n}
print = { weave = ":", sep = " " }       # аргументы в одну фразу через пробел
"Console.WriteLine" = { format = 0, style = "composite", weave = ":" }
fprintf = { format = 1, args = "1:" }

[io.input]
scanf = { args = "1:" }                  # Ввод: всё после формата
input = { args = ":0" }                  # просто «Ввод»
getline = { args = "1:", stream = 0 }    # только если аргумент 0 — поток ввода
```

Имя функции сравнивается целиком (`fmt.Println`) и по последней части
(`println`).

| Ключ функции вывода | Смысл |
|---------------------|-------|
| `format` | номер аргумента-формата |
| `style` | `printf` (по умолчанию) или `composite` (`{0}`, `{1}` в C#) |
| `weave` | срез аргументов, которые сплетаются в фразу: `"Итог: " + n` → `Итог: {n}` |
| `sep` | что вставлять между аргументами при сплетении (`print` в Python ставит пробел) |
| `args` | срез аргументов для `--io-style list` |

Срезы записываются как в Python: `":"`, `"1:"`, `":1"`, `":0"`.

| Ключ `[io]` | Смысл |
|-------------|-------|
| `assign` | присваивание из функции ввода — это ввод: `{ assignment = ["left", "right"] }`, тогда `n = int(input())` рисуется как `Ввод: n` |
| `skip_args`, `unwrap_args` | какие аргументы пропускать (`keyword_argument`) и какие обёртки снимать (`argument` в C#) |
| `input_strip` | префиксы, снимаемые с аргументов ввода: `"&"` |
| `printf_conversions`, `format_replace` | буквы спецификаторов формата; замены вроде `{ "%n" = " " }` в Java |
| `[io.streams]` | потоки C++: `output`, `input`, `output_operator`, `input_operator`, `newline`, `manipulators` |

### `[strings]`

| Ключ | Смысл |
|------|-------|
| `nodes` | типы строковых литералов; префиксы (`f`, `$`, `@`, `r`) и тройные кавычки снимаются сами |
| `concat` | узлы склейки соседних литералов (`"a" "b"` в C) |
| `concat_operator` | оператор склейки строк: `"+"` |
| `escape` | `backslash` (по умолчанию), `double` (`''` в Pascal) или `none` |
| `template` | вставка в шаблонной строке: `"${"` в JavaScript |
| `format_operator`, `format_tuples` | `"%d" % n` в Python |

## Границы подхода

- **Нужна грамматика tree-sitter.** Без неё описание не поможет: сначала
  придётся написать грамматику.
- **Таблица покрывает структурные конструкции.** Если в языке есть что-то
  своё, нужен hook. Пример — макросы Rust; так же решаются `defer` и `select`
  в Go или выражение в конце блока Rust как возвращаемое значение.
- **Некоторые конструкции упрощены.**
  - `for … else` / `while … else` при наличии `break` рисуются как проверка
    «цикл завершён без break?».
  - `try` рисуется последовательно: тело, затем проверки обработчиков, затем
    `finally`.
  - `break` с меткой (`break outer`) выходит из ближайшего цикла.
  - `break` внутри `match` Python ведёт к концу `match`.
- **Декларативные языки** (SQL, Prolog, Haskell) в блок-схему не
  укладываются.
