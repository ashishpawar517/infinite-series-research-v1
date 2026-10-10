# Ramanujan Series Research Program: Plan for Agent Teams

**Audience:** Claude Code sessions and sub-agent teams, plus the project owner.
**Companion document:** `ramanujan_infinite_series_engine_plan.md` (engineering plan, Milestones 1 to 4). This document does not replace it. It adds the research layer: questions, tracks, roles, protocols and evidence standards. Where the two disagree on engineering detail, the engineering plan wins. Where they disagree on how claims are labelled or verified, this document wins.

---

## 1. Mission

Build a reliable arbitrary-precision engine for infinite series, then use it as an experimental workbench to study one question:

> Given a constant (or an expression built from known constants), what infinite series converge to it, and which of those are *structured and fast* rather than trivial?

Two connected deliverables:

1. **Forward engine:** evaluate a registered series to a requested precision, with a convergence trace and an honest error statement.
2. **Reverse engine:** given a target, propose candidate series, validate them at higher precision than they were fitted at, rank them, and label their evidential status.

The project is **not** claiming that every constant has an interesting series, or that any search finds one. Every discovery claim is bounded by the families, parameter ranges and precision budget that were searched.

## 2. Ground rules for every agent

1. **Evidence labels are mandatory.** Every result carries exactly one status (see section 5). Never upgrade a status from numerical agreement alone.
2. **Arbitrary precision end to end.** Use `mpmath` (or `flint`/`gmpy2` backed equivalents later). Never route a result through Python `float`. Results are serialized as decimal **strings**.
3. **No `eval()` and no execution of user-supplied code.** Formulas are registered Python implementations. Any expression input goes through a hand-written parser with a fixed grammar.
4. **Recurrences, not factorials.** Compute hypergeometric terms by ratio recurrence.
5. **Separate fitting from validation.** A candidate is found at one precision and checked at a strictly higher one, with digits that were not used in the fit.
6. **Record negative results.** A family that yields nothing is a result. Log it with its search bounds.
7. **No unverified citations.** Do not cite a paper, theorem or formula from memory as fact. Either find the primary source, or mark it `unverified-recollection` in the notes and keep it out of the catalogue until a numerical check passes.
8. **Reproducibility.** Every experiment stores the command, library versions, precision, seed (if any) and algorithm version.
9. **Small changes, owned areas.** One agent owns each directory at a time (section 7). Do not edit another agent's area; open a handoff note instead.
10. **Human gates.** Ask the project owner before: adding a dependency, labelling anything `proved`, publishing a claim outside the repo, or spending more than the compute budget in section 10.

## 3. Current state (as of this document)

**Exists, prototype quality (do not build on without review):**

- `ramanujan_engine.py`: single-file prototype.
  - Evaluates Ramanujan 1914, Chudnovsky and Ramanujan 4/pi series.
  - `discover()` searches hypergeometric families `t(k) = (s1)_k (s2)_k (s3)_k / k!^3 * z^k` for `1/c = a*S0 + b*S1` using PSLQ.
  - Run on pi it rediscovered three known series:
    - `s=1/2, z=1/4`: `1/pi = sum t(k) (6k+1)/4`
    - `s=1/2, z=1/64`: `1/pi = sum t(k) (42k+5)/16`
    - `s=1/4, z=-1/4`: `1/pi = sum t(k) (20k+3)/8`
- `reverse_series_dashboard.html`: browser dashboard (published artifact). Parses an expression and shows series as typeset math.
  - Structured series: binomial series for square roots; Ramanujan, Chudnovsky and Machin series for rational multiples of pi or 1/pi.
  - Universal but trivial series: exponential (`sum (ln x)^n / n!`) and Engel expansion.
  - Runs in double precision, so it is limited to about 15 digits.

**Known defects of the prototypes (must be fixed in the real package):**

- Computes large factorials directly; mutates global `mp.dps`; no result objects, tests, CLI or tail bound.
- `discover()` fits and validates at the same precision, so it can overfit, and it reports hits as results rather than conjectures.
- The candidate `z` grid (small unit fractions) cannot reach the Chudnovsky `z`, which is about `1/151931373056000` (see Track D).
- Dashboard is double precision only and has no link to the Python engine.

**Verified numerical facts (checked with `mpmath`, 60 digits):**

