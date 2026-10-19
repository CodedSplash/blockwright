"""Hooks for rust.toml: what a table cannot say about Rust.

Each hook gets (builder, node, rule) and returns a list of flowchart items,
or None to let the rule's `kind` handle the node.
"""

import re

from blockwright import model as M

OUTPUT = {"println", "print", "eprintln", "eprint"}
PANIC = {"panic", "unreachable", "todo", "unimplemented"}


def _split_args(text):
    """`"{} -> {}", i, f(a, b)` -> ['"{} -> {}"', 'i', 'f(a, b)']"""
    out, depth, cur = [], 0, ""
    for ch in text:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


def macro(builder, node, rule):
    name = builder.t(builder.find(node, "macro"))
    tokens = builder.find(node, "token_tree")
    args = _split_args(builder.t(tokens)[1:-1]) if tokens is not None else []
    if name in OUTPUT:
        if builder.opts.io_style == "code":
            return [M.Simple(M.IO, builder.t(node))]
        if not args:
            return [M.Simple(M.IO, builder.L("newline"))]
        fmt, values = args[0], args[1:]
        if not (fmt.startswith('"') and fmt.endswith('"')):
            return [M.Simple(M.IO, builder.L("out") + ", ".join(args))]
        values = iter(values)
        # {} and {:.2} take the next argument, {name} names one itself
        text = re.sub(r"\{(:[^}]*)?\}", lambda m: "{" + next(values, "?") + "}", fmt[1:-1])
        return [M.Simple(M.IO, builder.L("out") + text)]
    if name in PANIC:
        msg = args[0].strip('"') if args else ""
        return [M.Simple(M.TERMINATOR, builder.L("exception", msg) if msg
                         else builder.L("exception_bare"), terminal=True)]
    return None


def range_for(builder, node, rule):
    rng = builder.find(node, "value")
    if rng is None or rng.type != "range_expression" or rng.named_child_count != 2:
        return None
    start, end = (builder.t(c) for c in rng.named_children)
    op = builder.t(rng)[len(start):].lstrip()[:3]
    if not op.startswith("..="):
        end = f"{end} - 1"
    var = builder.t(builder.find(node, "pattern"))
    body = builder.block(builder.find(node, "body"))
    return [builder.counting_loop(var, start, end, 1, body)]
