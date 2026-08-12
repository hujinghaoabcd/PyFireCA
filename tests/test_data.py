import numpy as np
import pytest

from pyfireca.data import (
    EnvironmentalData,
    LandscapeInput,
    MissingEnvironmentalDataError,
    SpatialLayer,
    build_domain_mask,
    nodata_mask,
)
from pyfireca.gis import RasterMetadata
from pyfireca.state import FireState


def _metadata(shape: tuple[int, int] = (2, 3)) -> RasterMetadata:
    return RasterMetadata(
        shape=shape,
        crs="EPSG:32650",
        transform=(30.0, 0.0, 500000.0, 0.0, -30.0, 3600000.0),
        nodata=-9999,
    )


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


def test_spatial_layer_validates_nodata_metadata() -> None:
    SpatialLayer(np.ones((2, 2)), nodata=np.nan)

    with pytest.raises(TypeError, match="nodata"):
        SpatialLayer(np.ones((2, 2)), nodata=True)
    with pytest.raises(ValueError, match="infinite"):
        SpatialLayer(np.ones((2, 2)), nodata=np.inf)


def test_environmental_data_validates_alignment_and_time_size() -> None:
    fuel = SpatialLayer(np.ones((2, 3), dtype=np.uint8), units="fuel-code")
    wind = SpatialLayer(np.ones((4, 2, 3), dtype=float), units="m/s")
    moisture = SpatialLayer(np.ones((4, 2, 3), dtype=float), units="fraction")

    data = EnvironmentalData({"fuel": fuel, "wind_speed": wind, "fuel_moisture": moisture})

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


def test_required_snapshot_returns_only_selected_complete_layers() -> None:
    fuel = SpatialLayer(np.ones((2, 3), dtype=np.int16), nodata=0)
    wind = SpatialLayer(np.arange(24, dtype=float).reshape(4, 2, 3), units="m/s")
    optional = SpatialLayer(np.full((4, 2, 3), np.nan), units="fraction")
    data = EnvironmentalData({"fuel": fuel, "wind": wind, "optional": optional})

    snapshot = data.require_complete_snapshot(["fuel", "wind"], time_index=2)

    assert set(snapshot) == {"fuel", "wind"}
    assert np.array_equal(snapshot["wind"], wind.values[2])


def test_required_snapshot_rejects_declared_dynamic_nodata() -> None:
    wind_values = np.ones((3, 2, 3), dtype=float)
    wind_values[1, 0, 2] = -9999.0
    data = EnvironmentalData(
        {"wind": SpatialLayer(wind_values, units="m/s", nodata=-9999.0)}
    )

    with pytest.raises(MissingEnvironmentalDataError, match="1 declared NoData"):
        data.require_complete_snapshot(["wind"], time_index=1)


def test_required_snapshot_rejects_unmarked_nonfinite_values_without_reclassifying_domain() -> None:
    wind_values = np.ones((2, 2, 3), dtype=float)
    wind_values[0, 1, 1] = np.nan
    data = EnvironmentalData({"wind": SpatialLayer(wind_values, units="m/s", nodata=None)})

    assert not nodata_mask(data.layer("wind"), time_index=0).any()
    with pytest.raises(MissingEnvironmentalDataError, match="additional non-finite"):
        data.require_complete_snapshot(["wind"], time_index=0)


def test_required_snapshot_does_not_interpolate_or_skip_missing_time() -> None:
    wind_values = np.ones((3, 2, 3), dtype=float)
    wind_values[1, 0, 0] = np.nan
    data = EnvironmentalData({"wind": SpatialLayer(wind_values, units="m/s")})

    with pytest.raises(MissingEnvironmentalDataError, match="time_index=1"):
        data.require_complete_snapshot(["wind"], time_index=1)

    valid = data.require_complete_snapshot(["wind"], time_index=2)
    assert np.array_equal(valid["wind"], wind_values[2])