- Ramanujan recurrence equals the direct factorial definition for `n = 0..5`.
- With `K = 9801/(2*sqrt(2))`: `terms=1 -> 3.14159273001330566...`, `terms=2 -> 3.14159265358979388...`, `terms=3` matches pi to about 24 digits.
- Tail-bound ratio `q = (256/396^4)(1 + 26390/1103) ~ 2.59e-7 < 1`, and the analytic bound exceeded the observed error for 1 to 5 terms (tight to about 4 digits).

## 4. Research questions

Each question has an owner track (section 6) and a falsifiable success condition.

| ID | Question | Success condition |
|----|----------|-------------------|
| Q1 | Can the pipeline rediscover known Ramanujan-type series for `1/pi` from only the target and a family definition? | All three series above plus at least 5 more from the literature, found with no hints, each validated at 3x the fit precision. |
| Q2 | Does extending the family (higher-order hypergeometric terms, polynomial numerators of degree 2+) recover known results for `1/pi^2` and related constants? | Rediscover at least one known `1/pi^2` formula (for example a Guillera-type series with `(1/2)_n^5 / n!^5` terms). The exact formula must be looked up and numerically confirmed before it enters the benchmark set. |
| Q3 | Can the `z` parameter be generated from theory (singular values of the j-invariant) instead of blind grid search? | For each class-number-1 discriminant, derive `z = 1728/j(tau)` and recover the corresponding Ramanujan-Sato series by PSLQ. Reproduce Chudnovsky's constants from `D = -163`. |
| Q4 | For which other constants (`zeta(3)`, Catalan, `log 2`, `sqrt 2`) do rapidly convergent, structured series exist in the searched families? | Either validated candidates, or a documented negative result with the exact search bounds. |
| Q5 | Can "interesting" be defined operationally so the reverse engine ranks structured series above trivial ones? | A scoring function (section 8) that places Ramanujan/Chudnovsky above exponential/Engel on every benchmark, with a written rationale. |
| Q6 | Can numerically found candidates be proven (or reduced to a known proof) with WZ/Zeilberger-style methods? | At least one candidate promoted to `symbolic_verified` with an independent derivation trail. |

## 5. Evidence statuses

Every candidate, formula and claim has exactly one status:

| Status | Meaning |
|--------|---------|
| `numerical_candidate` | Matches the target to the fit digits only. A conjecture. |
| `validated_candidate` | Also matches on held-out digits at higher precision, and was reproduced by a **different agent** from the stored record. |
| `symbolically_verified` | Checked symbolically under stated assumptions (for example, a recurrence identity verified with a CAS). |
| `proved` | Proof exists and has been reviewed by the project owner. Agents may propose this status but never assign it. |
| `known_literature` | Established result from a verified primary source, re-checked numerically in this repo. |
| `refuted` | Fails validation, with the failing precision recorded. |

A bound on truncation error must be named an **analytic truncation-error bound** and must state that it does not cover rounding error.

## 6. Research tracks

| Track | Name | Goal | Depends on |
|-------|------|------|-----------|
| A | Numerical core | Plan Milestone 1: recurrence-based Ramanujan engine, result objects, tail bound, CLI, tests | none |
| B | Catalogue and literature | Plan Milestone 2: formulas with metadata, sources and expected-value tests; reading notes | A |
| C | Discovery in hypergeometric families | Generalize PSLQ search (Q1, Q2, Q4) with fit/validation split | A |
| D | Modular construction | Generate `z` from singular values of j (Q3); Ramanujan-Sato series | A, B |
| E | Conjecture generation | Ramanujan-Machine-style search over polynomial continued fractions and recurrences (Apery-like) | A, C |
| F | Proof and verification | WZ pairs, Zeilberger, CAS cross-checks (Q6); independent re-verification of all candidates | B, C |
| G | Reverse engine | Expression to ranked series; taxonomy of trivial vs structured (Q5) | A, B, C |
| H | Dashboard and reporting | Plan Milestone 4: UI backed by the Python library | A, G |

**Dependency order:** A first. Then B and C in parallel. D, E and F start once their dependencies reach a usable state. G consumes B, C and D. H is last and must not contain mathematical logic.

### Track notes

