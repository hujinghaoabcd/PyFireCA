import numpy as np
import pytest

from pyfireca.data import EnvironmentalData, SpatialLayer


def test_static_spatial_layer_returns_same_raster_for_any_time_index() -> None:
    values = np.arange(6, dtype=float).reshape(2, 3)
    layer = SpatialLayer(values, units="m")

    assert not layer.is_dynamic
    assert layer.spatial_shape == (2, 3)
    assert layer.time_size is None
    assert np.shares_memory(layer.at(), values)
    assert np.shares_memory(layer.at(5), values)


def test_dynamic_spatial_layer_requires_valid_time_index() -> None:
    values = np.arange(24, dtype=float).reshape(4, 2, 3)
    layer = SpatialLayer(values, units="m/s")

    assert layer.is_dynamic
    assert layer.spatial_shape == (2, 3)
    assert layer.time_size == 4
    assert np.array_equal(layer.at(2), values[2])

    with pytest.raises(ValueError):
        layer.at()
    with pytest.raises(IndexError):
        layer.at(4)
    with pytest.raises(TypeError):
        layer.at(1.5)  # type: ignore[arg-type]


def test_spatial_layer_rejects_non_spatial_or_object_arrays() -> None:
    with pytest.raises(ValueError):
        SpatialLayer(np.array([1.0, 2.0]))

    with pytest.raises(TypeError):
        SpatialLayer(np.array([["fuel"]], dtype=object))


def test_environmental_data_validates_alignment_and_time_size() -> None:
    fuel = SpatialLayer(np.ones((2, 3), dtype=np.uint8), units="fuel-code")
    wind = SpatialLayer(np.ones((4, 2, 3), dtype=float), units="m/s")
    moisture = SpatialLayer(np.ones((4, 2, 3), dtype=float), units="fraction")

    data = EnvironmentalData(
        {"fuel": fuel, "wind_speed": wind, "fuel_moisture": moisture}
    )

    assert data.spatial_shape == (2, 3)
    assert data.time_size == 4

    snapshot = data.snapshot(1)
    assert snapshot["fuel"].shape == (2, 3)
    assert np.array_equal(snapshot["wind_speed"], wind.values[1])


def test_environmental_data_rejects_misaligned_spatial_shapes() -> None:
    with pytest.raises(ValueError, match="spatial shape"):
        EnvironmentalData(
            {
                "fuel": SpatialLayer(np.ones((2, 3))),
                "slope": SpatialLayer(np.ones((3, 3))),
            }
        )


def test_environmental_data_rejects_inconsistent_dynamic_lengths() -> None:
    with pytest.raises(ValueError, match="time size"):
        EnvironmentalData(
            {
                "wind_speed": SpatialLayer(np.ones((4, 2, 3))),
                "moisture": SpatialLayer(np.ones((5, 2, 3))),
            }
        )


def test_environmental_data_reports_missing_layer() -> None:
    data = EnvironmentalData({"fuel": SpatialLayer(np.ones((2, 2)))})

    with pytest.raises(KeyError, match="fuel"):
        data.layer("wind_speed")
