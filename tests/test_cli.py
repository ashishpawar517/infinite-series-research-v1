"""Tests for the CLI interface."""

from __future__ import annotations

import subprocess
import sys
from typing import Any

import json

from src.ramanujan_engine.cli import main, format_output
from src.ramanujan_engine.evaluator import evaluate_ramanujan_pi


def test_cli_help():
    """Test that CLI help works."""
    result = subprocess.run(
        [sys.executable, "-m", "ramanujan_engine.cli", "--help"],
        capture_output=True,
        text=True,
        cwd=".",
    )
    assert result.returncode == 0
    assert "Evaluate Ramanujan's infinite series for 1/pi" in result.stdout


def test_cli_basic_pi():
    """Test basic CLI pi computation."""
    result = subprocess.run(
        [sys.executable, "-m", "ramanujan_engine.cli", "pi", "--terms", "1", "--precision", "30"],
        capture_output=True,
        text=True,
        cwd=".",
    )
    assert result.returncode == 0
    assert "Formula:" in result.stdout
    assert "Pi approximation:" in result.stdout
    assert "Terms evaluated: 1" in result.stdout


def test_cli_json_output():
    """Test CLI JSON output."""
    result = subprocess.run(
        [sys.executable, "-m", "ramanujan_engine.cli", "pi", "--terms", "2", "--precision", "30", "--json"],
        capture_output=True,
        text=True,
        cwd=".",
    )
    assert result.returncode == 0

    # Parse JSON output
    data = json.loads(result.stdout)
    assert data["formula_name"] == "Ramanujan's pi formula"
    assert data["terms_evaluated"] == 2
    assert data["working_precision"] == 30
    assert "value" in data


def test_cli_invalid_terms():
    """Test CLI with invalid terms."""
    result = subprocess.run(
        [sys.executable, "-m", "ramanujan_engine.cli", "pi", "--terms", "0"],
        capture_output=True,
        text=True,
        cwd=".",
    )
    assert result.returncode != 0
    assert "Error:" in result.stderr
    assert "terms must be a positive integer" in result.stderr


def test_cli_invalid_precision():
    """Test CLI with invalid precision."""
    result = subprocess.run(
        [sys.executable, "-m", "ramanujan_engine.cli", "pi", "--precision", "0"],
        capture_output=True,
        text=True,
        cwd=".",
    )
    assert result.returncode != 0
    assert "Error:" in result.stderr
    assert "precision must be a positive integer" in result.stderr


def test_format_output():
    """Test the output formatting function."""
    result_obj = evaluate_ramanujan_pi(terms=1, precision=25, compute_trace=True)
    result_dict = result_obj.to_dict()

    formatted = format_output(result_dict, show_trace=False)
    assert "Formula:" in formatted
    assert "Pi approximation:" in formatted
    assert "Terms evaluated: 1" in formatted

    formatted_with_trace = format_output(result_dict, show_trace=True)
    assert "Convergence trace" in formatted_with_trace


if __name__ == "__main__":
    test_cli_help()
    test_cli_basic_pi()
    test_cli_json_output()
    test_cli_invalid_terms()
    test_cli_invalid_precision()
    test_format_output()
    print("CLI tests passed!")