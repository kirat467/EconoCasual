"""Small sanity tests for the budget optimizer (solve_allocation).

Run from the repository root:
    python backend/test_optimizer.py        (plain run)
    pytest backend/test_optimizer.py        (if pytest is installed)

Each test uses a tiny problem whose best answer can be worked out by hand.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from optimizer import solve_allocation  # noqa: E402

DISCOUNTS = [10, 20]


def test_never_exceeds_budget():
    rng = np.random.default_rng(0)
    values = rng.uniform(0.0, 0.1, size=(200, 2))
    for budget in (100, 500, 1500):
        choice = solve_allocation(values, DISCOUNTS, budget)
        assert choice.sum() <= budget + 1e-9


def test_skips_customers_with_negative_effect():
    # customer 0 would be hurt by any coupon, so they must get nothing
    values = np.array([[-0.05, -0.08],
                       [0.04, 0.06],
                       [0.03, 0.05]])
    choice = solve_allocation(values, DISCOUNTS, budget=1000)
    assert choice[0] == 0


def test_picks_best_use_of_a_tight_budget():
    # Budget 20: either one $20 coupon for customer 0 (value 0.09)
    # or two $10 coupons for customers 1 and 2 (value 0.05 + 0.05 = 0.10).
    values = np.array([[0.04, 0.09],
                       [0.05, 0.06],
                       [0.05, 0.06]])
    choice = solve_allocation(values, DISCOUNTS, budget=20)
    assert list(choice) == [0, 10, 10]


def test_one_coupon_per_customer_and_valid_values():
    rng = np.random.default_rng(1)
    values = rng.uniform(-0.02, 0.08, size=(50, 2))
    choice = solve_allocation(values, DISCOUNTS, budget=400)
    assert set(np.unique(choice)).issubset({0, 10, 20})
    assert choice.shape == (50,)


def test_zero_budget_gives_nothing():
    values = np.full((5, 2), 0.05)
    choice = solve_allocation(values, DISCOUNTS, budget=0)
    assert choice.sum() == 0


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"PASS  {t.__name__}")
    print(f"\n{len(tests)} tests passed")
