from pathlib import Path

import numpy as np
import pytest

rasterio = pytest.importorskip("rasterio")

from pyfireca.gis import RasterMetadata, read_raster, write_raster


def _metadata() -> RasterMetadata:
    return RasterMetadata(
        shape=(3, 4),
        crs="EPSG:32650",
        transform=(30.0, 0.0, 500000.0, 0.0, -30.0, 3600000.0),
        nodata=-9999,
    )


def test_write_then_read_raster_preserves_array_and_metadata(tmp_path: Path) -> None:
    path = tmp_path / "fuel.tif"
    values = np.arange(12, dtype=np.int16).reshape(3, 4)
    metadata = _metadata()

    write_raster(path, values, metadata)
    loaded, loaded_metadata = read_raster(path)

    assert np.array_equal(loaded, values)
    assert loaded.dtype == values.dtype
    assert loaded_metadata.shape == metadata.shape
    assert loaded_metadata.crs == metadata.crs
    assert loaded_metadata.transform == pytest.approx(metadata.transform)
    assert loaded_metadata.nodata == metadata.nodata


def test_written_geotiff_reopens_with_expected_geometry(tmp_path: Path) -> None:
    path = tmp_path / "state.tif"
    values = np.ones((3, 4), dtype=np.uint8)
    metadata = RasterMetadata(
        shape=(3, 4),
        crs="EPSG:32650",
        transform=(30.0, 0.0, 500000.0, 0.0, -30.0, 3600000.0),
        nodata=255,
    )

    write_raster(path, values, metadata)

    with rasterio.open(path) as dataset:
        assert dataset.driver == "GTiff"
        assert dataset.count == 1
        assert dataset.width == 4
        assert dataset.height == 3
        assert dataset.crs.to_string() == "EPSG:32650"
        assert dataset.nodata == 255
        assert dataset.transform.a == pytest.approx(30.0)
        assert dataset.transform.e == pytest.approx(-30.0)


def test_read_raster_rejects_missing_crs(tmp_path: Path) -> None:
    path = tmp_path / "no_crs.tif"
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=2,
        width=2,
        count=1,
        dtype="float32",
        transform=rasterio.Affine(1.0, 0.0, 0.0, 0.0, -1.0, 2.0),
    ) as dataset:
        dataset.write(np.ones((2, 2), dtype=np.float32), 1)

    with pytest.raises(ValueError, match="CRS"):
        read_raster(path)


def test_read_raster_rejects_invalid_band(tmp_path: Path) -> None:
    path = tmp_path / "one_band.tif"
    write_raster(path, np.ones((3, 4), dtype=np.int16), _metadata())

    with pytest.raises(ValueError, match="positive integer"):
        read_raster(path, band=0)
    with pytest.raises(IndexError, match="band 2"):
        read_raster(path, band=2)


def test_write_raster_requires_matching_two_dimensional_array(tmp_path: Path) -> None:
    metadata = _metadata()

    with pytest.raises(ValueError, match="two-dimensional"):
        write_raster(tmp_path / "three_dimensional.tif", np.ones((1, 3, 4)), metadata)

    with pytest.raises(ValueError, match="does not match"):
        write_raster(tmp_path / "wrong_shape.tif", np.ones((2, 4)), metadata)
