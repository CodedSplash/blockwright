"""Поиск исходников, выбор грамматики и извлечение функций."""

import os

import tree_sitter_c
import tree_sitter_cpp
from tree_sitter import Language, Parser

from .text import normalize

C_LANGUAGE = Language(tree_sitter_c.language())
CPP_LANGUAGE = Language(tree_sitter_cpp.language())

C_EXT = {".c"}
CPP_EXT = {".cpp", ".cc", ".cxx", ".c++", ".cp"}
H_EXT = {".h", ".hpp", ".hh", ".hxx", ".h++", ".inl", ".ipp", ".tcc"}
ALL_EXT = C_EXT | CPP_EXT | H_EXT

SKIP_DIRS = {".git", ".svn", "node_modules", "build", "cmake-build-debug",
             "cmake-build-release", "Debug", "Release", ".vs", ".idea",
             "x64", "x86", "__pycache__", "venv", ".venv", "vendor",
             "third_party", "external"}

CPP_MARKERS = ("std::", "class ", "namespace ", "template<", "template <",
               "public:", "private:", "protected:", "::", "#include <iostream>",
               "nullptr", "auto ", "new ", "delete ")


def discover(paths, recursive=True):
    """Возвращает отсортированный список исходных файлов."""
    files = []
    for p in paths:
        p = os.path.abspath(p)
        if os.path.isfile(p):
            files.append(p)
        elif os.path.isdir(p):
            for root, dirs, names in os.walk(p):
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
                for nm in sorted(names):
                    if os.path.splitext(nm)[1].lower() in ALL_EXT:
                        files.append(os.path.join(root, nm))
                if not recursive:
                    dirs[:] = []
    seen, out = set(), []
    for f in files:
        k = os.path.normcase(f)
        if k not in seen:
            seen.add(k)
            out.append(f)
    return out


def count_errors(node):
    total = 0
    stack = [node]
    while stack:
        n = stack.pop()
        if n.type == "ERROR" or n.is_missing:
            total += 1
        stack.extend(n.children)
    return total


def guess_language(path, src_text, force=None):
    if force in ("c", "cpp"):
        return force
    ext = os.path.splitext(path)[1].lower()
    if ext in CPP_EXT:
        return "cpp"
    if ext in C_EXT:
        return "c"
    return "cpp" if any(m in src_text for m in CPP_MARKERS) else "c"


def parse_source(src: bytes, lang: str):
    """Парсит исходник; при ошибках пробует вторую грамматику."""
    order = ["cpp", "c"] if lang == "cpp" else ["c", "cpp"]
    best = None
    for name in order:
        parser = Parser(CPP_LANGUAGE if name == "cpp" else C_LANGUAGE)
        tree = parser.parse(src)
        errs = count_errors(tree.root_node)
        if errs == 0:
            return tree, name, 0
        if best is None or errs < best[2]:
            best = (tree, name, errs)
    return best


# ------------------------------------------------------------- функции
def _text(src, node):
    if node is None:
        return ""
    return src[node.start_byte:node.end_byte].decode("utf-8", "replace")


def _find_function_declarator(node):
    cur = node.child_by_field_name("declarator")
    seen = 0
    while cur is not None and seen < 12:
        if cur.type == "function_declarator":
            return cur
        cur = cur.child_by_field_name("declarator")
        seen += 1
    return None


_NAME_TYPES = {"identifier", "field_identifier", "type_identifier",
               "qualified_identifier", "operator_name", "destructor_name",
               "operator_cast"}


def _innermost_name(src, node):
    cur = node
    seen = 0
    while cur is not None and seen < 12:
        if cur.type in _NAME_TYPES:
            return _text(src, cur).strip()
        nxt = cur.child_by_field_name("declarator")
        if nxt is None:
            for c in cur.named_children:
                if c.type in _NAME_TYPES:
                    return _text(src, c).strip()
            return ""
        cur = nxt
        seen += 1
    return ""


def _scope_prefix(src, node):
    parts = []
    cur = node.parent
    while cur is not None:
        if cur.type in ("class_specifier", "struct_specifier", "union_specifier"):
            nm = _text(src, cur.child_by_field_name("name")).strip()
            if nm:
                parts.append(nm)
        elif cur.type == "namespace_definition":
            nm = _text(src, cur.child_by_field_name("name")).strip()
            if nm:
                parts.append(nm)
        cur = cur.parent
    return "::".join(reversed(parts))


def _params(src, fdecl):
    plist = fdecl.child_by_field_name("parameters") if fdecl else None
    if plist is None:
        return []
    out = []
    for p in plist.named_children:
        if p.type not in ("parameter_declaration", "optional_parameter_declaration",
                          "variadic_parameter_declaration"):
            continue
        nm = _innermost_name(src, p)
        if not nm:
            nm = normalize(_text(src, p))
        out.append(nm)
    return [x for x in out if x and x != "void"]


def collect_functions(src, root):
    """Возвращает список узлов function_definition верхнего уровня."""
    out = []

    def rec(node, inside):
        kids = node.named_children
        if node.type == "function_definition":
            if not inside and node.child_by_field_name("body") is not None:
                out.append(node)
            inside = True
        for c in kids:
            rec(c, inside)

    rec(root, False)
    return out


def describe_function(src, node):
    fdecl = _find_function_declarator(node)
    name = _innermost_name(src, fdecl) if fdecl else ""
    if not name:
        name = _innermost_name(src, node) or "<аноним>"
    scope = _scope_prefix(src, node)
    full = f"{scope}::{name}" if scope else name
    body = node.child_by_field_name("body")
    sig = normalize(src[node.start_byte:body.start_byte].decode("utf-8", "replace"))
    params = _params(src, fdecl)
    base = name.split("::")[-1]
    short = "Начало" if base == "main" else f"{full}({', '.join(params)})"
    return {
        "name": full,
        "base": base,
        "signature": sig,
        "short": short,
        "line": node.start_point[0] + 1,
        "body": body,
    }


def collect_known_names(src, root):
    """Имена функций, определённых или объявленных в файле."""
    names = set()
    stack = [root]
    while stack:
        n = stack.pop()
        if n.type in ("function_definition", "declaration", "field_declaration"):
            fd = _find_function_declarator(n)
            if fd is not None:
                nm = _innermost_name(src, fd)
                if nm:
                    names.add(nm.split("::")[-1])
        stack.extend(n.named_children)
    return names
