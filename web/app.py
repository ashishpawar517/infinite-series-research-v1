"""
Reverse Series Engine Web Application
A Flask web app that provides a UI for discovering infinite series representations
of mathematical expressions, integrated with the Ramanujan engine backend.
"""

from flask import Flask, render_template, request, jsonify
import json
import math
import re
from typing import List, Dict, Any, Optional, Tuple

# Import our Ramanujan engine
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ramanujan_engine.evaluator import evaluate_ramanujan_pi

app = Flask(__name__, template_folder='templates', static_folder='static')

def parse_expression(src: str) -> float:
    """
    Parse a mathematical expression into a float value.
    Based on the parser from the original HTML file.
    """
    # Remove whitespace and normalize
    s = src.replace(/\s+/g, '').replace(/√/g, 'sqrt').replace(/root/g, 'sqrt').replace(/π/g, 'pi')
    i = 0

    # Mathematical functions
    F = {
        'sqrt': math.sqrt,
        'ln': math.log,
        'log': math.log,
        'exp': math.exp,
        'sin': math.sin,
        'cos': math.cos,
        'abs': abs
    }

    def err(m: str):
        raise ValueError(m)

    def expr() -> float:
        """Parse addition and subtraction"""
        v = term()
        while i < len(s) and s[i] in '+-':
            op = s[i]
            i += 1
            r = term()
            v = v + r if op == '+' else v - r
        return v

    def term() -> float:
        """Parse multiplication and division"""
        v = unary()
        while i < len(s) and s[i] in '*/':
            op = s[i]
            i += 1
            r = unary()
            v = v * r if op == '*' else v / r
        return v

    def unary() -> float:
        """Parse unary plus/minus"""
        if i < len(s) and s[i] == '-':
            i += 1
            return -unary()
        if i < len(s) and s[i] == '+':
            i += 1
            return unary()
        return power()

    def power() -> float:
        """Parse exponentiation"""
        v = atom()
        if i < len(s) and s[i] == '^':
            i += 1
            return math.pow(v, unary())
        return v

    def atom() -> float:
        """Parse numbers, parentheses, and functions"""
        if i < len(s) and s[i] == '(':
            i += 1
            v = expr()
            if i >= len(s) or s[i] != ')':
                err('Missing )')
            i += 1
            return v

        # Parse number
        num_match = re.match(r'^(\d+\.?\d*|\.\d+)', s[i:])
        if num_match:
            num_str = num_match.group(0)
            i += len(num_str)
            return float(num_str)

        # Parse function/function constants
        func_match = re.match(r'^[a-z]+', s[i:])
        if func_match:
            func_name = func_match.group(0)
            i += len(func_name)

            if func_name == 'pi':
                return math.pi
            if func_name == 'e':
                return math.e
            if func_name in F:
                if i >= len(s) or s[i] != '(':
                    err(f'Use {func_name}(...)')
                i += 1
                v = expr()
                if i >= len(s) or s[i] != ')':
                    err('Missing )')
                i += 1
                return F[func_name](v)
            err(f'Unknown name: {func_name}')

        err(f'Unexpected {s[i:] if i < len(s) else "end of input"}')

    result = expr()
    if i < len(s):
        err(f'Unexpected {s[i:]}')
    if not math.isfinite(result):
        err('Value is not finite')
    return result


def gcd(a: int, b: int) -> int:
    """Calculate greatest common divisor"""
    while b:
        a, b = b, a % b
    return abs(a)


def convergents(value: float, max_denominator: int) -> List[Tuple[int, int]]:
    """Generate continued fraction convergents"""
    convergents_list = []
    h1, h0 = 1, 0  # numerators
    k1, k0 = 0, 1  # denominators
    x = value

    for _ in range(30):  # limit iterations
        if k0 == 0:
            break
        a = math.floor(x) if x != 0 else 0
        h = a * h1 + h0
        k = a * k1 + k0

        if k > max_denominator:
            break

        convergents_list.append((h, k))
        h0, h1 = h1, h
        k0, k1 = k1, k

        f = x - a
        if f < 1e-12:
            break
        x = 1 / f if f != 0 else float('inf')

    return convergents_list