**A. Numerical core.** Follow the engineering plan exactly. Add: context-managed precision (no global leakage), trace sampling for huge term counts, and a generic hypergeometric-term generator `t(n+1)/t(n)` that Tracks B, C and D reuse.

**B. Catalogue and literature.** Each formula gets a record: identifier, TeX, domain, source (verified), implementation method, digits per term, tail bound if any, status. Starting set, each re-checked numerically before inclusion: Ramanujan 1914, Chudnovsky, Machin, the three rediscovered 1/pi series, Apery's zeta(3) series, BBP-type formulas. Reading list is in section 11.

**C. Discovery.** Upgrade `discover()`:

- Fit at P digits; validate at 3P digits with independent recomputation.
- PSLQ basis: `[1/c, S0, S1, S2, ...]` for polynomial degree up to a configurable bound; also allow user-supplied constant bases such as `{1, pi, sqrt(2), log 2}`.
- Families declared as data: Pochhammer parameter triples/quintuples, `z` generator, polynomial degree, coefficient bound.
- Every run writes a search manifest (family, ranges, counts tried, hits, near-misses).
- Report **false-positive rate**: run each search against random targets and decoys (for example `pi + 1e-30`, `pi*1.000001`) and record how often PSLQ returns spurious relations at the chosen `maxcoeff`.

**D. Modular construction.** Benchmark: reproduce Chudnovsky from `D = -163`, then the other class-number-1 discriminants. In the `(1/6, 1/2, 5/6)` family, Chudnovsky's `z` is `1728/j` with `j = -640320^3`, i.e. `z ~ -1/151931373056000`. Plan: compute `j(tau)` for CM points with `mpmath` (`kleinj`), set `z = 1728/j`, run PSLQ for `(a, b)`. Then extend to levels 2, 3 and 4. This track is theory-heavy; it must not claim a general theorem. Treat the published 2026 construction cited in the engineering plan as a reading target (verify the DOI before citing).

**E. Conjecture generation.** Search polynomial continued fractions `a_n, b_n` of small degree and small integer coefficients for limits matching target constants, then check convergence and recurrence structure. High false-positive risk: require validation at high precision and an independent reproduction. Optional track; do not start before C has a stable fit/validation protocol.

**F. Proof and verification.** Two responsibilities:

1. For each `validated_candidate`, an agent that did not discover it re-derives the numbers from the stored record only (no shared code path beyond the term generator).
2. Attempt symbolic or WZ-style proofs for selected candidates. Record the method, the tool versions and where the argument stops being automatic.

**G. Reverse engine.** Input: expression (fixed-grammar parser) or a decimal string plus a declared constant basis. Pipeline:

1. Normalize the target to arbitrary precision.
2. Structure detection: rational, square-root form (as in the dashboard), rational multiple of `pi` or `1/pi`, member of a supplied basis.
3. Candidate generation from the catalogue (Track B) and discovery (Track C).
4. Always include universal trivial series (exponential, Engel) but **tag them** `trivial_universal`.
5. Score and rank (section 8); output TeX plus metadata.

**H. Dashboard.** Reads results from the Python library (JSON, high-precision values as strings). Shows formula, status label, digits per term, validation precision, and a convergence plot labelled as benchmark/reference error where a reference value is used. No new mathematical logic in the frontend.

## 7. Agent roles and ownership

Run as a small team under one orchestrator. Roles map to tracks; a single Claude Code session may play several roles sequentially, but **author and independent verifier must never be the same agent for a candidate**.

| Role | Owns (directory) | Responsibilities |
|------|------------------|------------------|
| Orchestrator | `research/STATUS.md`, task board | Splits work, assigns tracks, merges handoffs, enforces gates, keeps the status file current |
| Numerics engineer | `src/ramanujan_engine/` core, `tests/` | Track A; keeps all numerical code correct and tested |
| Literature analyst | `catalogue/`, `research/notes/` | Track B; finds primary sources, writes reading notes, builds catalogue records |
| Discovery experimentalist | `src/.../discovery/`, `research/experiments/` | Tracks C and E; runs searches, writes manifests and experiment logs |
| Theory researcher | `research/theory/` | Track D; modular and CM constructions, derivations |
| Verifier | `research/verification/` | Track F; reproduces candidates independently, attempts proofs, red-teams claims |
| Reverse-engine developer | `src/.../reverse/` | Track G |
| Frontend developer | `dashboard/` | Track H |

