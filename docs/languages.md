# Describing a language

**English** · [Русский](languages.ru.md)

blockwright knows no programming language by itself. Everything that sets C
apart from Python or Pascal lives in a **language description**: a TOML file
in `blockwright/languages/`. The description names a
[tree-sitter](https://tree-sitter.github.io/) grammar and maps its nodes onto
flowchart constructs: "`while_statement` is a pre-test loop, the condition is
in the `condition` field, the body in `body`". Parsing, block layout, SVG and
the editor are shared by every language.

So a new language takes no code changes, just a grammar and a description.
Constructs that a table cannot express go into a small Python hooks file next
to the description.

- [What ships](#what-ships)
- [Your own language in five steps](#your-own-language-in-five-steps), with Rust as the example
- [Key reference](#key-reference)
- [Limits](#limits)

## What ships

| Language | File | Grammar |
|----------|------|---------|
| C | `c.toml` | bundled |
| C++ | `cpp.toml` (extends `c.toml`) | bundled |
| Python | `python.toml` | bundled |
| Java | `java.toml` | bundled |
| C# | `csharp.toml` | bundled |
| Go | `go.toml` | bundled |
| JavaScript | `javascript.toml` | bundled |
| Pascal | `pascal.toml` | `pip install tree-sitter-pascal`: the grammar is AGPL-3.0, so it is not bundled |

`python -m blockwright --langs` lists every loaded description with its
extensions and whether its grammar is installed.

## Your own language in five steps

The finished result of this section is in [`docs/example-rust/`](example-rust/):
the description, its hooks and a sample program.

### 1. Find a grammar

Almost every language has a tree-sitter grammar, usually with wheels on PyPI
named `tree-sitter-<language>`:

```bash
pip install tree-sitter-rust
```

The module is `tree_sitter_rust`, and its `language()` function returns the
grammar. When the function has another name (TypeScript has
`language_typescript`), the description says so.

### 2. Start with three lines

```toml
# my-langs/rust.toml
name = "rust"
grammar = "tree_sitter_rust"
extensions = [".rs"]
```

Put the file in any folder and pass the folder with `--lang-dir`, or list it
in the `BLOCKWRIGHT_LANGS` environment variable (`;`-separated on Windows,
`:` on Linux). A description there replaces a built-in one with the same
`name`.

### 3. Look at the tree

```bash
python -m blockwright --lang-dir my-langs --tree main.rs
```

`--tree` prints the nodes with their field names, which are the words a
description uses:

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

### 4. Map nodes to constructs

```toml
[functions]
nodes = ["function_item"]          # what a function is; its name is in `name`
entry = ["main"]                   # this one starts with "Begin"

[statements]
block = "block"                    # statements in a row
expression_statement = "expression"
let_declaration = "simple"         # a process block with the node's text
if_expression = { kind = "if", condition = "condition", then = "consequence", else = "alternative" }
else_clause = "block"
while_expression = { kind = "while", condition = "condition", body = "body" }
loop_expression = { kind = "while", body = "body" }      # no condition: "true"
match_expression = { kind = "switch", value = "value", body = "body", default_labels = ["_"], cases = { match_arm = { labels = ["match_pattern"], body = "value" } } }
break_expression = "break"
continue_expression = "continue"
return_expression = "return"
```

That is already enough for sensible charts. Nodes missing from `[statements]`
become process blocks with their own text, so a description can grow
step by step.

### 5. Hooks for what a table cannot say

`println!("{} -> {}", i, f(i))` is a macro, and the grammar leaves its
arguments as raw tokens. That takes code:

```toml
hooks = "rust_hooks.py"

[statements]
macro_invocation = { hook = "macro" }
# the hook first; when it returns None, a plain foreach
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
    return None        # other macros: a plain process block
```

A hook receives the builder, the node and the rule. It returns a list of
chart items (`blockwright/model.py`), or `None` to let the rule handle the
node. The builder offers what a hook needs:

- `t(node)`: the text of a node;
- `find(node, path)`;
- `block(node)` and `stmt(node)`: build nested statements;
- `L(key)`: chart words;
- `counting_loop(var, start, end, step, body)`.

The full example is
[`docs/example-rust/rust_hooks.py`](example-rust/rust_hooks.py).

Try it:

```bash
pip install tree-sitter-rust
python -m blockwright --lang-dir docs/example-rust --lang rust docs/example-rust --open
```

> [!WARNING]
> Hooks are Python code that runs when the description loads. Only pass
> folders you trust to `--lang-dir`.

## Key reference

### Node paths

Wherever a key points into a node (`condition = "condition"`), the value is a
**path**: one or more dot-separated steps. Each step is one of:

- a field name (`condition`, `body`);
- a child node type, when no field has that name (`for_clause`, `block`);
- `#N`, the N-th named child without a field (`#0` is the first).

For example, Go's `for_clause.initializer` is the `for_clause` child and then
its `initializer` field.

### Top level

| Key | Meaning |
|-----|---------|
| `name` | language id for `--lang`; defaults to the file name |
| `title` | human-readable name |
| `grammar` | grammar module, `"tree_sitter_x"`, or `{ module = "…", function = "language_tsx" }` |
| `package` | package name for the `pip install` hint |
| `bundle` | `false` keeps the grammar out of `vendor/` and the binaries |
| `extends` | the description this one builds on; tables merge key by key, lists and values are replaced |
| `extensions` | file extensions |
| `markers`, `priority` | choose between languages that share an extension (`.h`): the one with more markers in the text wins, then the higher `priority` |
| `retry` | grammars to try when this one reports syntax errors |
| `case_sensitive` | `false` matches function and I/O names regardless of case (Pascal) |
| `separators` | separators in qualified names: `["::"]`, `["."]` |
| `statement_end` | what to trim from the end of block text (`;` by default) |
| `assign` | the assignment sign in blocks blockwright writes itself (`:=` in Pascal) |
| `strip` | regular expressions removed from block text (`std::`); `--keep-std` turns them off |
| `skip`, `skip_pattern` | nodes that never become blocks: comments, keyword nodes (`^k[A-Z]` in Pascal) |
| `empty` | nodes that mean "nothing here", like the empty condition of `for (;;)` |
| `conditions` | condition wrappers: `{ condition_clause = "value" }` |
| `words` | statements written as an identifier: `{ break = ["break"], return = ["exit"] }` |
| `hooks` | the hooks file, relative to the description |

### `[functions]`

| Key | Meaning |
|-----|---------|
| `nodes` | function node types |
| `name` | path to the name (`name` by default); an empty string follows the `declarator` chain, as in C |
| `requires` | for C: a declaration is a function when its `declarator` chain contains this node |
| `declarations` | declarations without a body (prototypes): only their names are collected |
| `names` | node types that count as a name |
| `body`, `parameters`, `signature` | paths to the body, the parameter list and the header |
| `parameter_nodes`, `ignore_parameters` | which nodes are parameters and which names to drop (`self`, `void`) |
| `scopes`, `scope_separator` | classes and namespaces whose name prefixes the function's |
| `entry` | entry point names: their chart starts with "Begin" |
| `ok_exit` | `return` values in an entry point that mean a normal end (`0`) |
| `nested` | `true` gives nested functions charts of their own |

### `[program]`

Code outside functions gets a chart of its own: a Python script, Pascal's
`begin … end.`, C# top-level statements.

| Key | Meaning |
|-----|---------|
| `node` | program node type |
| `body` | path to the body, or a list of paths (the first match wins) |
| `name` | path to the program name; the file name otherwise |
| `skip` | what is not program code: imports, definitions |

No chart is made when the code does nothing but assign and call the user's
own functions, so `if __name__ == "__main__": main()` does not get one.

### `[statements]`

The key is a node type. The value is the construct: a string (`"break"`) or a
table with `kind`. A list of variants is allowed too: the first whose `when`
path finds a node wins. That is how Go's single `for_statement` turns into
four different loops.

| `kind` | Keys | Result |
|--------|------|--------|
| `block` | `skip` | statements in a row |
| `skip` | | nothing |
| `simple` | | a process block (or input, see `io.assign`) |
| `expression` | `skip` | an expression statement: I/O, a call of a user function, or a process |
| `if` | `condition`, `then`, `else`, `elif`, `init` | a decision; `elif` lists the node types of an `elif` chain |
| `while` | `condition`, `body`, `else` | pre-test loop |
| `do` | `condition`, `body`, `until` | post-test loop; `until = true` leaves when the condition holds |
| `for` | `init`, `condition`, `update`, `body`, `else` | C-style loop; a counting one becomes a hexagon |
| `counting` | `var`, `start`, `end`, `step`, `descending`, `body` | counting loop (`for i := 1 to n`) |
| `foreach` | `var`, `iterable`, `body`, `else`, `range` | "for each"; `range = ["range"]` turns `range(a, b)` into a counting loop |
| `switch` | `value`, `body`, `cases`, `fallthrough`, `default_labels`, `default_after` | multi-way branch |
| `break`, `continue` | | jumps |
| `return`, `throw` | `value` | terminators |
| `goto`, `label` | `label` | connectors |
| `try` | `body`, `handlers`, `else`, `finally`, `catch_all` | exception handling |
| `inline` | `body` | a header process block, then the body (`with`, `using`) |
| `hook` | `hook` | the hook alone |

Any kind may also carry a `hook` key. The hook runs first, and `kind` takes
over when the hook returns `None`.

**`switch`.** `cases` maps a branch node type to how to read it:

- `value`: path to its labels;
- `labels`: label node types (`case`, `default` and the colon are trimmed from their text);
- `body`: path to the body; without it, everything except the labels;
- `default = true`: the "else" branch;
- `fallthrough`: overrides the switch's own value for this type.

`fallthrough` on the switch itself:

- `true` works like C: a branch without `break` falls into the next one, and
  empty cases merge;
- `false` never falls through;
- a string names the statement type that falls through explicitly (Go's
  `fallthrough_statement`).

A switch without a value (Go's `switch { case x > 0: … }`) becomes a chain
of conditions. `default_after` is the token after which the "else" branch's
statements follow (`kElse` in Pascal).

**`try`.** `handlers` maps a handler node type to `{ parameter, body }`.
`else`, `finally` and `catch_all` are paths to parts of the statement.
`catch_all` holds statements that catch anything (Pascal's `except … end`
without `on`).

### `[calls]`

| Key | Meaning |
|-----|---------|
| `nodes` | call node type → path to its arguments: `{ call_expression = "arguments" }` |
| `callee` | path to what is called; without it, the text before the arguments (`System.out.println`) |
| `callee_types` | a call is a user function call only if the callee is one of these node types (in C, `obj.f()` is not) |

A call of a function defined in the project becomes a predefined process
block.

### `[io]`

```toml
[io.output]
printf = { format = 0 }                  # format in argument 0: "%d" → {n}
print = { weave = ":", sep = " " }       # arguments woven into one line, space-separated
"Console.WriteLine" = { format = 0, style = "composite", weave = ":" }
fprintf = { format = 1, args = "1:" }

[io.input]
scanf = { args = "1:" }                  # Input: everything after the format
input = { args = ":0" }                  # just "Input"
getline = { args = "1:", stream = 0 }    # only when argument 0 is an input stream
```

A function name matches in full (`fmt.Println`) or by its last part
(`println`).

| Output key | Meaning |
|------------|---------|
| `format` | index of the format argument |
| `style` | `printf` (default) or `composite` (`{0}`, `{1}` in C#) |
| `weave` | slice of arguments woven into one line: `"Total: " + n` → `Total: {n}` |
| `sep` | inserted between woven arguments (Python's `print` puts a space) |
| `args` | slice of arguments for `--io-style list` |

Slices are written as in Python: `":"`, `"1:"`, `":1"`, `":0"`.

| `[io]` key | Meaning |
|------------|---------|
| `assign` | assignment from an input function is input: with `{ assignment = ["left", "right"] }`, `n = int(input())` becomes `Input: n` |
| `skip_args`, `unwrap_args` | arguments to skip (`keyword_argument`) and wrappers to remove (`argument` in C#) |
| `input_strip` | prefixes removed from input arguments: `"&"` |
| `printf_conversions`, `format_replace` | format conversion letters; replacements such as `{ "%n" = " " }` for Java |
| `[io.streams]` | C++ streams: `output`, `input`, `output_operator`, `input_operator`, `newline`, `manipulators` |

### `[strings]`

| Key | Meaning |
|-----|---------|
| `nodes` | string literal types; prefixes (`f`, `$`, `@`, `r`) and triple quotes are handled |
| `concat` | nodes gluing adjacent literals (`"a" "b"` in C) |
| `concat_operator` | the string concatenation operator: `"+"` |
| `escape` | `backslash` (default), `double` (`''` in Pascal) or `none` |
| `template` | the substitution opener in template strings: `"${"` in JavaScript |
| `format_operator`, `format_tuples` | Python's `"%d" % n` |

## Limits

- **A tree-sitter grammar is required.** Without one, a description cannot
  help: the grammar comes first.
- **A table covers the structural constructs.** Anything a language does its
  own way needs a hook. Rust's macros are the example; Go's `defer` and
  `select`, or Rust's trailing expression as the return value, would be done
  the same way.
- **Some constructs are simplified:**
  - `for … else` / `while … else` with a `break` inside are drawn as a "loop
    ended without break?" check;
  - `try` is drawn in sequence: the body, then one check per handler, then
    `finally`;
  - a labelled `break outer` leaves the nearest loop;
  - a `break` inside a Python `match` goes to the end of the `match`.
- **Declarative languages** (SQL, Prolog, Haskell) do not fit a flowchart.
