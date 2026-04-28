---
name: sympy-symbolic-math
description: "Symbolic math in Python: exact algebra, calculus (derivatives, integrals, limits), equation solving, symbolic matrices, ODEs, code gen (lambdify, C/Fortran). Use for exact symbolic results. For numerical use numpy/scipy; for stats use statsmodels."
license: BSD-3-Clause
---

# SymPy — Symbolic Mathematics

## Overview

SymPy is a Python library for symbolic mathematics that performs exact computation using mathematical symbols rather than numerical approximations. It covers algebra, calculus, equation solving, linear algebra, physics, and code generation — all within pure Python with no external dependencies.

## When to Use

- Solving equations symbolically (algebraic, systems, differential equations)
- Performing calculus operations (derivatives, integrals, limits, series expansions)
- Simplifying and manipulating algebraic expressions
- Working with matrices symbolically (eigenvalues, determinants, decompositions)
- Converting symbolic expressions to fast numerical functions (lambdify → NumPy)
- Generating code from math expressions (C, Fortran, LaTeX)
- Needing exact results (e.g., `sqrt(2)` not `1.414...`)
- For **numerical computing** (array operations, linear algebra on data), use numpy/scipy
- For **statistical modeling** (regression, hypothesis testing), use statsmodels

## Prerequisites

```bash
pip install sympy
# Optional for numerical evaluation:
pip install numpy matplotlib
```

SymPy is pure Python — no compiled dependencies, installs everywhere.

## Quick Start

```python
from sympy import symbols, solve, diff, integrate, sqrt, pi

x = symbols('x')

# Solve equation
print(solve(x**2 - 5*x + 6, x))          # [2, 3]

# Derivative
print(diff(x**3 + 2*x, x))                # 3*x**2 + 2

# Integral
print(integrate(x**2, (x, 0, 1)))         # 1/3

# Exact arithmetic
print(sqrt(8))                              # 2*sqrt(2)
print(pi.evalf(30))                        # 3.14159265358979323846264338328
```

## Core API

### 1. Symbols and Expressions

Create symbolic variables and manipulate expressions.

```python
from sympy import symbols, Symbol, Rational, S, oo, pi, E, I
from sympy import simplify, expand, factor, collect, cancel, trigsimp

# Define symbols
x, y, z = symbols('x y z')

# With assumptions (improve simplification)
n = symbols('n', integer=True)
t = symbols('t', positive=True, real=True)
from sympy import sqrt
print(sqrt(t**2))   # t (not Abs(t), because t is positive)

# Exact fractions (avoid floats!)
expr = Rational(1, 3) * x + S(1)/7
print(expr)  # x/3 + 1/7

# Simplification
print(simplify(x**2 + 2*x + 1))          # (x + 1)**2
print(expand((x + 1)**3))                 # x**3 + 3*x**2 + 3*x + 1
print(factor(x**3 - x))                   # x*(x - 1)*(x + 1)
print(collect(x*y + x - 3 + 2*x**2 - z*x**2, x))  # x**2*(2 - z) + x*(y + 1) - 3
```

### 2. Calculus

Derivatives, integrals, limits, and series.

```python
from sympy import symbols, diff, integrate, limit, series, oo, sin, cos, exp, log

x = symbols('x')

# Derivatives
print(diff(sin(x**2), x))                 # 2*x*cos(x**2)
print(diff(x**4, x, 3))                   # 24*x (third derivative)

# Partial derivatives
x, y = symbols('x y')
f = x**2 * y**3
print(diff(f, x, y))                      # 6*x*y**2

# Integrals
x = symbols('x')
print(integrate(x**2, x))                 # x**3/3 (indefinite)
print(integrate(exp(-x**2), (x, -oo, oo)))  # sqrt(pi) (Gaussian)
print(integrate(x * exp(-x), (x, 0, oo)))  # 1

# Limits
print(limit(sin(x)/x, x, 0))             # 1
print(limit((1 + 1/x)**x, x, oo))        # E

# Taylor series
print(series(exp(x), x, 0, 5))           # 1 + x + x**2/2 + x**3/6 + x**4/24 + O(x**5)
```

### 3. Equation Solving

Algebraic, transcendental, and differential equations.

