from __future__ import annotations
from typing import Optional, Iterator, Iterable
from functools import reduce
from sympy import Matrix, Rational, Integer, lcm, gcd, symbols, linsolve, S, Interval, Union
from sympy.solvers.inequalities import reduce_rational_inequalities

from ..atomic_mass import Element
from ..pipeline_contracts import Context,Bundle,LineType, DataLine, Substance, SubstanceResult, Reaction, ReactionResult
from ..errors import ComputeError

# ======== Compute ======== 
def to_vector(basis:dict[str,Optional[Rational]],elements_stoich:dict[str,Rational])->Matrix:
    return Matrix([elements_stoich.get(e, Rational(0)) for e in basis])

def non_negative(stoichs:Iterable[Rational])->bool:
    for stoich in stoichs:
        if stoich < 0:
            return False
    return True

def solve_reaction(reactant_matrix:Matrix, product_vector:Matrix, reaction:Reaction)->list[Rational]:
    x = symbols(f'x0:{reactant_matrix.cols}')
    sol_set = linsolve((reactant_matrix, product_vector), x)
    sol_non_negative = True

    if sol_set:
        sol = list(sol_set.args[0])
        if not sol_set.free_symbols:
            sol_non_negative = non_negative(sol)

        elif len(sol_set.free_symbols) == 1:
            (free_symbol,) = tuple(sol_set.free_symbols)
            inequalities = [expr>=0 for expr in sol]
            iq_sol_set = reduce_rational_inequalities([inequalities], free_symbol)

            if iq_sol_set in (S.EmptySet, S.false, False):
                # S.EmptySet: solution set is empty
                # S.False:    False after bool reduce
                sol = [expr.subs(free_symbol, S.Zero) for expr in sol]
                sol_non_negative = False
            else:
                # Find a simple solution in the set
                if hasattr(iq_sol_set, "as_set"):
                    iq_sol_set = iq_sol_set.as_set()
                
                if isinstance(iq_sol_set, Interval):
                    infimum = iq_sol_set.inf
                # Defensive programming
                elif isinstance(iq_sol_set, Union):
                    candidates = []
                    for iv in iq_sol_set.args:
                        if iv.inf is S.NegativeInfinity:
                            if iv.sup == S.Infinity:
                                candidates.append(S.Zero)
                            else:
                                candidates.append(iv.sup)
                        else:
                            candidates.append(iv.inf)
                    infimum = min(candidates)
                # Defensive programming * 2
                else:
                    #fallback to zero
                    infimum = S.Zero
                    sol_non_negative = False

                sol = [expr.subs(free_symbol, infimum) for expr in sol]
                    

        else:
            reactant_formulas = (reactant.formula for reactant in reaction.reactants)
            raise ComputeError(
                    explanation="Too many unnessary reactants, which lead to more than 1 free variables in the solution. Please remove some from these:",
                    hint=", ".join(reactant_formulas)
                    )

        sol.append(Rational(1))
        if sol_non_negative:
            return sol
        else:
            sol = normalize_ratio(sol)
            for i,stoich in enumerate(sol):
                if stoich == 1:
                    sol[i] = ""
                elif stoich == -1:
                    sol[i] = "-"
                
            reactant_formulas = [reactant.formula for reactant in reaction.reactants]
            product_formula = reaction.product.formula
            raise ComputeError(
                    explanation="No non-negative solution. A solution is:",
                    hint=" ".join((
                        f"{sol[0]}{reactant_formulas[0]}",
                        *((f"+ {stoich}{formula}").replace("+ -", "- ") for stoich,formula in zip(sol[1:-1],reactant_formulas[1:])),
                        "===",
                        f"{sol[-1]}{product_formula}"
                        )
                    ))

    else:
        # just no solution
        # maybe the user writed wrong Element symbols?
        basis_elements = set(reaction.basis)
        reactant_elements = set().union(
                *(reactant.elements_stoich for reactant in reaction.reactants)
                )
        product_elements = set(reaction.product.elements_stoich)
        
        elements_not_in_reactant = basis_elements - reactant_elements
        elements_not_in_product = basis_elements - product_elements
        if elements_not_in_reactant:
            raise ComputeError(
                explanation="These required elements are missing from the reactants:",
                hint=", ".join(elements_not_in_reactant)
            )
        if elements_not_in_product:
             raise ComputeError(
                explanation="These required elements are missing from the product:",
                hint=", ".join(elements_not_in_product)
            )           

        raise ComputeError(
            hint="This chemical equation has no valid stoichiometric solution.",
        )

        

    
