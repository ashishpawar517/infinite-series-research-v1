# Infinite Series Calculation Context

This context defines the core mathematical and computational concepts for the Ramanujan Infinite Series Engine, which computes arbitrary-precision approximations of mathematical constants using infinite series.

## Language

**Ramanujan's pi formula**:
The specific infinite series identity for 1/pi discovered by Srinivasa Ramanujan that converges rapidly, providing approximately 8 correct decimal digits per term.
_Avoid_: Ramanujan pi series, Ramanujan's formula for pi

**Partial sum (S_N)**:
The sum of the first N terms of an infinite series, where N is the term count (summing indices 0 through N-1).
_Avoid_: Series sum, finite sum, summation

**Term (t_n)**:
The nth summand in an infinite series, specifically in Ramanujan's formula: t_n = c_n × (1103 + 26390×n) where c_n = (4n)!/(n!)⁴/396^(4n).
_Avoid_: Summand, series term, series element

**Coefficient (c_n)**:
The factorial-based coefficient in Ramanujan's formula: c_n = (4n)!/(n!)⁴/396^(4n), which can be computed efficiently via recurrence to avoid large intermediate factorials.
_Avoid_: Factorial coefficient, series coefficient

**Working precision**:
The number of decimal digits used in intermediate arbitrary-precision calculations, which may exceed the requested output precision to prevent rounding errors.
_Avoid_: Precision, decimal precision, calculation precision

**Analytic truncation-error bound**:
A mathematically proven upper bound on the error introduced by truncating an infinite series after a finite number of terms, derived from the series' convergence properties.
_Avoid_: Error bound, truncation bound, error estimate

**Convergence trace**:
A record of partial sums at successive term counts, used to analyze and visualize how the series approximation approaches its limit.
_Avoid_: Partial sum history, sum history, convergence history

**Term count (N)**:
The number of series terms to evaluate in the partial sum S_N = Σₙ₌₀ᴺ⁻¹ t_n, where terms=1 means only n=0 is evaluated.
_Avoid_: Number of terms, series length, iteration count

**Formula identifier**:
A unique string naming a specific infinite series implementation (e.g., "Ramanujan's pi formula") used for result tracking and cataloging.
_Avoid_: Formula name, series name, series identifier

**Arbitrary precision**:
Computation using numbers with user-specifiable precision rather than fixed-width floating-point formats, enabling calculations limited only by available memory and time.
_Avoid_: High precision, extended precision, big numbers