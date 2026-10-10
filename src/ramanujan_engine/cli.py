"""Command-line interface for the Ramanujan Infinite Series Engine."""

from __future__ import annotations

import argparse
import sys
from typing import Any

from .evaluator import evaluate_ramanujan_pi
from .formulas.ramanujan_pi import evaluate_ramanujan_pi_direct


def format_output(result: dict[str, Any], show_trace: bool = False) -> str:
    """
    Format the result for human-readable output.

    Args:
        result: Dictionary representation of SeriesResult
        show_trace: Whether to include trace information

    Returns:
        Formatted string for display
    """
    lines = [
        f"Formula: {result['formula_name']}",
        f"Pi approximation: {result['value']}",
        f"Terms evaluated: {result['terms_evaluated']}",
        f"Working precision: {result['working_precision']} decimal digits",
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
        description="Evaluate Ramanujan's infinite series for 1/pi"
    )
    parser.add_argument(
        "formula",
        choices=["pi"],
        help="Formula to evaluate (currently only 'pi' is supported)",
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
        if args.formula == "pi":
            result_obj = evaluate_ramanujan_pi(
                terms=args.terms,
                precision=args.precision,
                compute_trace=args.trace,
            )
            result_dict = result_obj.to_dict()

            if args.json:
                import json
                print(json.dumps(result_dict, indent=2))
            else:
                print(format_output(result_dict, show_trace=args.trace))

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()