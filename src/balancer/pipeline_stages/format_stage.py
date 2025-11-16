from __future__ import annotations
from openpyxl.styles import Font, Alignment, Border, Side
from typing import Iterator

from ..pipeline_contracts import Context, Bundle, LineType, DataLine, SubstanceResult, ReactionResult, Style, Cell, Block

from functools import lru_cache


# ======== styles ========
BLUE = "00008B"
RED = "FF0000"
BLACK = "000000"
DARK_GRAY = "1A1A1A"

thin = Side(border_style="thin", color=BLACK)

DEFAULT_FONT = "Times New Roman"
NORMAL_FONT   = "SimSun"

FONT_SIZE = 11
BIG_FONT_SIZE = 14

# works for Times New Roman
WIDTH_SCALE = FONT_SIZE / 11 * 1.04
WIDTH_EXTRA = 0.71

def col_width_from_str(text:str):
    english_count = sum(1 for ch in text if ord(ch) < 128)
    return (len(text) * 2 - english_count) * WIDTH_SCALE + WIDTH_EXTRA
# def col_width(char_count:int):
#     return char_count * WIDTH_SCALE + WIDTH_EXTRA
ROW_HEADER_WIDTH = 15
NUMBER_WIDTH = 8
EQ_WIDTH = 6

title_style = Style(
        Font(
            name=DEFAULT_FONT,
            size=BIG_FONT_SIZE,
            bold=True,
            color=BLUE,
            ),
        Alignment(
            horizontal="left",
            vertical="center",
            indent=0
            ),
        Border(left=None,right=None,top=None,bottom=None),
        )
row_header_style = title_style

col_header_style = Style(
        Font(
            name=DEFAULT_FONT,
            size=FONT_SIZE,
            bold=True,
            color=BLUE,
            ),
        Alignment(
            horizontal="center",
            vertical="center",
            indent=0,
            shrink_to_fit=True,
            ),
        Border(left=None,right=None,top=None,bottom=None),
        )

table_body_style = Style(
        Font(
            name=DEFAULT_FONT,
            size=FONT_SIZE,
            bold=False,
            color=BLACK,
            ),
        Alignment(
            horizontal="center",
            vertical="center",
            shrink_to_fit=True,
            indent=0
            ),
        Border(left=thin,right=thin,top=thin,bottom=thin),
        )

normal_style = Style(
        Font(
            name=NORMAL_FONT,
            size=FONT_SIZE,
            bold=False,
            color=DARK_GRAY,
            ),
        Alignment(
            horizontal="left",
            vertical="center",
            indent=1
            ),
        Border(left=None,right=None,top=None,bottom=None),
        )

row_header_column = (
       Cell(value="Equation", style=row_header_style),
       Cell(value="Mol. Wt.", style=row_header_style),
       Cell(value="Mol. Stoich.", style=row_header_style),
       Cell(value="Mass (g)", style=row_header_style),
        ) 

null_column = (
       Cell(value="", style=col_header_style),
       Cell(value="", style=table_body_style),
       Cell(value="", style=table_body_style),
       Cell(value="", style=table_body_style),
        ) 

eq_column = (
       Cell(value="  =  ", style=col_header_style),
       Cell(value="", style=table_body_style),
       Cell(value="", style=table_body_style),
       Cell(value="", style=table_body_style),
        ) 


def substance_column(result:SubstanceResult)->tuple[Cell]:
    if result.info:
        header = f"{result.formula}:{result.info}"
    else:
        header = result.formula
    return (
                Cell(header,"@",col_header_style),
                Cell(float(result.mole_mass),"0.#####",table_body_style),
                Cell(int(result.stoich_in_eq),"0",table_body_style),
                Cell(float(result.mass),"0.0000",table_body_style),
                )


# ======== Stage ========
class FormatStage:
    def __init__(self):
        self.reaction_rows = []
        self.null_start_cols = []
        self.product_columns = []
        self.focus_row = 1

    def title_block(self, title:str)->Block:
        cell = Cell(value=title, style=title_style)
        block = Block(
                (cell,),
                self.focus_row, 1,
                )
        self.focus_row += 2
        return block

    def normal_block(self, normal:str)->Block:
        cell = Cell(value=normal, style=normal_style)
        block = Block(
                (cell,),
                self.focus_row, 1
                )
        self.focus_row += 1
        return block

    def reactant_blocks(self, reaction_result:ReactionResult)->Iterator[Block]:
        focus_col=1
        yield Block(
                column=row_header_column,
                anchor_row=self.focus_row,
                anchor_col=focus_col,
                width=ROW_HEADER_WIDTH,
                )

        focus_col = 2
        for reactant in reaction_result.reactants:
            column = substance_column(reactant)
            yield Block(
                    column,
                    anchor_row=self.focus_row,
                    anchor_col=focus_col,
                    width=max(NUMBER_WIDTH, col_width_from_str(column[0].value)),
                    )
            focus_col += 1

        self.reaction_rows.append(self.focus_row)
        self.null_start_cols.append(focus_col)
        self.product_columns.append(substance_column(reaction_result.product))

        self.focus_row += 5


    def product_blocks(self):
        eq_col = max(self.null_start_cols)

        for row, null_start_col, product_column in zip(self.reaction_rows, self.null_start_cols, self.product_columns):
            for shift in range(eq_col - null_start_col):
                yield Block(
                        column=null_column,
                        anchor_row=row,
                        anchor_col=null_start_col+shift
                        )
            
            yield Block(
                    column=eq_column,
                    anchor_row=row,
                    anchor_col=eq_col,
                    width=EQ_WIDTH,
                    )

            yield Block(
                    column=product_column,
                    anchor_row=row,
                    anchor_col=eq_col+1,
                    width=max(NUMBER_WIDTH,col_width_from_str(product_column[0].value))
                    )


    def process(self,bundle:Bundle)->Bundle:
        datalines = bundle.stream

        def stream():
            for dataline in datalines:
                match dataline:
                    case DataLine(LineType.TITLE, title):
                        yield self.title_block(title)
                    case DataLine(LineType.REACTION, reaction_result):
                        yield from self.reactant_blocks(reaction_result)
                    case DataLine(LineType.NORMAL, normal):
                        yield self.normal_block(normal)
            
            if self.reaction_rows:
                yield from self.product_blocks()
        
        return Bundle(context=bundle.context, stream=stream())