**Handoffs.** Write `research/handoffs/<from>-to-<to>-<date>.md` with: what was done, files changed, commands to reproduce, open questions, and what the receiver should do first. The receiver confirms by committing a one-line reply in the same file.

**Parallelism guidance for the orchestrator.** Safe to run concurrently: B with C; D with F (after A); G and H once B and C expose stable interfaces. Do not run two agents on the same directory. Sub-agents get a self-contained brief (goal, inputs, outputs, evidence rules, stop condition); do not rely on them inheriting conversation context.

## 8. Candidate record schema and ranking

Store each candidate as one YAML (or JSON) file under `research/candidates/`:

```yaml
id: pi-hyp-s12-z1_64-001
target: {name: "1/pi", value: "<decimal string>", digits: 200}
family: {pochhammer: [1/2, 1/2, 1/2], z: "1/64", poly_degree: 1}
series_tex: "\\frac{1}{\\pi} = \\sum_{n\\ge 0} \\frac{(1/2)_n^3}{n!^3}\\,\\frac{42n+5}{16\\cdot 64^n}"
coefficients: {a: "5/16", b: "21/8"}
fit_digits: 60
validation_digits: 180
residual_validation: "<decimal string>"
digits_per_term: 1.8
status: validated_candidate
found_by: discovery-agent-1
verified_by: verifier-agent-2
algorithm_version: "discover-0.3"
environment: {python: "3.11", mpmath: "<version>"}
search_manifest: research/experiments/2026-10-xx-pi-family-sweep.md
references: []
notes: ""
```

**Ranking (Q5) starts transparent and simple.** Score components, each reported separately before being combined:

- validation residual (digits matched beyond the fit);
- digits gained per term (convergence rate);
- formula complexity (number of Pochhammer factors, polynomial degree);
- coefficient and parameter size;
- computational cost per digit.

Tag every candidate `structured` or `trivial_universal`. A universal series must never outrank a structured one purely because its coefficients are small. Tune weights only against the benchmark set (Ramanujan, Chudnovsky, Machin, Apery) and write down the rationale.

## 9. Experiment log protocol

One file per experiment: `research/experiments/YYYY-MM-DD-<slug>.md`.

```markdown
# <title>
- Hypothesis:
- Track / agent / date:
- Setup: family definition, ranges, precision (fit and validation), seeds
- Command: <exact command>
- Environment: python, mpmath, commit hash
- Results: hits, near-misses, counts tried, runtime
- Controls: decoy targets and false-positive count
- Conclusion: supported / not supported / inconclusive
- Status changes: candidate ids and new statuses
- Next steps:
```

An experiment without controls cannot move a candidate beyond `numerical_candidate`.

## 10. Quality gates, phases and budgets

| Phase | Scope | Exit criteria |
|-------|-------|---------------|
| R0 Foundation | Track A, plan Milestone 1 | Tests pass; acceptance values in the engineering plan reproduced; tail-bound tests pass; README states precision and bound caveats |
| R1 Baseline | Track B | Catalogue with at least 8 formulas, each with source and expected-value test |
| R2 Rediscovery | Track C (Q1, Q2) | Q1 success condition met; false-positive rates documented |
| R3 Theory-guided | Track D (Q3) | Chudnovsky reproduced from `D = -163`; at least 3 further discriminants |
| R4 Reverse engine | Track G (Q5) | Ranking separates structured from trivial on all benchmarks; reproducible JSON output |
| R5 Interface | Track H | Dashboard reads library output; labels and bounds shown with every result |
| R6 Extension | Tracks E and F (Q4, Q6) | Documented results (positive or negative) for at least two further constants; at least one verified derivation |

**Compute budget default:** any single experiment above 1 CPU-hour, or any run needing more than 2000 digits, needs orchestrator approval; above 24 CPU-hours needs owner approval. Record actual usage in the experiment log.

**Definition of done for any task:** code merged with tests passing; docs updated; experiment log or handoff written; statuses updated; commands to reproduce included; limitations listed.

## 11. Reading list (verify each before relying on it)

These are starting points recalled from the literature. Verify authors, years and formulas against the primary source before adding anything to the catalogue.