```python
from sympy import symbols, solve, solveset, Eq, S, linsolve, nonlinsolve, Function, dsolve

x, y = symbols('x y')

# Single equation
print(solve(x**2 - 4, x))                 # [-2, 2]
print(solveset(x**2 - 4, x, S.Reals))     # {-2, 2}

# System of linear equations
print(linsolve([x + y - 5, 2*x - y - 1], x, y))  # {(2, 3)}

# System of nonlinear equations
print(nonlinsolve([x**2 + y - 4, x + y**2 - 4], x, y))

# Differential equation: y'' + y = 0
f = Function('f')
ode = f(x).diff(x, 2) + f(x)
print(dsolve(ode, f(x)))                  # Eq(f(x), C1*sin(x) + C2*cos(x))

# With initial conditions
from sympy import Derivative
ics = {f(0): 1, f(x).diff(x).subs(x, 0): 0}
print(dsolve(ode, f(x), ics=ics))         # Eq(f(x), cos(x))
```

### 4. Matrices and Linear Algebra

Symbolic matrix operations.

```python
from sympy import Matrix, eye, zeros, ones, diag, symbols

# Create matrices
M = Matrix([[1, 2], [3, 4]])
print(f"Det: {M.det()}")                   # -2
print(f"Inverse:\n{M**-1}")

# Symbolic matrices
a, b = symbols('a b')
M = Matrix([[a, b], [b, a]])
print(f"Eigenvalues: {M.eigenvals()}")     # {a - b: 1, a + b: 1}

# Eigenvectors and diagonalization
eigendata = M.eigenvects()
# [(eigenval, multiplicity, [eigenvectors]), ...]
P, D = M.diagonalize()
print(f"M = P*D*P^-1")

# Solve linear system Ax = b
A = Matrix([[1, 2], [3, 4]])
b = Matrix([5, 6])
x = A.solve(b)
print(f"Solution: {x.T}")

# Matrix calculus
t = symbols('t')
M_t = Matrix([[t, t**2], [1, t]])
print(f"dM/dt:\n{M_t.diff(t)}")
```

### 5. Code Generation

Convert symbolic expressions to fast numerical functions or compiled code.

```python
import numpy as np
from sympy import symbols, lambdify, sin, exp, ccode, fcode, latex

x, y = symbols('x y')
expr = sin(x) * exp(-x**2 / 2)

# lambdify: symbolic → fast NumPy function
f = lambdify(x, expr, 'numpy')
x_vals = np.linspace(-5, 5, 1000)
y_vals = f(x_vals)
print(f"Shape: {y_vals.shape}, Max: {y_vals.max():.4f}")

# Multi-variable lambdify
expr2 = x**2 + y**2
f2 = lambdify((x, y), expr2, 'numpy')
print(f"f(3, 4) = {f2(3, 4)}")            # 25

# C code generation
print(ccode(expr))                          # sin(x)*exp(-1.0/2.0*pow(x, 2))

# Fortran code generation
print(fcode(expr))

# LaTeX output
print(latex(expr))                          # \sin{\left(x \right)} e^{- \frac{x^{2}}{2}}
```

### 6. Physics Module

Classical mechanics, vector analysis, and units.

```python
from sympy import symbols, cos, sin, Function
from sympy.physics.mechanics import dynamicsymbols, LagrangesMethod, Particle, Point, ReferenceFrame
from sympy.physics.vector import dot, cross

# Vector analysis
N = ReferenceFrame('N')
v1 = 3*N.x + 4*N.y + 0*N.z
v2 = 1*N.x + 0*N.y + 2*N.z
print(f"Dot: {dot(v1, v2)}")               # 3
print(f"Cross: {cross(v1, v2)}")            # 8*N.x - 6*N.y - 4*N.z

# Simple pendulum via Lagrangian mechanics
q = dynamicsymbols('q')       # Generalized coordinate (angle)
m, g, l = symbols('m g l', positive=True)
T = Rational(1, 2) * m * (l * q.diff())**2          # Kinetic energy
V = m * g * l * (1 - cos(q))                         # Potential energy
L = T - V                                            # Lagrangian
print(f"Lagrangian: {L}")
```

## Key Concepts

### Exact vs Numerical Arithmetic

```python
from sympy import Rational, S, sqrt, pi

# WRONG: introduces floating-point error
expr_bad = 0.5 * x           # Float 0.5, loses exactness

# CORRECT: exact symbolic arithmetic
expr_good = Rational(1, 2) * x    # Exact 1/2
expr_good = S(1)/2 * x            # Alternative exact syntax
expr_good = x / 2                  # Also exact

# Numerical evaluation when needed
print(sqrt(2).evalf())         # 1.41421356237310
print(pi.evalf(50))            # 50 digits of precision
```

### Solver Selection Guide

