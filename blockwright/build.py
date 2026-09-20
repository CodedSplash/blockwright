"""Построение IR блок-схемы по синтаксическому дереву tree-sitter."""

import re

from . import model as M
from .text import normalize

# --- функции ввода-вывода из <stdio.h> ------------------------------------
OUT_FUNCS = {"printf", "fprintf", "puts", "fputs", "putchar", "putc", "vprintf",
             "printf_s", "wprintf", "cout"}
IN_FUNCS = {"scanf", "fscanf", "sscanf", "gets", "gets_s", "fgets", "getchar",
            "getc", "scanf_s", "wscanf"}
OUT_STREAMS = {"cout", "cerr", "clog", "wcout"}
IN_STREAMS = {"cin", "wcin"}
ENDL = {"std::endl", "endl", '"\\n"', "'\\n'", "std::flush", "flush"}

# манипуляторы форматирования — сами по себе ничего не выводят
MANIPULATORS = {"endl", "flush", "ends", "fixed", "scientific", "hexfloat",
                "defaultfloat", "boolalpha", "noboolalpha", "showpoint",
                "noshowpoint", "showpos", "noshowpos", "left", "right",
                "internal", "hex", "dec", "oct", "setw", "setprecision",
                "setfill", "setbase", "setiosflags", "resetiosflags"}

STR_TYPES = {"string_literal", "raw_string_literal", "concatenated_string",
             "char_literal"}

# escape-последовательности -> то, что видно на экране
_ESCAPES = {"n": " ", "t": " ", "r": "", "0": "", "a": "", "b": "", "f": " ",
            "v": " ", "\\": "\\", '"': '"', "'": "'", "?": "?"}

# спецификаторы формата printf/scanf
_SPEC_RE = re.compile(
    r"%(?:%|[-+ #0']*\*?\d*(?:\.\*?\d+)?(?:hh|h|ll|l|L|q|z|j|t)?"
    r"[diuoxXfFeEgGaAcspn])")

_INT_RE = re.compile(r"^[+-]?\d+$")


def unescape(s):
    """Раскрывает escape-последовательности строкового литерала."""
    out, i = [], 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s):
            out.append(_ESCAPES.get(s[i + 1], s[i + 1]))
            i += 2
        else:
            out.append(s[i])
            i += 1
    return "".join(out)


def _minus_one(t):
    t = t.strip()
    if _INT_RE.match(t):
        return str(int(t) - 1)
    return f"{t} - 1"


def _plus_one(t):
    t = t.strip()
    if _INT_RE.match(t):
        return str(int(t) + 1)
    return f"{t} + 1"


def strip_parens(s):
    s = s.strip()
    while s.startswith("(") and s.endswith(")"):
        depth = 0
        ok = True
        for i, ch in enumerate(s):
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0 and i != len(s) - 1:
                    ok = False
                    break
        if not ok:
            break
        s = s[1:-1].strip()
    return s


