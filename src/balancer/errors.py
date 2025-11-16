from __future__ import annotations
from typing import Optional
import textwrap
# ======== No Traceback for CuteError ========
import sys

def handle_exception(exc_type, exc, tb):
    if issubclass(exc_type, CuteError):
        print(exc)
    else:
        sys.__excepthook__(exc_type, exc, tb)

sys.excepthook = handle_exception

# ======== ANSI Styles ========
RESET = "\033[0m"
BOLD = "\033[1m"

YELLOW = "\033[33m"
RED = "\033[31m"
BLUE = "\033[34m"


# ======== Base Classes ========
class CuteError(Exception):
    """ Human-friendly error with a gentle tone and structured wording. """

    def __init__(
        self,
        something: str,
        body: str,
        *,
        begin:str = "😿 Something weng wrong while " ,
        explanation: Optional[str] = None,
        hint: Optional[str] = None,
    ):
        self.begin = begin
        self.something = something
        self.body = body
        self.explanation = explanation
        self.hint = hint
        super().__init__(body)

    def __str__(self) -> str:
        # Apply indentation and coloring
        begin = self.begin
        something = f"{BLUE}{self.something}:{RESET}"
        body = textwrap.indent(f"{RED}{BOLD}{self.body}{RESET}", "   ")
        explanation = (
            f"{self.explanation}" if self.explanation else ""
        )
        hint = (
            textwrap.indent(f"{YELLOW}{self.hint}{RESET}", "   ")
            if self.hint else ""
        )

        return (
            f"--------\n{RESET}"
            f"{begin}{something}\n"
            f"{body}\n"
            f"{explanation}\n"
            f"{hint}\n"
        )

# ======== Specialized Errors ========

class InputError(CuteError):
    def __init__(self, path: str,*,explanation,hint):
        super().__init__(
            something="reading the input file",
            body=path,
            explanation=explanation,
            hint=hint,
        )

class InitHint(CuteError):
    def __init__(self, path: str,*,explanation,hint):
        super().__init__(
            something="The input file is needed",
            body=path,
            begin="🤓 Welcome to use this program! ",
            explanation=explanation,
            hint=hint,
        )


class ParseError(CuteError):
    def __init__(self, raw_reaction=None,*,explanation=None,hint=None):
        super().__init__(
            something="parsing the reaction",
            body=raw_reaction,
            explanation=explanation,
            hint=hint,
        )


class ComputeError(CuteError):
    def __init__(self, raw_reaction=None,*,explanation=None,hint=None):
        super().__init__(
            something="balancing the reaction",
            body=raw_reaction,
            explanation=explanation,
            hint=hint,
        )


class OutputError(CuteError):
    def __init__(self, output_path,*,explanation=None,hint=None):
        super().__init__(
            something="saving the recipe table to",
            body=output_path,
            explanation=explanation,
            hint=hint,
        )
