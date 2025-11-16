English | [中文文档](https://github.com/ponyofshadows/balancer/blob/master/README.zh-CN.md)

# reaction-balancer
A precise chemical-equation balancer that uses exact rational arithmetic and CIAAW atomic weights to generate printable reaction preparation sheets (Excel format) from Markdown input.
---

## Features

### 1. Exact scientific computation  
- Uses **CIAAW (2024)** standard atomic weights.  
- All internal math uses **sympy.Rational** (exact fractions), eliminating floating-point errors.  
- Linear algebra–based solver ensures **correct balancing** or gives an informative error if impossible.

### 2. Flexible input syntax  
- Supports parentheses and fractional subscripts:  
  - `Ni(NO3)2(H2O)6`  
  - `Fe7/8Se`  
  - `La1.8Sr0.2CuO4.12`  
- Optional basis specification (e.g., <BaTiO>) allows partial balancing, which is useful for sol–gel and oxide-precursor routes.

### 3. Automatic Excel output  
- Produces a **ready-to-print xlsx recipe sheet** with formatted layout.  
- Column widths, styles, and alignment handled automatically—no manual editing required.

### 4. Reproducible and traceable  
- Input is a Markdown document, allowing you to record:  
  - sample IDs  
  - furnace schedule  
  - experimental notes  
- Perfect for lab notebooks and long-term traceability.

### 5. Designed for materials synthesis  
Suitable for:  
- solid-state reactions  
- flux growth  
- hydrothermal / sol-gel precursor balancing  
- cuprates, pnictides, nickelates, chalcogenides, and general inorganic synthesis

---

## Installation
```bash
pip install balancer
```
or if using uv:
```bash
uv tool install balancer
```

## Usage
Run this command in a directory:
```bash
python -m balancer
# or use uv:
# uv run balancer
```
If `input.md` is missing, the program automatically creates a template in your working directory.

You may also specify an explicit filepath:
```bash
balancer <filepath>
```
