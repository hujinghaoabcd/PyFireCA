import pytest

from pyfireca.gis import (
    RasterAlignmentError,
    RasterMetadata,
    validate_named_raster_alignment,
    validate_raster_alignment,
)


def _reference_metadata() -> RasterMetadata:
    return RasterMetadata(
        shape=(100, 200),
        crs="EPSG:32650",
        transform=(30.0, 0.0, 500000.0, 0.0, -30.0, 3600000.0),
        nodata=-9999,
    )


def test_raster_metadata_reports_north_up_resolution() -> None:
    metadata = _reference_metadata()

    assert metadata.resolution == pytest.approx((30.0, 30.0))


def test_raster_metadata_reports_rotated_axis_magnitudes() -> None:
    metadata = RasterMetadata(
        shape=(10, 10),
        crs="EPSG:32650",
        transform=(3.0, 4.0, 0.0, 4.0, -3.0, 0.0),
    )

    assert metadata.resolution == pytest.approx((5.0, 5.0))


def test_raster_metadata_rejects_invalid_shape_crs_and_transform() -> None:
    with pytest.raises(ValueError, match="shape"):
        RasterMetadata((0, 10), "EPSG:32650", (1.0, 0.0, 0.0, 0.0, -1.0, 0.0))

    with pytest.raises(ValueError, match="crs"):
        RasterMetadata((10, 10), "", (1.0, 0.0, 0.0, 0.0, -1.0, 0.0))

    with pytest.raises(ValueError, match="finite"):
        RasterMetadata(
            (10, 10),
            "EPSG:32650",
            (1.0, 0.0, float("nan"), 0.0, -1.0, 0.0),
        )


def test_equal_rasters_are_aligned() -> None:
    reference = _reference_metadata()

    validate_raster_alignment(reference, reference)


def test_alignment_rejects_shape_crs_and_transform_mismatches() -> None:
    reference = _reference_metadata()

    wrong_shape = RasterMetadata(
        shape=(99, 200),
        crs=reference.crs,
        transform=reference.transform,
    )
    with pytest.raises(RasterAlignmentError, match="shape"):
        validate_raster_alignment(reference, wrong_shape)

    wrong_crs = RasterMetadata(
        shape=reference.shape,
        crs="EPSG:4326",
        transform=reference.transform,
    )
    with pytest.raises(RasterAlignmentError, match="crs"):
        validate_raster_alignment(reference, wrong_crs)

    wrong_transform = RasterMetadata(
        shape=reference.shape,
        crs=reference.crs,
        transform=(30.0, 0.0, 500015.0, 0.0, -30.0, 3600000.0),
    )
    with pytest.raises(RasterAlignmentError, match="transform"):
        validate_raster_alignment(reference, wrong_transform)


def test_alignment_uses_explicit_transform_tolerance() -> None:
    reference = _reference_metadata()
    tiny_offset = RasterMetadata(
        shape=reference.shape,
        crs=reference.crs,
        transform=(30.0, 0.0, 500000.0 + 5e-10, 0.0, -30.0, 3600000.0),
    )

    validate_raster_alignment(reference, tiny_offset)

    with pytest.raises(RasterAlignmentError):
        validate_raster_alignment(reference, tiny_offset, absolute_tolerance=1e-11)


def test_nodata_is_optional_alignment_policy() -> None:
    reference = _reference_metadata()
    candidate = RasterMetadata(
        shape=reference.shape,
        crs=reference.crs,
        transform=reference.transform,
        nodata=-32768,
    )

    validate_raster_alignment(reference, candidate)

    with pytest.raises(RasterAlignmentError, match="nodata"):
        validate_raster_alignment(reference, candidate, check_nodata=True)


def test_named_alignment_reports_layer_name() -> None:
    reference = _reference_metadata()
    bad = RasterMetadata(
        shape=(100, 199),
        crs=reference.crs,
        transform=reference.transform,
    )

    with pytest.raises(RasterAlignmentError, match="wind_speed"):
        validate_named_raster_alignment(reference, {"wind_speed": bad})


def test_alignment_rejects_invalid_tolerance() -> None:
    reference = _reference_metadata()

    with pytest.raises(ValueError, match="absolute_tolerance"):
        validate_raster_alignment(reference, reference, absolute_tolerance=-1.0)