class Builder:
    """Преобразует поддерево функции в IR блок-схемы."""

    def __init__(self, src: bytes, opts, known_funcs=frozenset()):
        self.src = src
        self.opts = opts
        self.known = known_funcs
        self.fn_is_main = False

    # ---------- утилиты ----------
    def t(self, node):
        if node is None:
            return ""
        s = self.src[node.start_byte:node.end_byte].decode("utf-8", "replace")
        s = normalize(s)
        if not self.opts.keep_std:
            s = re.sub(r"\bstd\s*::\s*", "", s)
        return s

    def raw_name(self, node):
        if node is None:
            return ""
        return self.src[node.start_byte:node.end_byte].decode("utf-8", "replace").strip()

    @staticmethod
    def f(node, name):
        return node.child_by_field_name(name) if node is not None else None

    def op_of(self, node):
        o = self.f(node, "operator")
        if o is not None:
            return self.raw_name(o)
        for i in range(node.child_count):
            c = node.child(i)
            if not c.is_named and node.field_name_for_child(i) == "operator":
                return self.raw_name(c)
        return ""

    # ---------- вход ----------
    def build_body(self, body_node, is_main=False):
        self.fn_is_main = is_main
        return M.Seq(self.stmt_list(body_node))

    def stmt_list(self, node):
        out = []
        if node is None:
            return out
        if node.type == "compound_statement":
            for c in node.named_children:
                out.extend(self.stmt(c))
        else:
            out.extend(self.stmt(node))
        return out

    def block(self, node):
        return M.Seq(self.stmt_list(node))

    # ---------- операторы ----------
    def stmt(self, n):
        k = n.type
        if k in ("comment", "preproc_call"):
            return []
        if k == "compound_statement":
            return self.stmt_list(n)
        if k == "expression_statement":
            return self.expression_statement(n)
        if k in ("declaration", "field_declaration"):
            return [self.declaration(n)]
        if k == "if_statement":
            return [self.if_stmt(n)]
        if k == "while_statement":
            return [M.While(self.cond_text(self.f(n, "condition")),
                            self.block(self.f(n, "body")))]
        if k == "do_statement":
            return [M.DoWhile(self.cond_text(self.f(n, "condition")),
                              self.block(self.f(n, "body")))]
        if k == "for_statement":
            return [self.for_stmt(n)]
        if k == "for_range_loop":
            return [self.for_range(n)]
        if k == "switch_statement":
            return [self.switch_stmt(n)]
        if k == "break_statement":
            return [M.Jump("break")]
        if k == "continue_statement":
            return [M.Jump("continue")]
        if k == "return_statement":
            return [self.return_stmt(n)]
        if k == "goto_statement":
            lab = self.raw_name(self.f(n, "label"))
            return [M.Simple(M.CONNECTOR, lab, terminal=True)]
        if k == "labeled_statement":
            lab = self.raw_name(self.f(n, "label"))
            items = [M.Simple(M.CONNECTOR, lab)]
            for c in n.named_children[1:]:
                items.extend(self.stmt(c))
            return items
        if k == "try_statement":
            return self.try_stmt(n)
        if k == "throw_statement":
            inner = n.named_children[0] if n.named_children else None
            txt = self.t(inner) if inner is not None else ""
            return [M.Simple(M.TERMINATOR, ("Исключение: " + txt) if txt else "Исключение",
                             terminal=True)]
        if k in (";", "ERROR"):
            return []
        # всё остальное — обычный процесс
        txt = self.t(n).rstrip(";")
        return [M.Simple(M.PROCESS, txt)] if txt else []

    # ---------- отдельные конструкции ----------
    def cond_text(self, node):
        if node is None:
            return "условие"
        if node.type == "condition_clause":
            v = self.f(node, "value")
            if v is None:
                v = node.named_children[-1] if node.named_children else None
            return strip_parens(self.t(v))
        return strip_parens(self.t(node))

    def declaration(self, n):
        txt = self.t(n).rstrip(";").strip()
        # вызов пользовательской функции в инициализаторе не меняет тип блока
        return M.Simple(M.PROCESS, txt)

    def return_stmt(self, n):
        inner = n.named_children[0] if n.named_children else None
        txt = self.t(inner) if inner is not None else ""
        style = getattr(self.opts, "return_style", "auto")
        if style == "end" or not txt:
            # `return;` — это просто конец подпрограммы
            label = self.opts.end_label
        elif style == "auto" and self.fn_is_main and txt in ("0", "EXIT_SUCCESS"):
            # `return 0` в main — штатное завершение программы, не «значение»
            label = self.opts.end_label
        else:
            label = f"Возврат {txt}"
        return M.Simple(M.TERMINATOR, label, terminal=True)

    def if_stmt(self, n):
        cond = self.cond_text(self.f(n, "condition"))
        then_ = self.block(self.f(n, "consequence"))
        alt = self.f(n, "alternative")
        else_ = None
        if alt is not None:
            if alt.type == "else_clause":
                inner = alt.named_children[-1] if alt.named_children else None
                else_ = self.block(inner)
            else:
                else_ = self.block(alt)
            if not else_.items:
                else_ = None
        return M.If(cond, then_, else_)

    # --- for -------------------------------------------------------------
    def _simple_from_node(self, node):
        if node is None:
            return None
        txt = self.t(node).rstrip(";").strip()
        return M.Simple(M.PROCESS, txt) if txt else None

    def _canonical_for(self, n):
        """Распознаёт «школьный» счётный цикл -> текст шестиугольника."""
        init, cond, upd = self.f(n, "initializer"), self.f(n, "condition"), self.f(n, "update")
        if init is None or cond is None or upd is None:
            return None
        # переменная и начальное значение
        var = start = None
        if init.type == "declaration":
            decls = [c for c in init.named_children if c.type == "init_declarator"]
            if len(decls) != 1:
                return None
            var = self.t(self.f(decls[0], "declarator"))
            start = self.t(self.f(decls[0], "value"))
        elif init.type == "assignment_expression":
            var = self.t(self.f(init, "left"))
            start = self.t(self.f(init, "right"))
        else:
            return None
        if not var or not start or not re.fullmatch(r"[A-Za-z_]\w*", var):
            return None
        # условие
        if cond.type != "binary_expression":
            return None
        op = self.op_of(cond)
        if op not in ("<", "<=", ">", ">="):
            return None
        if self.t(self.f(cond, "left")) != var:
            return None
        limit = self.t(self.f(cond, "right"))
        # шаг
        step = None
        if upd.type == "update_expression":
            if self.t(self.f(upd, "argument")) != var:
                return None
            step = 1 if self.op_of(upd) == "++" else -1
        elif upd.type == "assignment_expression":
            if self.t(self.f(upd, "left")) != var:
                return None
            uop = self.op_of(upd)
            rhs = self.t(self.f(upd, "right"))
            if not _INT_RE.match(rhs):
                return None
            if uop == "+=":
                step = int(rhs)
            elif uop == "-=":
                step = -int(rhs)
            else:
                return None
        else:
            return None
        if step == 0:
            return None
        if step > 0 and op not in ("<", "<="):
            return None
        if step < 0 and op not in (">", ">="):
            return None
        end = limit if op in ("<=", ">=") else (_minus_one(limit) if step > 0 else _plus_one(limit))
        header = f"{var} = {start}, {end}"
        if step != 1:
            header += f", {step}"
        return header

    def for_stmt(self, n):
        body = self.block(self.f(n, "body"))
        style = self.opts.for_style
        header = None
        if style in ("auto", "hexagon"):
            header = self._canonical_for(n)
        if header and style in ("auto", "hexagon"):
            return M.ForLoop(body=body, style="hexagon", header=header)
        cond = self.f(n, "condition")
        return M.ForLoop(
            body=body,
            style="decision",
            init=self._simple_from_node(self.f(n, "initializer")),
            cond=self.cond_text(cond) if cond is not None else "истина",
            update=self._simple_from_node(self.f(n, "update")),
        )

    def for_range(self, n):
        var = self.t(self.f(n, "declarator")).lstrip("&* ").strip()
        cont = self.t(self.f(n, "right"))
        body = self.block(self.f(n, "body"))
        header = f"для каждого {var} из {cont}"
        if self.opts.for_style == "decision":
            return M.ForLoop(body=body, style="decision", init=None,
                             cond=f"есть ещё элементы {cont}?", update=None)
        return M.ForLoop(body=body, style="hexagon", header=header)

    # --- switch ----------------------------------------------------------
    def switch_stmt(self, n):
        expr = self.cond_text(self.f(n, "condition"))
        body = self.f(n, "body")
        cases = []
        pending_labels = []
        if body is not None:
            raw = [c for c in body.named_children if c.type == "case_statement"]
            for idx, cs in enumerate(raw):
                val = self.f(cs, "value")
                label = self.t(val) if val is not None else "иначе"
                stmts = []
                for c in cs.named_children:
                    if val is not None and c.start_byte == val.start_byte:
                        continue
                    stmts.extend(self.stmt(c))
                if not stmts:
                    # пустая ветка `case X:` — объединяем с следующей
                    pending_labels.append(label)
                    continue
                labels = pending_labels + [label]
                pending_labels = []
                blk = M.Seq(stmts)
                cases.append(M.Case(labels, blk))
            if pending_labels:
                cases.append(M.Case(pending_labels, M.Seq([])))
        # определить «проваливание» (нет break/return в конце ветки)
        for i, c in enumerate(cases):
            c.fallthrough = (i < len(cases) - 1) and not _ends_flow(c.body)
        return M.Switch(expr, cases)

    def try_stmt(self, n):
        items = self.stmt_list(self.f(n, "body"))
        for c in n.named_children:
            if c.type == "catch_clause":
                params = self.t(self.f(c, "parameters"))
                cond = "Возникло исключение " + strip_parens(params) if params else "Возникло исключение"
                items.append(M.If(cond, self.block(self.f(c, "body")), None))
        return items

    # --- выражения -------------------------------------------------------
    def expression_statement(self, n):
        inner = n.named_children[0] if n.named_children else None
        if inner is None:
            return []
        io = self.try_io(inner)
        if io is not None:
            return [io]
        if inner.type == "call_expression" and self.is_user_call(inner):
            return [M.Simple(M.PREDEF, self.t(inner))]
        txt = self.t(inner)
        return [M.Simple(M.PROCESS, txt)] if txt else []

    def callee_name(self, call):
        fn = self.f(call, "function")
        if fn is None:
            return ""
        name = self.raw_name(fn)
        name = name.split("::")[-1]
        return name.strip()

    def is_user_call(self, call):
        fn = self.f(call, "function")
        if fn is None or fn.type not in ("identifier", "qualified_identifier"):
            return False
        return self.callee_name(call) in self.known

    # --- сборка человекочитаемого текста ввода-вывода --------------------
    def _string_value(self, node):
        """Содержимое строкового литерала без кавычек, либо None."""
        if node is None:
            return None
        if node.type == "concatenated_string":
            vals = [self._string_value(c) for c in node.named_children
                    if c.type in STR_TYPES]
            if not vals or any(v is None for v in vals):
                return None
            return "".join(vals)
        if node.type not in STR_TYPES:
            return None
        raw = self.raw_name(node)
        quote = "'" if node.type == "char_literal" else '"'
        i, j = raw.find(quote), raw.rfind(quote)
        if i < 0 or j <= i:
            return None
        return unescape(raw[i + 1:j])

    def _is_manipulator(self, node):
        name = self.raw_name(node).split("::")[-1].split("(")[0].strip()
        return name in MANIPULATORS

    @staticmethod
    def _weave(segments, prefix):
        """Склеивает куски текста и выражений в одну читаемую строку.

        Текст из литералов идёт как есть, значения выражений подставляются
        в фигурных скобках — получается «Вывод: Задание #{job.id} (12 стр.)»
        вместо «Вывод: " Задание #", job.id, " (", ...».
        """
        exprs = [v for kind, v in segments if kind == "expr"]
        if not any(kind == "text" for kind, _ in segments):
            return prefix + ", ".join(exprs) if exprs else "Перевод строки"
        buf = []
        for kind, v in segments:
            buf.append(v if kind == "text" else "{" + v + "}")
        body = normalize("".join(buf)).strip()
        if not body:
            return prefix + ", ".join(exprs) if exprs else "Перевод строки"
        return prefix + body

    def _segments(self, nodes):
        segs = []
        for p in nodes:
            if self._is_manipulator(p):
                segs.append(("text", " "))
                continue
            val = self._string_value(p)
            if val is not None:
                segs.append(("text", val))
            else:
                segs.append(("expr", self.t(p)))
        return segs

    def _format_call(self, fmt_node, arg_nodes, prefix):
        """printf-подобный вызов -> текст с подставленными аргументами."""
        fmt = self._string_value(fmt_node)
        args = [self.t(a) for a in arg_nodes]
        if fmt is None:
            parts = ([self.t(fmt_node)] if fmt_node is not None else []) + args
            return prefix + ", ".join(p for p in parts if p)
        used = [0]

        def repl(m):
            if m.group(0) == "%%":
                return "%"
            if used[0] < len(args):
                used[0] += 1
                return "{" + args[used[0] - 1] + "}"
            return m.group(0)

        body = _SPEC_RE.sub(repl, fmt)
        tail = args[used[0]:]
        if tail:
            body = body.rstrip() + " " + ", ".join("{" + a + "}" for a in tail)
        body = normalize(body).strip()
        return prefix + body if body else "Перевод строки"

    def _flatten_stream(self, node, op):
        if node.type == "binary_expression" and self.op_of(node) == op:
            return (self._flatten_stream(self.f(node, "left"), op)
                    + [self.f(node, "right")])
        return [node]

    def try_io(self, node):
        """Распознаёт ввод-вывод; возвращает блок IO либо None."""
        style = self.opts.io_style
        code_style = style == "code"
        pretty = style == "pretty"
        # --- потоки C++ ---
        if node.type == "binary_expression" and self.op_of(node) in ("<<", ">>"):
            op = self.op_of(node)
            parts = self._flatten_stream(node, op)
            head = self.raw_name(parts[0]).split("::")[-1]
            if op == "<<" and head in OUT_STREAMS:
                if code_style:
                    return M.Simple(M.IO, self.t(node))
                if pretty:
                    return M.Simple(M.IO, self._weave(self._segments(parts[1:]),
                                                      "Вывод: "))
                args = [self.t(p) for p in parts[1:]]
                args = [a for a in args if a not in ENDL and a.replace("std::", "") not in ENDL]
                return M.Simple(M.IO, "Вывод: " + ", ".join(args) if args else "Перевод строки")
            if op == ">>" and head in IN_STREAMS:
                if code_style:
                    return M.Simple(M.IO, self.t(node))
                args = [self.t(p) for p in parts[1:]]
                return M.Simple(M.IO, "Ввод: " + ", ".join(args))
            return None
        # --- функции C ---
        if node.type == "call_expression":
            name = self.callee_name(node)
            arglist = self.f(node, "arguments")
            nodes = list(arglist.named_children) if arglist is not None else []
            args = [self.t(a) for a in nodes]
            if name == "getline" and args:
                stream = args[0].split("::")[-1]
                if stream in IN_STREAMS:
                    return M.Simple(M.IO, self.t(node) if code_style
                                    else "Ввод: " + ", ".join(args[1:]))
                return None
            if name in OUT_FUNCS:
                if code_style:
                    return M.Simple(M.IO, self.t(node))
                if pretty and nodes:
                    if name in ("printf", "printf_s", "wprintf", "vprintf"):
                        return M.Simple(M.IO, self._format_call(nodes[0], nodes[1:], "Вывод: "))
                    if name == "fprintf":
                        return M.Simple(M.IO, self._format_call(nodes[1], nodes[2:], "Вывод: "))
                    if name in ("puts", "fputs", "putchar", "putc"):
                        return M.Simple(M.IO, self._weave(self._segments(nodes[:1]), "Вывод: "))
                if name in ("fprintf", "putc"):
                    args = args[1:]
                elif name == "fputs":
                    args = args[:1]
                return M.Simple(M.IO, "Вывод: " + ", ".join(args) if args else "Вывод")
            if name in IN_FUNCS:
                if code_style:
                    return M.Simple(M.IO, self.t(node))
                if name in ("scanf", "scanf_s", "wscanf"):
                    rest = args[1:]
                elif name in ("fscanf", "sscanf"):
                    rest = args[2:]
                else:
                    rest = args
                rest = [a.lstrip("&") for a in rest]
                return M.Simple(M.IO, "Ввод: " + ", ".join(rest) if rest else "Ввод")
        return None


def _ends_flow(block):
    """True, если поток управления не доходит до конца блока (break/return)."""
    items = block.items if isinstance(block, M.Seq) else [block]
    if not items:
        return False
    last = items[-1]
    if isinstance(last, M.Jump):
        return True
    if isinstance(last, M.Simple):
        return last.terminal
    if isinstance(last, M.If):
        return (last.else_ is not None and _ends_flow(last.then_)
                and _ends_flow(last.else_))
    if isinstance(last, M.Switch):
        return bool(last.cases) and all(_ends_flow(c.body) for c in last.cases)
    return False
