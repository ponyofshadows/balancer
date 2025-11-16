from __future__ import annotations
from typing import Iterator, Optional
from enum import Enum, auto
from sympy import Rational
from itertools import chain

from ..pipeline_contracts import Context, Bundle, LineType, DataLine, Substance, Reaction
from ..errors import ParseError

# ========= Utils ========
def toRational(s:str)->Optional[Rational]:
    try:
        return Rational(s)
    except (TypeError,ValueError,ZeroDivisionError):
        raise ParseError(
                explanation=f"Unable to interpret this world as a rational number:",
                hint=s,
                        )

# ========= Parse ========
class State(Enum):
    DEFAULT = auto()
    FORMULA = auto()
    FORMULA_COMPLETE = auto()
    CONTROL = auto()
    INFO = auto()
    MASS = auto()
    BASIS = auto()

class C(Enum):
    UPPER = (str.isupper,)
    LOWER = (str.islower,)
    SPACE = (str.isspace,)
    DIGIT = (lambda c: c.isdigit() or c == '.' or c == '/',)
    ADD = (lambda c:  c == '+',)
    HYPHEN = (lambda c: c == '-',)
    L_ANGLE  = (lambda c: c == '<',)
    R_ANGLE = (lambda c: c == '>',)
    L_BRACKET  = (lambda c: c == '[',)
    R_BRACKET = (lambda c: c == ']',)
    L_PAREN = (lambda c: c == '(',)
    R_PAREN = (lambda c: c == ')',)

    @classmethod
    def detect(cls, c: str)->Optional[C]:
        for t in cls:
            if t.value[0](c):
                return t
        return None


