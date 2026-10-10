"""Command-line interface for the Ramanujan Infinite Series Engine."""

from __future__ import annotations

import argparse
import sys
from typing import Any

from .evaluator import evaluate_formula_by_name, evaluate_ramanujan_pi
from .formulas.catalogue import list_formulas


def format_output(result: dict[str, Any], show_trace: bool = False) -> str:
    """
    Format the result for human-readable output.

    Args:
        result: Dictionary representation of SeriesResult
        show_trace: Whether to include trace information

    Returns:
        Formatted string for display
    """
    is_pi = "pi" in result['formula_name'].lower()
    value_label = "Pi approximation" if is_pi else "Value"
    lines = [
        f"Formula: {result['formula_name']}",
        f"{value_label}: {result['value']}",
        f"Terms evaluated: {result['terms_evaluated']}",
        f"Working precision: {result['working_precision']} decimal digits",
        f"Accelerator: {result.get('accelerator', 'direct')}",
        f"Provenance: {result.get('provenance', 'proven')}",
    ]

    if result.get('analytic_bound') is not None:
        lines.append(
            f"Analytic truncation-error bound: ±{result['analytic_bound']}"
        )

    if show_trace and result.get('trace'):
        lines.append("\nConvergence trace (term index, partial sum):")
        for i, (n, term_val) in enumerate(result['trace']):
            if i < 10:  # Limit display to first 10 terms
                lines.append(f"  n={n}: {term_val}")
            elif i == 10:
                lines.append(f"  ... and {len(result['trace']) - 10} more terms")
                break

    return "\n".join(lines)


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Evaluate Ramanujan's infinite series for 1/pi "
        "(plus general catalogue: use 'list')"
    )
    parser.add_argument(
        "formula",
        nargs="?",
        default="pi",
        help=(
            "Formula to evaluate: 'pi' (Ramanujan, legacy), a catalogue name "
            f"{list_formulas()}, or 'list' to show the catalogue"
        ),
    )
    parser.add_argument(
        "--terms",
        type=int,
        default=1,
        help="Number of terms to evaluate (sum from n=0 to terms-1)",
    )
    parser.add_argument(
        "--precision",
        type=int,
        default=50,
        help="Working precision in decimal digits",
    )
    parser.add_argument(
        "--accelerator",
        default="auto",
        choices=["auto", "direct", "richardson", "wynn-epsilon", "shanks",
                 "levin-u", "cvz", "alternating"],
        help="Convergence accelerator (auto picks from formula metadata)",
    )
    parser.add_argument(
        "--trace",
        action="store_true",
        help="Output convergence trace",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output result as JSON",
    )

    args = parser.parse_args()

    try:
        if args.formula == "list":
            print("Available formulas:")
            for name in list_formulas():
                print(f"  {name}")
            print("Legacy alias: pi -> ramanujan-pi")
            return
        if args.formula == "pi":
            result_obj = evaluate_ramanujan_pi(
                terms=args.terms,
                precision=args.precision,
                compute_trace=args.trace,
            )
        else:
            result_obj = evaluate_formula_by_name(
                args.formula,
                terms=args.terms,
                precision=args.precision,
                accelerator=args.accelerator,
                compute_trace=args.trace,
            )
        result_dict = result_obj.to_dict()

        if args.json:
            import json
            print(json.dumps(result_dict, indent=2))
        else:
            print(format_output(result_dict, show_trace=args.trace))

    except (KeyError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