- S. Ramanujan, "Modular equations and approximations to pi" (1914): the original 17 series.
- J. Borwein and P. Borwein, *Pi and the AGM* (1987).
- D. and G. Chudnovsky, work on series for pi and rational-multiple constants (late 1980s).
- N. D. Baruah, B. C. Berndt, H. H. Chan, "Ramanujan's series for 1/pi: a survey", *Amer. Math. Monthly* (2009).
- S. Cooper, *Ramanujan's Theta Functions* (2017): Ramanujan-Sato series at higher levels.
- J. Guillera, work on Ramanujan-like series for `1/pi^2`.
- H. R. P. Ferguson and D. H. Bailey, PSLQ; D. H. Bailey, P. Borwein, S. Plouffe, BBP formula (1997).
- M. Petkovsek, H. S. Wilf, D. Zeilberger, *A = B* (1996): Zeilberger, WZ.
- G. Raayoni et al., "Generating conjectures on fundamental constants with the Ramanujan Machine", *Nature* (2021).
- mpmath documentation: summation, `identify`, `pslq`, `kleinj`.
- The 2026 *Ramanujan Journal* paper on computer-assisted construction of Ramanujan-Sato series for 1/pi, cited in the engineering plan (DOI as given there; check it resolves before citing).

## 12. Repository layout (target)

```text
ramanujan-series-research/
├── CLAUDE.md                     # short rules block, see below
├── pyproject.toml
├── README.md
├── src/ramanujan_engine/         # engine, formulas, discovery, reverse
├── tests/
├── catalogue/                    # one record per trusted formula
├── dashboard/                    # frontend only (Track H)
├── docs/                         # mathematics.md, roadmap.md
└── research/
    ├── STATUS.md                 # orchestrator-maintained board
    ├── notes/                    # reading notes with source verification status
    ├── experiments/              # section 9 logs
    ├── candidates/               # section 8 records
    ├── theory/                   # derivations
    ├── verification/             # independent reproductions and proof attempts
    └── handoffs/
```

### Suggested `CLAUDE.md` block

```markdown
# Rules for agents in this repo
- Read research/STATUS.md and docs/roadmap.md before starting. Work only in the directory you own.
- Arbitrary precision only (mpmath). No float, no eval. Serialize values as strings.
- Every result gets exactly one evidence status. Never assign `proved`.
- Fit at P digits, validate at >= 3P digits. Include decoy/control runs.
- Never cite from memory. Verify sources or mark `unverified-recollection`.
- The author of a candidate cannot be its verifier.
- Log every experiment (research/experiments/) including negative results.
- Ask the owner before: new dependencies, `proved` claims, external publication, compute above budget.
- Finish every task with: files changed, commands run, test results, limitations, next task.
```

## 13. Risks and honest limits

- **False positives from PSLQ.** With enough digits and a big enough basis, spurious relations appear. Controls and held-out validation are the defence.
- **Search-space illusion.** A family may contain no interesting series for a given constant. Report the search bounds with every negative result.
- **Trivial series dressed up as discoveries.** Exponential and Engel expansions exist for every positive real. They are not findings.
- **Theory gap.** Fast Ramanujan-Sato series come from modular forms, not blind search. Track D is where real progress on the reverse problem is most likely; Track C alone will mostly rediscover known results.
- **Rounding error.** `mpmath` arithmetic is not interval arithmetic. Truncation bounds do not bound rounding error; use extra working precision and, later, interval arithmetic (`mpmath.iv`) for stronger claims.
- **Frontend drift.** The double-precision dashboard prototype must not be presented as the engine's output.

## 14. First actions for the orchestrator

1. Create the repository layout in section 12 and commit this plan and the engineering plan under `docs/`.
2. Launch Track A (Numerics engineer) on Milestone 1 of the engineering plan. Do not start other tracks' code until its acceptance tests pass.
3. In parallel, launch Track B (Literature analyst) to produce reading notes and catalogue records for the formulas in section 6, each with a numerical check.
4. Once A is green, launch Track C with the fit/validation upgrade and the Q1 benchmark; launch the Verifier on the three rediscovered 1/pi series as the first independent-reproduction exercise.
5. Report to the owner after R0 and after R2 with: statuses table, negative results, false-positive rates and the proposed next phase.