def normalize_ratio(stoichs:list(Rational))->list(Integer):
    """
        lcm: least common multiple
        gcd: greast common divisor
        p: numerator
        q: denominator
    """
    lcm_of_denominator = reduce(lcm,
                                [n.q for n in stoichs if n!=0]
                                )
    integerized = [n * lcm_of_denominator for n in stoichs]
    gcd_of_integers = reduce(gcd,integerized)
    return [n / gcd_of_integers for n in integerized]

def mole_mass(elements_stoich:dict[str,Rational])->Rational:
    try:
        return sum([Rational(Element[e].value) * n for e,n in elements_stoich.items()])
    except KeyError as e:
            raise ComputeError(
                explanation=f"Unknown element symbol encountered:",
                hint=e.args[0]
            )

def mass(stoichs:list, mole_masses:list, input_masses:iterator[Optional[Rational]])->list[Rational]:
    for i,input_mass in enumerate(input_masses):
        if input_mass is not None:
            if stoichs[i]==0:
                match i:
                    case 0:
                        num = f"{i+1}-st"
                    case 1:
                        num = f"{i+1}-nd"
                    case 2:
                        num = f"{i+1}-rd"
                    case _:
                        num = f"{i+1}-th"

                raise ComputeError(
                        hint=f"You provided an input mass for the {num} reactant, but its stoichiometric coefficient in the balanced equation is zero."
                        )
            eq_mole = input_mass / mole_masses[i] / stoichs[i]
            break
    else:
        raise ComputeError(
            explanation="No input mass was provided for any reactant or product.",
            hint="Please write mass in grams (g) near the product or one of the reactants."
            )

    return [eq_mole * stoich * mole_mass for stoich,mole_mass in zip(stoichs,mole_masses)]




def balancer(reaction:Reaction)->Optional[ReactionResult]:
    basis = reaction.basis
    reactant_cnt = len(reaction.reactants)
    reactant_matrix = Matrix.hstack(*[to_vector(basis, reactant.elements_stoich) for reactant in reaction.reactants])
    product_vector = to_vector(basis, reaction.product.elements_stoich)
    reactant_product_stoich = solve_reaction(
            reactant_matrix,
            product_vector,
            reaction
            )

    reactant_product_stoich=normalize_ratio(reactant_product_stoich)
    reactant_product_mole_mass = [mole_mass(s.elements_stoich) for s in reaction]
    reactant_product_mass = mass(
                                 reactant_product_stoich,
                                 reactant_product_mole_mass,
                                 (substance.input_mass for substance in reaction),
                                )

    # ok!
    *reactants_mole_mass, product_mole_mass = reactant_product_mole_mass
    *reactants_stoich, product_stoich = reactant_product_stoich
    *reactants_mass, product_mass = reactant_product_mass

    return ReactionResult(
            SubstanceResult(
                reaction.product.formula,
                reaction.product.info,
                product_mole_mass,
                product_stoich,
                product_mass,
                ),
            [
                SubstanceResult(
                    reactant.formula,
                    reactant.info,
                    mole_mass,
                    stoich,
                    mass)
                for reactant,mole_mass,stoich,mass
                in zip(
                    reaction.reactants,
                    reactants_mole_mass,
                    reactants_stoich,
                    reactants_mass
                    )
                ],
            )

    
    
# ======== Stage ========
class ComputeStage:
    """ balance the reaction """
    def process(self, bundle: Bundle)->Bundle:
        datalines=bundle.stream

        def stream():
            for dataline in datalines:
                if dataline.line_type is LineType.REACTION:
                    raw_reaction = dataline.data.raw
                    try:
                        dataline.data = balancer(dataline.data)
                    except ComputeError as e:
                        e = ComputeError(
                                raw_reaction,
                                explanation=e.explanation,
                                hint=e.hint,
                                )
                        print(e)
                        continue
                yield dataline

        return Bundle(context=bundle.context, stream=stream())
