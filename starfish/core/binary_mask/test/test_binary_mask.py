import os

import numpy as np
import pytest
import xarray as xr

from starfish.core.types import Axes, Coordinates
from ..binary_mask import _validate_binary_mask, BinaryMaskCollection


def test_validate_binary_mask():
    good = xr.DataArray([[True, False, False],
                         [False, True, True]],
                        dims=('y', 'x'),
                        coords=dict(x=[0, 1, 2],
                                    y=[0, 1],
                                    xc=('x', [0.5, 1.5, 2.5]),
                                    yc=('y', [0.5, 1.5])))
    _validate_binary_mask(good)

    good = xr.DataArray([[[True], [False], [False]],
                         [[False], [True], [True]]],
                        dims=('z', 'y', 'x'),
                        coords=dict(z=[0, 1],
                                    y=[1, 2, 3],
                                    x=[42],
                                    zc=('z', [0.5, 1.5]),
                                    yc=('y', [1.5, 2.5, 3.5]),
                                    xc=('x', [42.5])))
    _validate_binary_mask(good)

    bad = xr.DataArray([[1, 2, 3],
                        [4, 5, 6]],
                       dims=('y', 'x'),
                       coords=dict(x=[0, 1, 2],
                                   y=[0, 1],
                                   xc=('x', [0.5, 1.5, 2.5]),
                                   yc=('y', [0.5, 1.5])))
    with pytest.raises(TypeError):
        _validate_binary_mask(bad)

    bad = xr.DataArray([True],
                       dims=('x'),
                       coords=dict(x=[0],
                                   xc=('x', [0.5])))
    with pytest.raises(TypeError):
        _validate_binary_mask(bad)

    bad = xr.DataArray([[True]],
                       dims=('z', 'y'),
                       coords=dict(z=[0],
                                   y=[0],
                                   zc=('z', [0.5]),
                                   yc=('y', [0.5])))
    with pytest.raises(TypeError):
        _validate_binary_mask(bad)

    bad = xr.DataArray([[True]],
                       dims=('x', 'y'))
    with pytest.raises(TypeError):
        _validate_binary_mask(bad)


def test_from_label_image():
    label_image = np.zeros((5, 5), dtype=np.int32)
    label_image[0] = 1
    label_image[3:5, 3:5] = 2
    label_image[-1, -1] = 0

    physical_ticks = {Coordinates.Y: [1.2, 2.4, 3.6, 4.8, 6.0],
                      Coordinates.X: [7.2, 8.4, 9.6, 10.8, 12]}

    masks = list(BinaryMaskCollection.from_label_image(
        label_image, physical_ticks).masks())

    assert len(masks) == 2

    region_0, region_1 = masks

    assert region_0.name == '0'
    assert region_1.name == '1'

    assert np.array_equal(region_0, np.ones((1, 5), dtype=np.bool))
    temp = np.ones((2, 2), dtype=np.bool)
    temp[-1, -1] = False
    assert np.array_equal(region_1, temp)

    assert np.array_equal(region_0[Axes.Y.value], [0])
    assert np.array_equal(region_0[Axes.X.value], [0, 1, 2, 3, 4])

    assert np.array_equal(region_1[Axes.Y.value], [3, 4])
    assert np.array_equal(region_1[Axes.X.value], [3, 4])

    assert np.array_equal(region_0[Coordinates.Y.value],
                          physical_ticks[Coordinates.Y][0:1])
    assert np.array_equal(region_0[Coordinates.X.value],
                          physical_ticks[Coordinates.X][0:5])

    assert np.array_equal(region_1[Coordinates.Y.value],
                          physical_ticks[Coordinates.Y][3:5])
    assert np.array_equal(region_1[Coordinates.X.value],
                          physical_ticks[Coordinates.X][3:5])


def test_to_label_image():
    # test via roundtrip
    label_image = np.zeros((5, 6), dtype=np.int32)
    label_image[0] = 1
    label_image[3:6, 3:6] = 2
    label_image[-1, -1] = 0

    physical_ticks = {Coordinates.Y: [1.2, 2.4, 3.6, 4.8, 6.0],
                      Coordinates.X: [7.2, 8.4, 9.6, 10.8, 12, 15.5]}

    masks = BinaryMaskCollection.from_label_image(label_image,
                                                  physical_ticks)

    assert np.array_equal(masks.to_label_image(), label_image)


def test_save_load():
    label_image = np.zeros((5, 5), dtype=np.int32)
    label_image[0] = 1
    label_image[3:5, 3:5] = 2
    label_image[-1, -1] = 0

    physical_ticks = {Coordinates.Y: [1.2, 2.4, 3.6, 4.8, 6.0],
                      Coordinates.X: [7.2, 8.4, 9.6, 10.8, 12]}

    masks = BinaryMaskCollection.from_label_image(label_image,
                                                  physical_ticks)

    path = 'data.tgz'
    try:
        masks.save(path)
        masks2 = BinaryMaskCollection.from_disk(path)
        for m, m2 in zip(masks.masks(), masks2.masks()):
            assert np.array_equal(m, m2)
    finally:
        os.remove(path)

    # ensure that the regionprops are equal
    for ix in range(len(masks)):
        original_props = masks.mask_regionprops(ix)
        recalculated_props = masks.mask_regionprops(ix)
        assert original_props == recalculated_props