def sqrt_series(x: float, N: int = 40) -> Optional[Dict[str, Any]]:
    """Generate sqrt series representation"""
    try:
        # Check if x is a nice square root
        conv_list = convergents(x, 1000)
        if any(abs(p/q - x) < 1e-12 * x for p, q in conv_list):
            return None

        # Look for x^2 as a rational
        conv_x2 = convergents(x * x, 3000)
        rational_x2 = next(([p, q] for p, q in conv_x2 if abs(p/q - x*x) < 1e-10 * max(1, x*x)), None)
        if not rational_x2:
            return None

        P, Q = rational_x2
        # U(a,b) = (P*b^2 - Q*a^2) / (Q*a^2)
        def U(a, b):
            return (P * b * b - Q * a * a) / (Q * a * a)

        # Get candidates for sqrt series
        cs = convergents(x, 500)
        cs = [c for c in cs if c[0] > 0]  # positive terms only
        if not cs:
            return None

        # Find best candidate
        best_candidate = min(cs, key=lambda c: abs(U(c[0], c[1])))
        a, b = best_candidate
        u_val = U(a, b)

        # Calculate series terms
        num = P * b * b - Q * a * a
        den = Q * a * a
        g = gcd(num, den)
        num //= g
        den //= g

        terms = []
        co = 1
        pu = 1
        for k in range(N):
            if k > 0:
                co *= (0.5 - (k - 1)) / k
                pu *= u_val
            terms.append(a / b * co * pu)

        # Format the LaTeX
        sqrt_arg = f"{P}" if Q == 1 else f"\\frac{{{P}}}{{{Q}}}"
        frac_part = f"{a}" if b == 1 else f"\\frac{{{a}}}{{{b}}}"

        tex = f"\\sqrt{{{sqrt_arg}}} = {frac_part} \\sum_{{n=0}}^{{\\infty}} \\binom{{1/2}}{{n}} \\left( {{ \\frac{{{num}}}{{{den}}} }} \\right)^{{n}}"

        return {
            'name': 'Binomial series (exact structure)',
            'tex': tex,
            'note': f'From √(1+u) = Σ C(1/2,n)uⁿ, valid for |u|&lt;1. Here u = {num}/{den}+.',
            'color': '--a',
            'det': f'Detected x² = {P}/{Q}, so x = √({P}/{Q})',
            'formula': f'x = ({a}/{b}) · Σ C(1/2,k) · ({num}/{den})^k\nfrom √(1+u) = Σ C(1/2,k) u^k, valid for |u|<1',
            'terms': terms
        }
    except Exception:
        return None


def exp_series(x: float, N: int = 40) -> Optional[Dict[str, Any]]:
    """Generate exponential series representation"""
    try:
        L = math.log(x)
        terms = []
        p = 1
        for k in range(N):
            if k > 0:
                p *= L / k
            terms.append(p)

        tex = f"x = \\sum_{{n=0}}^{{\\infty}} \\frac{{(\\ln x)^{n}}}{{n!}},\\quad \\ln x = {L:.10f}"

        return {
            'name': 'Exponential series (universal)',
            'tex': tex,
            'note': 'From eˣ = Σ xⁿ/n!, converges for every real input. It feeds ln x in, so it is universal but not deep.',
            'color': '--b',
            'formula': f'x = Σ (ln x)^k / k!\nln x = {L:.12f}\nfrom eˣ = Σ xᵏ/k!, converges for every real input',
            'terms': terms
        }
    except Exception:
        return None


def engel_series(x: float, N: int = 25) -> Optional[Dict[str, Any]]:
    """Generate Engel series representation"""
    try:
        n_part = math.floor(x)
        t = [n_part] if n_part > 0 else []
        a = []
        u = x - n_part
        prod = 1

        while u > 1e-13 and len(a) < 25 and prod < 1e15:
            ai = math.ceil(1 / u)
            a.append(ai)
            prod *= ai
            t.append(1 / prod)
            u = u * ai - 1

        a_str = ', '.join(map(str, a))
        n_prefix = f"{n_part}+" if n_part > 0 else ""

        tex = f"x = {n_part if n_part > 0 else ''}\\sum_{{k=1}}^{{\\infty}} \\frac{{1}}{{a_1a_2\\cdots a_k}}"

        return {
            'name': 'Engel series (greedy, any positive real)',
            'tex': tex,
            'note': f'Engel expansion, a = [{a_str}]',
            'color': '--c',
            'formula': f'x = {n_part} + Σ 1/(a₁a₂⋯aₖ)\na = [{a_str}]\nEngel (1913): aₖ₊₁ ≥ aₖ, terms shrink at least geometrically',
            'terms': t
        }
    except Exception:
        return None