def parse_reaction(raw_reaction:str)-> Optional[Reaction]:
    """ parse reaction reversely """
    reversed_number_cache = []
    reversed_formula_cache = []
    reversed_info_cache = []
    mass_cache = None
    substance_cache = None
    cul_multiplier = Rational(1) 
    multipliers_history = []
    reversed_elements = []
    reversed_stoichs = []
    reversed_reactants = []
    reversed_products = []
    reversed_basis = []
    has_input_mass = False
    product_on_right = None
    all_formulas = set()

    c_it = chain(reversed(raw_reaction),"+ ")
    c = ""
    c_type = None
    last_c = ""
    last_c_type = None
    def c_next():
       nonlocal c, last_c, c_type, last_c_type
       last_c = c
       last_c_type = c_type
       c = next(c_it)
       c_type = C.detect(c)

    state = State.DEFAULT
    try:
        c_next()
        while True:
            # ==== State.DEFAULT ====
            if state is State.DEFAULT:
                if c_type is C.SPACE:
                    c_next()
                elif (c_type is C.DIGIT) or (c_type is C.LOWER) or (c_type is C.UPPER) or (c_type is C.R_PAREN):
                    state = State.FORMULA
                elif c_type is C.R_BRACKET:
                    c_next()
                    state = State.INFO
                elif (c_type is C.R_ANGLE) or (c_type is C.HYPHEN):
                    c_next()
                    state = State.CONTROL
                elif c_type is C.ADD:
                    state = State.FORMULA_COMPLETE
                    c_next()
                else:
                    raise ParseError(
                                     explanation=f"There is a unexpected character '{c}' before '{last_c}'.",
                                     hint="Please check the format of your reaction line.")
            # ==== State.FORMULA ====
            elif state is State.FORMULA:
                if c_type is C.DIGIT:
                    if last_c_type is C.LOWER:
                        if last_c == 'g':
                            state = State.MASS
                        else:
                            raise ParseError(
                                explanation=f"A lowercase letter '{last_c}' appears right after a number '{c}' in the formula.",
                                hint="In a chemical formula, lowercase letters must follow an uppercase letter as part of an element symbol, "
                                    "not a number. Please check your capitalization.")
                    else:
                        reversed_number_cache.append(c)
                        reversed_formula_cache.append(c)
                        c_next()
                elif c_type is C.LOWER:
                    if last_c_type is C.DIGIT:
                        reversed_stoichs.append(Rational(''.join(reversed(reversed_number_cache)))*cul_multiplier)
                        reversed_number_cache = []
                    else:
                        reversed_stoichs.append(cul_multiplier)
                    c_next()
                elif c_type is C.UPPER:
                    if last_c_type is C.LOWER:
                        e = c+last_c
                        reversed_elements.append(e)
                        reversed_formula_cache.append(e)
                    elif last_c_type is C.DIGIT:
                        reversed_elements.append(c)
                        reversed_formula_cache.append(c)
                        reversed_stoichs.append(Rational(''.join(reversed(reversed_number_cache)))*cul_multiplier)
                        reversed_number_cache = []
                    else:
                        reversed_elements.append(c)
                        reversed_formula_cache.append(c)
                        reversed_stoichs.append(cul_multiplier)
                    c_next()
                elif c_type is C.R_PAREN:
                    reversed_formula_cache.append(c)
                    if last_c_type is C.DIGIT:
                        multipliers_history.append(cul_multiplier)
                        cul_multiplier *= Rational(''.join(reversed(reversed_number_cache)))
                        reversed_number_cache = []
                    elif last_c_type is C.LOWER:
                        raise ParseError(
                            explanation=f"A lowercase letter '{last_c}' appears right after right parenthesis '{c}' in the formula.",
                            hint="In a chemical formula, lowercase letters must follow an uppercase letter as part of an element symbol, "
                                "not a right parenthesis. Please check your capitalization.")
                       
                    c_next()
                elif c_type is C.L_PAREN:
                    reversed_formula_cache.append(c)
                    try:
                        cul_multiplier=multipliers_history.pop()
                    except IndexError:
                        raise ParseError(
                            explanation="Detected an opening parenthesis '(' that is never closed.",
                            hint="Make sure all parentheses are balanced.",)
                    if last_c_type is C.LOWER:
                        raise ParseError(
                            explanation=f"A lowercase letter '{last_c}' appears right after left parenthesis '{c}' in the formula.",
                            hint="In a chemical formula, lowercase letters must follow an uppercase letter as part of an element symbol, "
                                "not a left parenthesis. Please check your capitalization.")
                    c_next()
                elif c_type is C.SPACE:
                    if last_c_type is C.LOWER:
                        if last_c == 'g':
                            state = State.MASS
                        else:
                            raise ParseError(
                                explanation=f"A lonely lowercase letter '{last_c}' exists in the formula.",
                                hint=f"In a chemical formula, lowercase letters must follow an uppercase letter as part of an element symbol.")
                    elif last_c_type is C.DIGIT:
                        formula = "".join(reversed(reversed_formula_cache))
                        raise ParseError(
                                hint=f"Unexpected space before '{formula}'. Please write a complete chemical formula here."
                                )
                    else:
                        c_next()
                elif c_type is C.R_BRACKET:
                    if last_c_type is C.LOWER:
                        raise ParseError(
                            explanation=f"A lonely lowercase letter '{last_c}' appears after the bracket '['.",
                            hint=f"In a chemical formula, lowercase letters must follow an uppercase letter as part of an element symbol.")
                    elif last_c_type is C.DIGIT:
                        formula = "".join(reversed(reversed_formula_cache))
                        raise ParseError(
                                hint=f"Unexpected bracket ']' before '{formula}'. Please write a complete chemical formula here."
                                )
                    
                    state = State.INFO
                    c_next()
                else:
                    if last_c_type is C.LOWER:
                        raise ParseError(
                            explanation=f"A lonely lowercase letter '{last_c}' exists in the formula.",
                            hint=f"In a chemical formula, lowercase letters must follow an uppercase letter as part of an element symbol.")
                    elif last_c_type is C.DIGIT:
                        lonely_number = "".join(reversed(reversed_number_cache))
                        raise ParseError(
                            explanation=f"A number '{lonely_number}' appears in a formula without a preceding element or bracket.",
                            hint="Numbers in a chemical formula must follow an element symbol or a closing bracket.")
                    elif multipliers_history:
                        raise ParseError(
                            explanation="Unmatched closing parenthesis ')' detected in the reaction formula.",
                            hint="Each ')' must have a matching '(' before it.")
                    state = state.FORMULA_COMPLETE
                    
                    
            # ==== State.FORMULA_COMPLETE ====
            elif state is State.FORMULA_COMPLETE:
                if reversed_formula_cache:
                    elements_stoich = {}
                    for element,stoich in zip(reversed(reversed_elements),reversed(reversed_stoichs)):
                        elements_stoich[element] = elements_stoich.setdefault(element,Rational(0)) + stoich
                    if product_on_right is None:
                        reversed_reactants.append(
                            Substance(
                                formula="".join(reversed(reversed_formula_cache)),
                                info = "".join(reversed(reversed_info_cache)),
                                elements_stoich=elements_stoich,
                                input_mass=mass_cache,
                            )
                        )
                    else:   
                        reversed_products.append(
                            Substance(
                                formula="".join(reversed(reversed_formula_cache)),
                                info = "".join(reversed(reversed_info_cache)),
                                elements_stoich=elements_stoich,
                                input_mass=mass_cache,
                            )
                        )
                    reversed_formula_cache = []
                    reversed_info_cache = []
                    reversed_elements = []
                    reversed_stoichs = []
                    mass_cache = None
                state = State.DEFAULT
                
            # ==== State.MASS ====
            elif state is State.MASS:
                if (last_c_type is C.LOWER) and (reversed_number_cache):
                    raise ParseError(
                        explanation="Unexpected number detected after the mass unit 'g'.",
                        hint="The mass unit 'g' must appear at the end of the number, "
                            "without any digits following it.\n")
                elif c_type is C.DIGIT:
                    reversed_number_cache.append(c)
                    c_next()
                elif (c_type) is C.SPACE and (not reversed_number_cache):
                    c_next()
                elif c_type is C.LOWER or c_type is C.UPPER:
                    raise ParseError(
                        explanation="A space is missing between the formula and its mass value.",
                        hint="Please add a space before the mass unit to avoid ambiguity.")
                else:
                    if mass_cache is None:
                        mass_cache = toRational(''.join(reversed(reversed_number_cache)))
                        reversed_number_cache = []
                    else:
                        raise ParseError(
                            explanation="Multiple mass values detected for the same substance.",
                            hint="Each substance should have only one mass value.")
                    
                    state = State.FORMULA_COMPLETE

            # ==== State.CONTROL ====
            elif state is State.CONTROL:
                if last_c_type is C.HYPHEN:
                    if c_type is C.L_ANGLE:
                        if product_on_right is None:
                            product_on_right = True
                            c_next()
                            state = State.DEFAULT
                        else:
                            raise ParseError(
                                explanation="You writed more than one reaction arrow(<- or ->).",
                                hint="Each reaction should have exactly one arrow indicating direction. "
                                    "For example: '- A + B -> C' or '- C <- A + B'.",)
                    else:
                        raise ParseError(
                            explanation="A reaction arrow seems incomplete or malformed.",
                            hint="Use a full arrow '<-' or '->' to indicate the reaction direction.\n"
                                "Examples:\n"
                                "  '- A + B -> C'\n"
                                "  '- C <- A + B'",)
                elif last_c_type is C.R_ANGLE:
                    if c_type is C.HYPHEN:
                        if product_on_right is None:
                            product_on_right = False
                            c_next()
                            state = State.DEFAULT
                        else:
                            raise ParseError(
                                explanation="You writed more than one reaction arrow(<- or ->).",
                                hint="Each reaction should have exactly one arrow indicating direction. "
                                    "For example: '- A + B -> C' or '- C <- A + B'.",)
                    else:
                        state = State.BASIS
                # no other branch

            # ==== State.INFO ====
            elif state is State.INFO:
                if c_type is C.L_BRACKET:
                    state = State.FORMULA
                else:
                    reversed_info_cache.append(c)
                c_next()
            # ==== State.BASIS ====
            elif state is State.BASIS:
                if c_type is C.UPPER:
                    if last_c_type is C.LOWER:
                        reversed_basis.append(c+last_c)
                    elif last_c_type is C.UPPER:
                        reversed_basis.append(last_c)
                    c_next()
                elif c_type is C.LOWER:
                    if last_c_type is not C.LOWER:
                        c_next()
                    else:

                        raise ParseError(
                            explanation="Invalid element symbol detected inside angle brackets.",
                            hint="Each element symbol should start with an uppercase letter "
                                "optionally followed by a single lowercase letter.",)

                elif c_type is C.L_ANGLE:
                    c_next()
                    state = State.FORMULA
                elif c_type is C.SPACE:
                    if last_c_type is C.LOWER:
                        raise ParseError(
                                explanation="Invalid element symbol in the basis <...>:",
                                hint=last_c
                                )
                    c_next()
                else:
                    raise ParseError(
                        hint="Illegal character(s) inside angle brackets '<...>' or missing '<' as open.",
                        )
    # ==== StopIteration ====
    except StopIteration:
        if state is not State.DEFAULT:
            raise ParseError(
                explanation="Unmatched closing bracket ']' detected.",
                hint="Every closing bracket must have a corresponding opening one.\n",)
        
        if product_on_right is None:
            raise ParseError(
                explanation="No reaction arrow ('->' or '<-') was found in this line.",
                hint="Each reaction must include one arrow to indicate direction.\n"
                    "Examples:\n"
                    "  '- A + B -> C'\n"
                    "  '- C <- A + B'",)
        elif not product_on_right:
            reversed_products, reversed_reactants = reversed_reactants, reversed_products

        if len(reversed_products) != 1:
            product_formulas = (product.formula for product in reversed(reversed_products))
            raise ParseError(
                explanation="This program is designed for synthesis (combination) reactions with a single product. Try to keep only one of these:",
                hint=", ".join(product_formulas)
                )


        if reversed_basis:
            basis = dict.fromkeys(reversed(reversed_basis))
        else:
            basis = reversed_products[0].elements_stoich
            

        # let's go!
        return Reaction(
                    raw_reaction,
                    reversed_products[0],
                    list(reversed(reversed_reactants)),
                    basis,
                )

# ========== Stage =========
class ParseStage:
    """ Parse the reaction line """
    def process(self, bundle: Bundle)->Bundle:
        datalines = bundle.stream

        def stream():
            for dataline in datalines:
                if dataline.line_type is LineType.REACTION:
                    try:
                        raw_reaction = dataline.data
                        dataline.data = parse_reaction(raw_reaction)
                    except ParseError as e:
                        e = ParseError(
                                raw_reaction,
                                explanation=e.explanation,
                                hint=e.hint,
                                )
                        print(e)
                        continue
                yield dataline

        return Bundle(context=bundle.context, stream=stream())
