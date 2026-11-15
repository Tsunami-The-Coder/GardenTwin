
import math
import pytest

from simulation.crops.single_sine import calculate_single_sine_gdd


def test_constant_temperature():
    result = calculate_single_sine_gdd(20, 20, 10, 30)
    assert result == pytest.approx(10.0)


def test_temperature_entirely_below_base():
    result = calculate_single_sine_gdd(0, 5, 10, 30)
    assert result == pytest.approx(0.0)


def test_temperature_entirely_above_upper():
    result = calculate_single_sine_gdd(35, 40, 10, 30)
    assert result == pytest.approx(20.0)


def test_lower_threshold_crossing():
    result = calculate_single_sine_gdd(0, 20, 10, 30)
    assert result == pytest.approx(10 / math.pi)


def test_upper_threshold_cutoff():
    result = calculate_single_sine_gdd(20, 40, 10, 30)
    assert result == pytest.approx(20 - 10 / math.pi)


def test_invalid_temperature_order():
    with pytest.raises(ValueError):
        calculate_single_sine_gdd(25, 15, 10, 30)


def test_invalid_threshold_order():
    with pytest.raises(ValueError):
        calculate_single_sine_gdd(10, 20, 30, 20)


def test_non_finite_input():
    with pytest.raises(ValueError):
        calculate_single_sine_gdd(float("nan"), 20, 10, 30)