| Solver | Use When | Returns |
|--------|----------|---------|
| `solve(eq, x)` | General purpose, legacy | List of solutions |
| `solveset(eq, x, domain)` | Algebraic equations (preferred) | Set (may be infinite) |
| `linsolve(system, vars)` | Linear systems | FiniteSet of tuples |
| `nonlinsolve(system, vars)` | Nonlinear systems | FiniteSet of tuples |
| `dsolve(ode, f(x))` | Ordinary differential equations | Equality (Eq) |
| `nsolve(eq, x0)` | Numerical root finding | Float approximation |

### Common Simplification Functions

| Function | Does | Example |
|----------|------|---------|
| `simplify()` | General simplification (slow, tries everything) | `sin(x)**2 + cos(x)**2` → `1` |
| `expand()` | Distribute multiplication | `(x+1)**2` → `x**2+2*x+1` |
| `factor()` | Factor into irreducibles | `x**2-1` → `(x-1)*(x+1)` |
| `collect()` | Group by variable | Collect terms in `x` |
| `cancel()` | Cancel common factors in fractions | `(x**2-1)/(x-1)` → `x+1` |
| `trigsimp()` | Simplify trig expressions | Faster than `simplify` for trig |
| `powsimp()` | Simplify powers/exponentials | Combine `x**a * x**b` |

## Common Workflows

### Workflow: Symbolic-to-Numeric Pipeline

```python
from sympy import symbols, diff, integrate, lambdify, sin, cos
import numpy as np
import matplotlib.pyplot as plt

x = symbols('x')

# 1. Define expression symbolically
f_expr = sin(x) * cos(x)**2

# 2. Symbolic operations
f_prime = diff(f_expr, x)
F_expr = integrate(f_expr, x)
print(f"f(x) = {f_expr}")
print(f"f'(x) = {f_prime}")
print(f"F(x) = {F_expr}")

# 3. Convert to fast numerical functions
f_num = lambdify(x, f_expr, 'numpy')
f_prime_num = lambdify(x, f_prime, 'numpy')
F_num = lambdify(x, F_expr, 'numpy')

# 4. Evaluate and plot
x_vals = np.linspace(0, 2*np.pi, 500)
fig, axes = plt.subplots(1, 3, figsize=(12, 4))
axes[0].plot(x_vals, f_num(x_vals)); axes[0].set_title('f(x)')
axes[1].plot(x_vals, f_prime_num(x_vals)); axes[1].set_title("f'(x)")
axes[2].plot(x_vals, F_num(x_vals)); axes[2].set_title('F(x)')
plt.tight_layout()
plt.savefig('symbolic_pipeline.png', dpi=150)
print("Saved symbolic_pipeline.png")
```

### Workflow: Solve and Verify

```python
from sympy import symbols, solve, simplify, Eq, sqrt

x = symbols('x')

# 1. Define equation
equation = x**3 - 6*x**2 + 11*x - 6

# 2. Solve symbolically
solutions = solve(equation, x)
print(f"Solutions: {solutions}")            # [1, 2, 3]

# 3. Verify each solution
for sol in solutions:
    result = simplify(equation.subs(x, sol))
    assert result == 0, f"Solution {sol} failed!"
    print(f"  x={sol}: f(x) = {result} ✓")

# 4. Factor the polynomial
from sympy import factor
print(f"Factored: {factor(equation)}")      # (x - 1)*(x - 2)*(x - 3)
```

### Workflow: ODE System Analysis

1. Define the ODE using `Function` and `dsolve()`
2. Solve symbolically; apply initial conditions with `ics={}` parameter
3. Convert solution to numerical function with `lambdify()`
4. Plot the solution trajectory with matplotlib

## Key Parameters

| Parameter | Function | Default | Options | Effect |
|-----------|----------|---------|---------|--------|
| `domain` | `solveset()` | `S.Complexes` | `S.Reals`, `S.Integers` | Restrict solution domain |
| `force` | `simplify()` | False | True/False | Aggressive simplification |
| `n` | `diff(expr, x, n)` | 1 | 1–∞ | Order of derivative |
| Precision | `evalf(n)` | 15 | 1–1000+ | Digits of numerical precision |
| Backend | `lambdify()` | "math" | "numpy", "scipy", "mpmath" | Numerical backend for evaluation |
| `rational` | `nsimplify()` | True | True/False | Find exact rational approximation |

## Best Practices

1. **Always use `Rational()` or `S()` for fractions**: `0.5 * x` introduces floats that break exact computation. Use `Rational(1, 2) * x` or `S(1)/2 * x`.

2. **Add assumptions to symbols**: `symbols('x', positive=True)` enables simplifications like `sqrt(x**2) → x`. Without assumptions, SymPy must handle the general complex case.