def pi_series(x: float, N: int = 40) -> List[Dict[str, Any]]:
    """Generate pi-based series representations"""
    results = []

    def ok(value: float) -> Optional[Tuple[int, int]]:
        """Find a good rational approximation"""
        conv_list = convergents(value, 200)
        for p, q in conv_list:
            if p > 0 and abs(p/q - value) < 1e-11 * value:
                return (p, q)
        return None

    try:
        # Try x * π
        r = ok(x * math.pi)
        if r:
            p, q = r
            c = p / q
            lhs = f"\\frac{{{p}}}{{{q if q != 1 else ''}}\\pi}"
            pre = '' if c == 1 else f"\\frac{{{p}}}{{{q}}} \\cdot "

            # Ramanujan series
            rm_terms = []
            ch_terms = []
            T = 1
            M = 1

            for n in range(N):
                if n > 0:
                    T *= 4*n*(4*n-1)*(4*n-2)*(4*n-3) / (n**4 * 396**4)
                    M *= 6*n*(6*n-1)*(6*n-2)*(6*n-3)*(6*n-4)*(6*n-5) / (3*n*(3*n-1)*(3*n-2)*n**3 * 640320**3)
                rm_terms.append(c * 2 * math.SQRT2 / 9801 * T * (1103 + 26390*n))
                ch_terms.append(c * 12 / (640320**1.5) * ((-1)**n) * M * (13591409 + 545140134*n))

            results.append({
                'name': 'Ramanujan 1914 (~8 digits/term)',
                'tex': f"{lhs} = {pre}\\frac{{2\\sqrt{{2}}}}{{9801}}\\sum_{{n=0}}^{{\\infty}} \\frac{{(4n)! \\, (1103+26390n)}}{{(n!)^{4}\\, 396^{4n}}}",
                'note': 'Ramanujan 1914. Each term adds about 8 correct digits.',
                'color': '--d',
                'det': '',
                'formula': '',
                'terms': rm_terms
            })

            results.append({
                'name': 'Chudnovsky (~14 digits/term)',
                'tex': f"{lhs} = {pre}\\frac{{12}}{{640320^{{3/2}}}}\\sum_{{n=0}}^{{\\infty}} \\frac{{(-1)^{n}(6n)! \\, (13591409+545140134n)}}{{(3n)! \\, (n!)^{3}\\, 640320^{3n}}}",
                'note': 'Chudnovsky 1987. Each term adds about 14 correct digits.',
                'color': '--e',
                'det': '',
                'formula': '',
                'terms': ch_terms
            })

        # Try x / π
        r = ok(x / math.pi)
        if r:
            p, q = r
            c = p / q
            k = '' if c == 1 else f"\\frac{{{p}}}{{{q}}}"

            # Machin-like series
            machin_terms = []
            for n in range(N):
                term_val = c * ((-1)**n) / (2*n+1) * (16/(5**(2*n+1)) - 4/(239**(2*n+1)))
                machin_terms.append(term_val)

            results.append({
                'name': 'Machin formula (~1.4 digits/term)',
                'tex': f"{k}\\pi = {k}\\sum_{{n=0}}^{{\\infty}} \\frac{{(-1)^{n}}}{{2n+1}} \\left( \\frac{{16}}{{5^{{2n+1}}}} - \\frac{{4}}{{239^{{2n+1}}}} \\right)",
                'note': 'Machin 1706: π = 16 arctan(1/5) − 4 arctan(1/239), expanded as one series.',
                'color': '--d',
                'det': '',
                'formula': '',
                'terms': machin_terms
            })
    except Exception:
        pass

    return results


@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')


@app.route('/compute', methods=['POST'])
def compute():
    """Handle computation requests"""
    try:
        data = request.get_json()
        expression = data.get('expression', '').strip()

        if not expression:
            return jsonify({'error': 'Please enter an expression'}), 400

        # Parse the expression
        x = parse_expression(expression)

        if x <= 0:
            return jsonify({'error': 'Needs a positive value'}), 400

        # Generate series representations
        series_results = []

        # Try different series types
        sqrt_result = sqrt_series(x)
        if sqrt_result:
            series_results.append(sqrt_result)

        exp_result = exp_series(x)
        if exp_result:
            series_results.append(exp_result)

        engel_result = engel_series(x)
        if engel_result:
            series_results.append(engel_result)

        pi_results = pi_series(x)
        series_results.extend(pi_results)

        # Also compute using our Ramanujan engine for reference
        ramanujan_result = evaluate_ramanujan_pi(terms=5, precision=50)

        return jsonify({
            'value': x,
            'value_precision': f"{x:.15f}",
            'series': series_results,
            'ramanujan_reference': {
                'value': float(ramanujan_result.value),
                'terms': ramanujan_result.terms_evaluated,
                'precision': ramanujan_result.working_precision
            }
        })

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)