
import pytest

from app.engines.screening import StockScreen
from app.engines.simulations import SimulationEngine


def test_price_filter():
    screen = StockScreen()
    assert screen.filter_by_price([100, 110], 100, 120)
    assert not screen.filter_by_price([100, 130], 100, 120)


def test_missing_momentum_not_zero():
    screen = StockScreen()
    result = screen.score_stock([100, 110, 105])

    assert result["momentum_6m"] is None
    assert result["beta"] is None
    assert result["score"] is None


def test_momentum_filter():
    screen = StockScreen()

    prices = [100.0] * 126 + [120.0]

    assert screen.filter_by_momentum(
        prices, min_momentum=0.10
    )


def test_monte_carlo_is_reproducible():
    engine = SimulationEngine()

    kwargs = {
        "historical_prices": [100, 102, 101, 104],
        "simulation_days": 5,
        "number_of_paths": 3,
        "random_seed": 42,
    }

    first = engine.monte_carlo(**kwargs)
    second = engine.monte_carlo(**kwargs)

    assert first == second
    assert len(first) == 3
    assert all(len(path) == 6 for path in first)


def test_bootstrap_constant_returns():
    engine = SimulationEngine()

    paths = engine.bootstrap(
        historical_returns=[0.10],
        initial_value=100.0,
        horizon=2,
        simulations=2,
    )

    assert paths[0] == pytest.approx([100, 110, 121])


def test_bootstrap_rejects_empty_history():
    engine = SimulationEngine()

    with pytest.raises(ValueError):
        engine.bootstrap([])


def test_summary_uses_true_median():
    engine = SimulationEngine()

    summary = engine.monte_carlo_summary([
        [100, 110],
        [100, 130],
    ])

    assert summary["final"]["median"] == pytest.approx(120)
    assert summary["final"]["mean"] == pytest.approx(120)
