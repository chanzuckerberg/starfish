from typing import Mapping, Optional, Sequence, Type

import numpy as np
import pytest

from starfish import Log
from starfish.image import Filter
from starfish.types import Axes, Coordinates, Number
from ..label_image import AttrKeys, CURRENT_VERSION, DOCTYPE_STRING, LabelImage


@pytest.mark.parametrize(
    "array, physical_coordinates, log, expected_error",
    [
        # 3D label image
        [
            np.zeros((1, 1, 1), dtype=np.int32),
            {
                Coordinates.X: [0],
                Coordinates.Y: [0],
                Coordinates.Z: [0],
            },
            None,
            None,
        ],
        # 2D label image
        [
            np.zeros((1, 1), dtype=np.int32),
            {
                Coordinates.X: [0],
                Coordinates.Y: [0],
            },
            None,
            None,
        ],
        # wrong dtype
        [
            np.zeros((1, 1), dtype=np.float32),
            {
                Coordinates.X: [0],
                Coordinates.Y: [0],
            },
            None,
            TypeError,
        ],
        # missing some coordinates
        [
            np.zeros((1, 1), dtype=np.float32),
            {
                Coordinates.X: [0],
            },
            None,
            KeyError,
        ],
    ]
)
def test_from_array_and_coords(
        array: np.ndarray,
        physical_coordinates: Mapping[Coordinates, Sequence[Number]],
        log: Optional[Log],
        expected_error: Optional[Type[Exception]],
):
    """Test that we can construct a LabelImage and that some common error conditions are caught."""
    if expected_error is not None:
        with pytest.raises(expected_error):
            LabelImage.from_array_and_coords(array, None, physical_coordinates, log)
    else:
        label_image = LabelImage.from_array_and_coords(array, None, physical_coordinates, log)
        assert isinstance(label_image.log, Log)
        assert label_image.xarray.attrs.get(AttrKeys.DOCTYPE, None) == DOCTYPE_STRING
        assert label_image.xarray.attrs.get(AttrKeys.VERSION, None) == str(CURRENT_VERSION)


def test_pixel_coordinates():
    array = np.zeros((2, 2, 2), dtype=np.int32)
    pixel_coordinates = {
        Axes.X: [2, 3],
        Axes.ZPLANE: [0, 1],
    }
    physical_coordinates = {
        Coordinates.X: [0, 0.5],
        Coordinates.Y: [0, 0.2],
        Coordinates.Z: [0, 0.1],
    }
    label_image = LabelImage.from_array_and_coords(
        array, pixel_coordinates, physical_coordinates, None)

    assert np.array_equal(label_image.xarray.coords[Axes.X.value], [2, 3])
    # not provided, should be 0..N-1
    assert np.array_equal(label_image.xarray.coords[Axes.Y.value], [0, 1])
    assert np.array_equal(label_image.xarray.coords[Axes.ZPLANE.value], [0, 1])


def test_save_and_load(tmp_path):
    """Verify that we can save the label image and load it correctly."""
    array = np.zeros((2, 2, 2), dtype=np.int32)
    pixel_coordinates = {
        Axes.X: [2, 3],
        Axes.ZPLANE: [0, 1],
    }
    physical_coordinates = {
        Coordinates.X: [0, 0.5],
        Coordinates.Y: [0, 0.2],
        Coordinates.Z: [0, 0.1],
    }
    log = Log()
    # instantiate a filter (even though that makes no sense in this context)
    filt = Filter.Reduce((Axes.ROUND,), func="max")
    log.update_log(filt)

    label_image = LabelImage.from_array_and_coords(
        array, pixel_coordinates, physical_coordinates, log)
    label_image.to_netcdf(tmp_path / "label_image.netcdf")

    loaded_label_image = LabelImage.open_netcdf(tmp_path / "label_image.netcdf")

    assert label_image.xarray.equals(loaded_label_image.xarray)
    assert label_image.xarray.attrs == loaded_label_image.xarray.attrs