def test_required_snapshot_validates_requested_names() -> None:
    data = EnvironmentalData({"fuel": SpatialLayer(np.ones((2, 2)))})

    with pytest.raises(ValueError, match="at least one"):
        data.require_complete_snapshot([])
    with pytest.raises(ValueError, match="unique"):
        data.require_complete_snapshot(["fuel", "fuel"])


def test_nodata_mask_uses_only_explicit_marker() -> None:
    sentinel = SpatialLayer(
        np.array([[1.0, -9999.0], [np.nan, 2.0]]),
        nodata=-9999.0,
    )
    assert np.array_equal(
        nodata_mask(sentinel),
        np.array([[False, True], [False, False]], dtype=bool),
    )

    nan_marker = SpatialLayer(np.array([[1.0, np.nan], [2.0, np.nan]]), nodata=np.nan)
    assert np.array_equal(
        nodata_mask(nan_marker),
        np.array([[False, True], [False, True]], dtype=bool),
    )

    undeclared_nan = SpatialLayer(np.array([[1.0, np.nan]]), nodata=None)
    assert not nodata_mask(undeclared_nan).any()


def test_domain_mask_combines_only_selected_static_nodata_layers() -> None:
    fuel = SpatialLayer(
        np.array([[1, 1, 0], [1, 1, 1]], dtype=np.int16),
        nodata=0,
    )
    slope = SpatialLayer(
        np.array([[5.0, -9999.0, 10.0], [0.0, 2.0, 3.0]]),
        nodata=-9999.0,
    )
    wind = SpatialLayer(np.ones((4, 2, 3), dtype=float), units="m/s")
    environment = EnvironmentalData({"fuel": fuel, "slope": slope, "wind": wind})

    domain = build_domain_mask(environment, ["fuel", "slope"])

    expected = np.array([[True, False, False], [True, True, True]], dtype=bool)
    assert np.array_equal(domain, expected)


def test_dynamic_layer_cannot_define_persistent_domain() -> None:
    environment = EnvironmentalData(
        {"wind": SpatialLayer(np.ones((4, 2, 3), dtype=float), nodata=-9999.0)}
    )

    with pytest.raises(ValueError, match="dynamic layer"):
        build_domain_mask(environment, ["wind"])


def test_landscape_input_assembles_domain_state_and_independent_grid() -> None:
    fuel = SpatialLayer(
        np.array([[1, 1, 0], [1, 1, 1]], dtype=np.int16),
        nodata=0,
    )
    slope = SpatialLayer(np.ones((2, 3), dtype=float), units="degrees")
    environment = EnvironmentalData({"fuel": fuel, "slope": slope})
    ignition = np.array([[False, True, False], [False, False, False]], dtype=bool)

    landscape = LandscapeInput.from_domain_layers(
        environment,
        _metadata(),
        domain_layer_names=["fuel"],
        ignition_mask=ignition,
    )

    expected = np.array(
        [
            [FireState.UNBURNED, FireState.BURNING, FireState.UNBURNABLE],
            [FireState.UNBURNED, FireState.UNBURNED, FireState.UNBURNED],
        ],
        dtype=np.uint8,
    )
    assert np.array_equal(landscape.initial_state, expected)

    grid = landscape.make_grid()
    grid.state[0, 0] = FireState.BURNED
    assert landscape.initial_state[0, 0] == FireState.UNBURNED
    assert grid.cell_size is None


def test_landscape_input_requires_one_shared_spatial_shape() -> None:
    environment = EnvironmentalData({"fuel": SpatialLayer(np.ones((2, 3)))})

    with pytest.raises(ValueError, match="metadata shape"):
        LandscapeInput.from_domain_layers(
            environment,
            _metadata((3, 3)),
            domain_layer_names=["fuel"],
        )

    with pytest.raises(ValueError, match="initial_state shape"):
        LandscapeInput(
            environment=environment,
            metadata=_metadata(),
            initial_state=np.ones((2, 2), dtype=np.uint8),
        )
