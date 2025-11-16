> This is a comment line. Lines starting with `>` are ignored.

# Example Recipe Sheet

FE-1024-1
    - La0.9FeAsO 1 g <- La2O3 + Fe + As + La
Ni-1024-1   Balance using only La and Ni.
    - <LaNi> La3Ni2O7 2g <- La2(NO3)3 + Ni(NO3)2(H2O)6 
Precursor-FE-1024
    - FeSe <- Fe[Inno Chem 3N] + 5.4321g Se[Alfa 5N]

> A separator line (`---`, `___`, or `***`) ends the current recipe.
---


# Another Example
> Only The first recipe sheet will be read by the program
- 0.2131 g I2 + Nb + Se -> NbSe2I1/6
- CaO+CuO->CaCuO2 0.7g

---
> ***Syntax Summary***
> # Title
> Lines starting with `# `(the Spaces is necessary) set the title of the recipe (used as the output Excel filename).
> The default file name is the current date

> - Reaction line  
> Must start with `- `. The reaction arrow can be `->` or `<-`.
> Mass must be written next to at least one of the chemical formulas. If multiple masses are written, the program will take into account the mass of the first reactant

> Normal Line (line without prefix)
> Normal Line will be written into the output table just as it is.
