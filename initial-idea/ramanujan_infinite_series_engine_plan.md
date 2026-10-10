# Ramanujan Infinite Series Engine — Project Plan

**Purpose:** Build a reliable arbitrary-precision engine for evaluating infinite series, starting with Ramanujan's rapidly convergent series for \(1/\pi\), then expand it into a research workbench that proposes and tests candidate series representations for supplied constants.

**Audience:** Codex (implementation agent) and the project owner.

**Recommended first step:** Implement Milestone 1 only, run the test suite, and report the files changed and any decisions that need approval. Do not attempt to implement the entire research roadmap in one pass.

---

## 1. Product vision

The project has two connected parts:

1. **Series computation engine:** evaluate finite truncations of infinite series at configurable arbitrary precision, record partial sums, analyse convergence, and stop according to an explicit term limit or a defensible error criterion.
2. **Series discovery workbench:** given a high-precision representation of a constant, search within declared mathematical families for candidate identities, rank them, and validate them at higher precision. Candidates must be labelled as conjectures until mathematically proved.

The long-term aspiration is to explore Ramanujan-style formulas and other structured series. The project must not claim that an algorithm can automatically find a useful identity for every arbitrary constant. The discovery system can only search the formula families, parameter ranges, and precision budget it is given.

## 2. Project principles

- **Correctness before speed.** Establish trusted benchmark tests before optimisation.
- **Arbitrary precision.** Use `mpmath` or an equivalent arbitrary-precision library; do not route important values through Python `float`.
- **Never hide uncertainty.** Distinguish an exact formula, a numerical approximation, a heuristic convergence indicator, an analytic truncation bound, and a proven identity.
- **No unsafe expression evaluation.** The MVP registers formulas as Python implementations. Do not use `eval()` or execute arbitrary user-supplied code or strings.
- **Small, testable milestones.** Complete the numerical core before adding a frontend or automated discovery.
- **Reproducibility.** Record formula identifiers, settings, algorithm version, term count, and precision with each result.

## 3. Scope

### MVP — include now

- Python package with a reusable series-evaluation API.
- Ramanujan's well-known series for \(1/\pi\), implemented using a recurrence rather than repeated large factorial calculations.
- Configurable number of terms and decimal working precision.
- Partial-sum / convergence trace suitable for later charting.
- Formula-specific analytic truncation bound for Ramanujan's positive-term series, if implemented as described in Section 5. Clearly document that this bound does not rigorously cover finite-precision rounding error.
- Command-line interface (CLI).
- Unit tests, benchmark tests against `mpmath`'s high-precision value of \(\pi\), basic documentation, and reproducible examples.

### Later milestones — design for, but do not implement yet

- Registry/catalogue of multiple known series for constants such as \(\pi\), \(e\), and \(\zeta(2)\).
- More convergence diagnostics and acceleration methods, each with documented applicability and limitations.
- A bounded discovery pipeline using PSLQ/integer-relation searches and constrained formula-family exploration.
- Candidate scoring based on independent numerical validation, convergence rate, complexity, and parameter simplicity.
- Research notes, citations, candidate history, and exportable results.
- Optional API and interactive frontend with convergence plots.

### Explicitly out of scope for the MVP

- Automatically proving arbitrary mathematical identities.
- Claiming that every decimal constant has a discoverable “interesting” series.
- Arbitrary user-defined code execution or a general-purpose mathematical expression parser.
- GPU/distributed computation or million-digit optimisation.
- A web UI before the core library and CLI are reliable.

## 4. Mathematical benchmark: Ramanujan's formula for \(\pi\)

Implement this identity:

\[
\frac{1}{\pi}=\frac{2\sqrt{2}}{9801}\sum_{n=0}^{\infty}
\frac{(4n)!(1103+26390n)}{(n!)^4 396^{4n}}.
\]

Define

\[
c_n=\frac{(4n)!}{(n!)^4 396^{4n}},\qquad c_0=1.
\]

The recurrence is

\[
c_{n+1}=c_n\frac{(4n+1)(4n+2)(4n+3)(4n+4)}{(n+1)^4 396^4}.
\]

The term at index \(n\) is \(t_n=c_n(1103+26390n)\). For a requested term count \(N\), sum indices \(0\) through \(N-1\), then calculate

\[
\pi_N=\frac{9801}{2\sqrt{2}\sum_{n=0}^{N-1}t_n}.
\]

