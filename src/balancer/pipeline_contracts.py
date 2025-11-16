from __future__ import annotations
from enum import Enum, auto
from typing import TypeVar, Generic, Optional, NamedTuple, Iterable
from dataclasses import dataclass, field
from sympy import Rational, Integer
from openpyxl.styles import Font, Alignment, Border, Side

T = TypeVar("T")

@dataclass(slots=True)
class Context:
    title: Optional(str)=None

class Bundle(NamedTuple):
    context: Context
    stream: T



class LineType(Enum):
    """ All the types of lines in the input file """
    END = auto()
    COMMENT = auto()
    TITLE = auto()
    REACTION = auto()
    NORMAL = auto()

@dataclass(slots=True)
class DataLine:
    line_type: LineType
    data: T



class Substance(NamedTuple):
    formula: str
    info: str
    elements_stoich: dict[str,Rational]
    input_mass: Optional[Rational]


class Reaction(NamedTuple):
    raw: str
    product: Substance
    reactants: list[Substance]
    basis: dict # only keys are used

    def __iter__(self):
        yield from self.reactants
        yield self.product


class SubstanceResult(NamedTuple):
    formula: str
    info: Optional[str]
    mole_mass: Rational
    stoich_in_eq: Integer
    mass: Rational

class ReactionResult(NamedTuple):
    product: SubsatanceResult
    reactants: list[SubstanceResult]



class Style(NamedTuple):
    font: Font
    alignment: Alignment
    border: Border
    
class Cell(NamedTuple):
    value: T
    number_format: str = "@"
    style: Optional[Sytle] = None

class Block(NamedTuple):
    column: Iterable[Cell]
    anchor_row: int
    anchor_col: int
    width: Optional[float]=None
