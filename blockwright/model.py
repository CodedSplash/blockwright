"""Промежуточное представление (IR) блок-схемы.

IR — это структурное дерево (последовательность, ветвление, циклы,
переключатель) плюс «нелокальные» переходы (break / continue / return /
goto). Такое представление позволяет строить схему без универсального
graph-layout: каждая конструкция знает, как разместить себя сама.
"""

from dataclasses import dataclass, field
from typing import List, Optional

# --- типы блоков по ГОСТ 19.701-90 ---------------------------------------
TERMINATOR = "terminator"     # начало / конец / возврат (овал)
PROCESS = "process"           # процесс (прямоугольник)
IO = "io"                     # ввод-вывод (параллелограмм)
DECISION = "decision"         # решение (ромб)
PREDEF = "predefined"         # предопределённый процесс (вызов функции)
PREP = "preparation"          # подготовка (заголовок цикла, шестиугольник)
CONNECTOR = "connector"       # соединитель (круг)


@dataclass
class Simple:
    """Одиночный блок с одним входом и (необязательно) одним выходом."""
    kind: str
    text: str
    terminal: bool = False    # True -> у блока нет выхода (return / throw)


@dataclass
class Jump:
    """break / continue — переход без собственного блока."""
    kind: str                 # 'break' | 'continue'


@dataclass
class Seq:
    items: List[object] = field(default_factory=list)


@dataclass
class If:
    cond: str
    then_: object
    else_: Optional[object] = None


@dataclass
class While:
    cond: str
    body: object


@dataclass
class DoWhile:
    cond: str
    body: object


@dataclass
class ForLoop:
    body: object
    style: str = "decision"           # 'hexagon' | 'decision'
    header: str = ""                  # текст шестиугольника (style='hexagon')
    init: Optional[Simple] = None
    cond: Optional[str] = None
    update: Optional[Simple] = None


@dataclass
class Case:
    labels: List[str]
    body: object
    fallthrough: bool = False


@dataclass
class Switch:
    expr: str
    cases: List[Case] = field(default_factory=list)


@dataclass
class Function:
    name: str            # полное имя (с классом/пространством имён)
    signature: str       # сигнатура для подписи схемы
    short: str           # текст блока «Начало»
    file: str
    rel: str
    line: int
    lang: str
    body: Seq