**Indexing requirement:** `terms=1` means evaluate only index `n=0`; `terms=2` means evaluate `n=0,1`. Explain this in CLI help and tests.

### Optional analytic tail bound for this formula

The summands are positive. For every \(n\ge 0\), a conservative upper bound on the ratio of consecutive terms is

\[
q=\frac{256}{396^4}\left(1+\frac{26390}{1103}\right)<1.
\]

This follows by bounding each factor \((4n+k)/(n+1)\le 4\), for \(k=1,2,3,4\), and bounding the linear factor ratio by \(1+26390/1103\). If \(S_N=\sum_{n=0}^{N-1}t_n\), the remaining sum \(T_N=\sum_{n=N}^{\infty}t_n\) satisfies

\[
0\le T_N\le B_N=\frac{t_N}{1-q}.
\]

Let \(K=9801/(2\sqrt{2})\). Since \(\pi=K/(S_N+T_N)\) and \(\pi_N=K/S_N\), the truncation error obeys

\[
0\le \pi_N-\pi\le \frac{K B_N}{S_N^2}.
\]

Implement this bound only if the derivation and implementation are covered by tests and documentation. Name it an **analytic truncation-error bound**. Do not label the displayed value as a fully rigorous total numerical error bound, because the MVP does not rigorously bound arbitrary-precision rounding error. Use a higher working precision than the requested display precision where useful, and explain the distinction in docs.

## 5. Recommended technical stack

- **Language:** Python 3.11+ (unless an existing repository already specifies a supported version).
- **Numerics:** `mpmath` for arbitrary-precision arithmetic and reference constants.
- **Testing:** `pytest`.
- **Packaging:** `pyproject.toml`.
- **Typing/style:** use type hints; add a formatter/linter only if the repository already uses one or it can be added without complicating the MVP.
- **Frontend:** none in Milestone 1. Expose a clean Python API and CLI first.

Use a local/isolated precision context where practicable so one calculation does not unexpectedly change precision for another caller. If the chosen implementation uses `mpmath`'s global context, wrap precision changes in a context manager and document that the MVP is single-process/synchronous.

## 6. Proposed repository structure

Adapt to an existing repository if present; do not overwrite existing project conventions without a reason.

```text
ramanujan-infinite-series-engine/
├── pyproject.toml
├── README.md
├── src/
│   └── ramanujan_engine/
│       ├── __init__.py
│       ├── models.py              # result/configuration dataclasses and status enums
│       ├── evaluator.py           # generic finite-term summation and diagnostics
│       ├── cli.py                 # CLI entry point
│       ├── formulas/
│       │   ├── __init__.py
│       │   └── ramanujan_pi.py    # recurrence and pi transform
│       └── discovery/             # reserved for later; do not implement in MVP
├── tests/
│   ├── test_ramanujan_pi.py
│   ├── test_evaluator.py
│   └── test_cli.py
├── docs/
│   ├── mathematics.md             # formula, recurrence, bounds, caveats
│   └── roadmap.md                 # future discovery work
└── notebooks/                     # optional research experiments later
```

Avoid creating empty placeholder modules unless they provide value. It is fine to begin with fewer files and split them only when there is a concrete need.

## 7. API and data model requirements

Create a small, documented API, with names that fit the actual implementation. The exact class layout is flexible, but the observable behaviour must satisfy these requirements.

### Configuration

- `terms`: positive integer; required or given a sensible documented default.
- `precision`: positive integer decimal digits; default around 50–80 for the CLI.
- Optional `trace` setting to collect partial-sum values for plotting.
- Optional target tolerance only if the evaluator can report what kind of estimate it is using.

Reject invalid inputs with a useful `ValueError` or CLI error message. Reject booleans where an integer is expected if the value is used as a term count or precision.

### Evaluation result

Return a structured result (not only a formatted string) that includes, at minimum:

- formula identifier/name;
- approximated value as an `mpmath` number internally;
- terms evaluated;
- working precision;
- final raw partial sum, where meaningful;
- final term magnitude, where meaningful;
- optional trace of selected term counts and approximations;
- optional analytic truncation-error bound and an explicit label for its meaning;
- elapsed time if easily available;
- status/reason the calculation stopped.

String formatting should happen in the CLI/output layer. Use `mp.nstr` or equivalent for display rather than converting the result to `float`.

### Generic engine boundary

