"""Independent first-order uncertainty-budget checks by Jason Stys.

Functions: test_*; variables: inverse sensitivities, covariance terms and withheld gates.
Evaluation references never enter the fit or budget. Definition lines: docs/CODE_INDEX.md.
"""

import math
from copy import deepcopy

from sensorlab.engine import analyze, build_run
from sensorlab.model import CASES, Settings, configuration


def test_variance_budget_matches_independent_inverse_gradient():
    """Use explicit derivatives dy=1/b, da=-1/b, db=-x/b including signed covariance."""
    run = build_run(Settings())
    fit = run["fit"]
    for row, supplied in zip(run["rows"], run["input"]["samples"], strict=True):
        x, b = row["estimate"], fit["b"]
        response = (supplied["u_uv"] / 1000) ** 2 / b**2
        parameters = (fit["var_a"] + x * x * fit["var_b"] + 2 * x * fit["cov_ab"]) / b**2
        assert math.isclose(row["response_variance"], response, rel_tol=1e-8, abs_tol=1e-9)
        assert math.isclose(row["fit_parameter_variance"], parameters, rel_tol=1e-8, abs_tol=1e-9)
        assert math.isclose(row["u"] ** 2, response + parameters, rel_tol=1e-8, abs_tol=1e-9)
        assert math.isclose(
            row["response_variance_fraction"] + row["fit_variance_fraction"], 1, abs_tol=1e-9
        )
        assert row["fit_covariance_cross_term"] <= 0


def test_withheld_budget_and_reference_isolation():
    """No estimate means no budget; changing supplied monitoring truth cannot change uncertainty."""
    for scenario in CASES:
        run = build_run(Settings(scenario=scenario))
        assert all(
            (row["response_variance"] is None) == (row["estimate"] is None) for row in run["rows"]
        )
    data = configuration(Settings())
    other = deepcopy(data)
    other["samples"][0]["reference_milli"] = None
    before, after = analyze(data)["rows"][0], analyze(other)["rows"][0]
    for key in (
        "u",
        "response_variance",
        "fit_parameter_variance",
        "response_variance_fraction",
        "dominant_uncertainty",
    ):
        assert before[key] == after[key]