3. **Use `lambdify` for numerical evaluation, not `subs().evalf()`**: `subs/evalf` in a loop is 100-1000x slower than a single `lambdify` call.
   ```python
   # Slow: [expr.subs(x, v).evalf() for v in values]
   # Fast: f = lambdify(x, expr, 'numpy'); f(np.array(values))
   ```

4. **Anti-pattern — using `simplify()` as default**: `simplify()` is slow because it tries many strategies. Use specific functions (`factor`, `expand`, `trigsimp`) when you know the desired form.

5. **Prefer `solveset` over `solve` for algebraic equations**: `solveset` returns proper mathematical sets and handles edge cases better. `solve` is legacy but still useful for general cases.

6. **Anti-pattern — solving symbolically when numerical is sufficient**: For equations with no closed-form solution, use `nsolve(eq, x0)` for numerical root finding instead of waiting for `solve` to fail.

7. **Use `init_printing()` in Jupyter for readable output**: `from sympy import init_printing; init_printing()` enables LaTeX rendering in notebooks.

## Common Recipes

### Recipe: Generate LaTeX Documentation

```python
from sympy import symbols, Integral, Eq, latex, sqrt, pi

x = symbols('x')
integral = Integral(x**2 * sqrt(1 - x**2), (x, 0, 1))
result = integral.doit()

print(f"$$ {latex(integral)} = {latex(result)} $$")
# $$ \int\limits_{0}^{1} x^{2} \sqrt{1 - x^{2}}\, dx = \frac{\pi}{16} $$
```

### Recipe: Parametric ODE Solution

```python
from sympy import symbols, Function, dsolve, Eq, exp, lambdify
import numpy as np

x = symbols('x')
k, A = symbols('k A', positive=True)
f = Function('f')

# Solve y' = -ky with y(0) = A
ode = Eq(f(x).diff(x), -k * f(x))
solution = dsolve(ode, f(x), ics={f(0): A})
print(f"Solution: {solution}")              # f(x) = A*exp(-k*x)

# Evaluate for specific parameters
f_num = lambdify((x, k, A), solution.rhs, 'numpy')
x_vals = np.linspace(0, 5, 100)
y_vals = f_num(x_vals, k=0.5, A=10)
print(f"y(5) = {y_vals[-1]:.4f}")
```

### Recipe: Symbolic Matrix Decomposition

```python
from sympy import Matrix, symbols, pprint

a, b, c, d = symbols('a b c d')
M = Matrix([[a, b], [c, d]])

# Characteristic polynomial
lam = symbols('lambda')
char_poly = M.charpoly(lam)
print(f"Characteristic polynomial: {char_poly.as_expr()}")

# Eigenvalues (symbolic)
eigenvals = M.eigenvals()
print(f"Eigenvalues: {eigenvals}")

# Determinant and trace
print(f"det(M) = {M.det()}")               # a*d - b*c
print(f"tr(M) = {M.trace()}")              # a + d
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `NameError: name 'x' is not defined` | Symbol not created | Define with `x = symbols('x')` before use |
| Unexpected float results | Using `0.5` instead of `Rational(1,2)` | Use `Rational()` or `S()` for exact fractions |
| `simplify()` very slow | Trying all strategies on complex expr | Use specific function: `factor()`, `expand()`, `trigsimp()` |
| `solve()` returns empty list | No closed-form solution exists | Use `nsolve(eq, x0)` for numerical approximation |
| `sqrt(x**2)` returns `sqrt(x**2)` not `x` | No assumption on `x` | Define `x = symbols('x', positive=True)` |
| `lambdify` wrong results | Expression has SymPy-specific functions | Specify backend: `lambdify(x, expr, 'numpy')` or `'scipy'` |
| `NotImplementedError` in `dsolve` | ODE type not supported | Try numerical ODE solver (scipy `odeint`) instead |

## Related Skills

- **matplotlib-scientific-plotting** — plot symbolic results after lambdify conversion
- **statsmodels-statistical-modeling** — statistical inference; use when you need p-values, not exact algebra
- **matlab-scientific-computing** — MATLAB alternative for numerical (not symbolic) computing

## References

- [SymPy documentation](https://docs.sympy.org/) — official API reference and tutorials
- [SymPy tutorial](https://docs.sympy.org/latest/tutorials/intro-tutorial/index.html) — introduction for new users
- [SymPy GitHub](https://github.com/sympy/sympy) — source code, examples, and issues
- Meurer et al. (2017) "SymPy: symbolic computing in Python" — [PeerJ Computer Science](https://doi.org/10.7717/peerj-cs.103)