The generic evaluator should not assume every series is positive, convergent, or has a usable error bound. For MVP, it may support fixed-term computation and attach formula-specific diagnostics. A future tolerance-based stopping option must state whether it uses a proved/analytic tail bound or only a heuristic based on small terms. Do not report a heuristic as a guarantee.

## 8. CLI requirements

Expose a command similar to:

```bash
python -m ramanujan_engine pi --terms 3 --precision 80
```

Support:

- `pi` formula command;
- `--terms N`;
- `--precision DIGITS`;
- `--json` for machine-readable structured output, if straightforward in Milestone 1;
- `--trace` to print or emit the convergence trace, if straightforward.

Human-readable output should show the formula name, approximation, number of terms, working precision, and any analytic truncation bound. If showing observed error against `mpmath.pi`, label it as a **benchmark/reference error** because this is possible only for this known formula. Do not treat reference comparison as a generic engine capability.

Example usage and output belong in the README. CLI help must explain that “terms” is a count, not the last index.

## 9. Implementation milestones

### Milestone 1 — Working numerical MVP

Tasks:

1. Inspect the existing repository and preserve existing conventions, if any.
2. Set up or adapt package metadata and test infrastructure.
3. Implement Ramanujan's coefficient recurrence and term generation.
4. Implement the evaluator/result structure and precision handling.
5. Implement the pi transform and, if feasible, the analytic truncation bound described in Section 4.
6. Add CLI commands and readable output; add JSON output if it remains simple.
7. Write unit tests and benchmark tests.
8. Write README usage and a mathematical note covering the formula and limitations.
9. Run the full test suite and report results.

**Acceptance criteria:**

- `terms=1` produces a value close to `3.14159273001330566`.
- `terms=2` produces a value close to `3.14159265358979388`.
- `terms=3` is substantially more accurate than `terms=2` and agrees with `mpmath.pi` to the expected precision for this formula.
- Increasing the number of terms reduces the observed error for the tested first few term counts.
- Increasing working precision allows a correspondingly more precise result without accidental conversion to machine `float`.
- Invalid terms and precision values fail clearly.
- CLI works from a clean environment using documented install/run instructions.
- Tests include recurrence-vs-direct-factorial comparisons for small indices, guarding against recurrence/indexing mistakes.
- If a truncation bound is implemented, tests verify it safely exceeds the observed reference error across several small term counts at higher working precision. Tests are evidence against bugs, not a replacement for the mathematical derivation.

### Milestone 2 — Formula catalogue and comparisons

- Add several independently documented formulas for well-known constants.
- Give each formula metadata: identifier, expression, domain/assumptions, source, implementation method, convergence properties, available tail bound, and whether the identity is mathematically established.
- Provide a benchmark report comparing accuracy gained per term and elapsed time. Be careful when comparing formulas that compute different transformed series.
- Add tests for every formula and avoid adding formulas without trustworthy references and expected-value checks.

### Milestone 3 — Discovery prototype

Start with a narrow, explicitly constrained research task rather than a universal “formula generator.”

Candidate pipeline:

1. Accept a target as a decimal **string** with declared precision and optional context/name. A decimal string alone does not tell the system which mathematical constant it represents.
2. Allow the user to provide a basis of known constants (for example \(1,\pi,e,\sqrt{2}\)) and run a bounded PSLQ/integer-relation search.
3. Search only configured candidate families and small parameter/coefficient ranges initially. Store the family definition and constraints with each run.
4. Recompute each candidate using more precision than was used for fitting. When the target has sufficient digits, reserve digits or use an independent higher-precision target for validation to reduce overfitting.
5. Rank candidates using a transparent score: numerical residual on validation digits, convergence rate, formula complexity, coefficient size, parameter simplicity, and computational cost.
6. Store the candidate formula, search settings, residual, validation precision, stopping reasons, source family, and proof status.
7. Label results **numerical candidate / conjecture**, **symbolically verified under stated assumptions**, or **proved**, as appropriate. Never infer “proved” from numerical agreement alone.

Important limitation: PSLQ searches for integer relations among numbers supplied to it. It can suggest identities relative to a chosen basis but cannot by itself produce arbitrary infinite-series identities. More sophisticated Ramanujan–Sato discovery involves modular forms, modular functions, and symbolic proof techniques; treat this as a separate long-term research track rather than a simple parameter optimiser.

### Milestone 4 — Research interface (optional)

Only after the library/CLI is useful:

- Add interactive partial-sum/convergence plots.
- Show term count, precision, formula, result, and bound labels together.
- Compare formulas side by side.
- Support saving and exporting reproducible experiments.
- Consider a small API if a separate frontend needs it; keep mathematical logic in the core package.

## 10. Test strategy

### Unit tests

- Validate term count and precision.
- Verify recurrence coefficients against a direct factorial formula for several small values of \(n\).
- Verify the first few summands and partial sums.
- Verify the transformation from the partial sum to \(\pi_N\).
- Verify output precision/formatting without conversion through `float`.
- Verify trace indices and trace lengths.

### Numerical regression tests

- Compare values against `mpmath.pi` at sufficiently high working precision.
- Assert sensible error ranges for 1, 2, 3, and 4 terms; avoid overly brittle exact string comparisons.
- Test that observed error decreases for the initial term counts.
- Test at more than one working precision.

### CLI tests

- Default command works.
- Explicit term count and precision are applied.
- Invalid arguments display clear errors and nonzero exit status.
- JSON output parses and represents high-precision values as strings, not JSON floating-point numbers.

### Bound tests (if implemented)

- Check the ratio bound has `q < 1`.
- Check the bound is non-negative and decreases as more terms are included.
- Against high-precision reference runs, check that the analytic truncation bound exceeds the observed truncation error with a generous test margin.
- Document that ordinary `mpmath` arithmetic is not interval arithmetic and this does not bound every rounding error.

## 11. Numerical correctness and edge cases

- Never form large factorials for the Ramanujan computation; use the recurrence.
- Create constants in the arbitrary-precision context (for example by dividing context-aware values) instead of first calculating expressions in binary floating point.
- Keep `terms` semantics consistent everywhere: exactly `N` summands, starting at index zero.
- Do not assume terms becoming small proves convergence for a general series.
- Do not assume alternating-series error bounds apply unless the mathematical conditions are established.
- Avoid runaway trace memory for huge term counts. Provide trace-off/trace sampling or a documented maximum trace size before exposing very large scales.
- Add reasonable CLI validation and friendly exceptions; don't swallow numerical errors silently.

## 12. Documentation requirements

The README should explain:

- What the project does and what it does not claim to do.
- Environment/install requirements.
- At least two copy-pasteable CLI examples.
- How to import and call the Python API.
- What “precision” and “terms” mean.
- Difference between a partial-sum approximation, a heuristic estimate, an analytic truncation bound, and a proof.
- How to add a new trusted formula without changing the generic evaluator.

`docs/mathematics.md` should include the full Ramanujan identity, recurrence derivation, index convention, and any implemented tail-bound derivation.

## 13. Research references

Use these as starting points, verify formulas and API details against the current installed library version, and add formula-specific primary sources as the catalogue grows:

- **mpmath documentation (arbitrary precision and numerical tools):** https://mpmath.org/doc/current/
- **mpmath summation and convergence acceleration:** https://mpmath.org/doc/current/calculus/sums_limits.html
- **mpmath number identification and PSLQ:** https://mpmath.org/doc/current/identification.html
- **Computer-assisted construction of Ramanujan–Sato series for \(1/\pi\), Ramanujan Journal (published 26 February 2026):** https://doi.org/10.1007/s11139-026-01352-2

The last paper is an advanced research direction, not a requirement for the MVP. Its construction uses modular forms/functions and symbolic algorithms; do not imply that its full methodology is implemented by the initial discovery prototype.

## 14. Instructions to Codex for the first implementation

When given this plan:

1. Inspect the repository first. Summarise its current state briefly before making changes.
2. Implement **Milestone 1 only** unless the user explicitly asks to continue further.
3. Keep the code small and readable. Avoid premature abstractions and unnecessary dependencies.
4. Implement the recurrence formula exactly as written and include tests comparing it with the direct definition for small indices.
5. Use arbitrary precision end to end and preserve results as strings in JSON output.
6. Be explicit about what an error estimate does and does not guarantee.
7. Run tests and relevant lint/type checks available in the repository. Do not claim they passed if they were not run.
8. Finish with a concise report: implemented features, files changed, commands run, test results, known limitations, and the recommended next task.
9. If a requirement conflicts with the current repository structure, preserve the working architecture and explain the adaptation instead of blindly replacing files.

**Definition of done for the first Codex run:** a working Python package and CLI that evaluates Ramanujan's pi formula to an arbitrary requested precision for a user-specified number of terms, with automated tests and clear documentation of the numerical guarantees and limitations.
