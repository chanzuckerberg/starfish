import numpy as np
import xarray as xr

from starfish import IntensityTable
from starfish.test import test_utils
from starfish.types import Coordinates, Features
from starfish.types._constants import OverlapStrategy
from starfish.util.overlap_utils import Area, remove_area_of_xarray, sel_area_of_xarray, find_overlaps_of_xarrays


def create_intenisty_table_with_coords(area: Area, n_spots=10):
    """
    Creates a 50X50 intensity table with physical coordinates within
    the given Area.
    """
    codebook = test_utils.codebook_array_factory()
    it = IntensityTable.synthetic_intensities(
        codebook,
        num_z=1,
        height=50,
        width=50,
        n_spots=n_spots
    )
    # intensity table 1 has 10 spots, xmin = 0, ymin = 0, xmax = 2, ymax = 1
    it[Coordinates.X.value] = xr.DataArray(np.linspace(area.min_x, area.max_x, n_spots), dims=Features.AXIS)
    it[Coordinates.Y.value] = xr.DataArray(np.linspace(area.min_y, area.max_y, n_spots), dims=Features.AXIS)
    return it


def test_find_area_intersection():
    area1 = Area(min_x=0, max_x=2, min_y=0, max_y=2)
    area2 = Area(min_x=1, max_x=2, min_y=1, max_y=3)
    intersection = Area.find_intersection(area1, area2)
    # intersection should be area with bottom point (1,1) and top point (2,2)
    assert intersection == Area(min_x=1, max_x=2, min_y=1, max_y=2)

    area2 = Area(min_x=3, max_x=5, min_y=3, max_y=5)
    intersection = Area.find_intersection(area1, area2)
    # no intersection
    assert intersection is None

    area2 = Area(min_x=0, max_x=5, min_y=3, max_y=5)
    # area 2 right above area one
    assert intersection is None


def test_find_overlaps_of_xarrays():
    # Create some overlapping intensity tables
    it0 = create_intenisty_table_with_coords(Area(min_x=0, max_x=1, min_y=0, max_y=1))
    it1 = create_intenisty_table_with_coords(Area(min_x=.5, max_x=2, min_y=.5, max_y=1.5))
    it2 = create_intenisty_table_with_coords(Area(min_x=1.5, max_x=2.5, min_y=0, max_y=1))
    it3 = create_intenisty_table_with_coords(Area(min_x=0, max_x=1, min_y=1, max_y=2))
    overlaps= find_overlaps_of_xarrays([it0, it1, it2, it3])
    # should have 4 total overlaps
    assert len(overlaps) == 4
    # overlap 1 between it0 and it1:
    overlap_1 = Area(min_x=.5, max_x=1, min_y=.5, max_y=1)
    assert overlap_1 == overlaps[(0, 1)]
    # overlap 2 between it1 and it2
    overlap_2 = Area(min_x=1.5, max_x=2, min_y=.5, max_y=1)
    assert overlap_2 == overlaps[(1, 2)]
    # overlap 3 between it1 and it3
    overlap_3 = Area(min_x=.5, max_x=1, min_y=1, max_y=1.5)
    assert overlap_3 == overlaps[(1, 3)]
    # overlap 4 between it0 and it3
    overlap_4 = Area(min_x=0, max_x=1, min_y=1, max_y=1)
    assert overlap_4 == overlaps[(0, 3)]


def test_remove_area_of_xarray():
    it = create_intenisty_table_with_coords(Area(min_x=0, max_x=2, min_y=0, max_y=2), n_spots=10)

    area = Area(min_x=1, max_x=2, min_y=1, max_y=3)
    # grab some random coord values in this range
    removed_x = it.where(it.xc > 1, drop=True)[Coordinates.X.value].data[0]
    removed_y = it.where(it.yc > 1, drop=True)[Coordinates.X.value].data[3]

    it = remove_area_of_xarray(it, area)
    # assert coords from removed section are no longer in it
    assert not np.any(np.isclose(it[Coordinates.X.value], removed_x))
    assert not np.any(np.isclose(it[Coordinates.Y.value], removed_y))


def test_sel_area_of_xarray():
    it = create_intenisty_table_with_coords(Area(min_x=0, max_x=2, min_y=0, max_y=2), n_spots=10)

    area = Area(min_x=1, max_x=2, min_y=1, max_y=3)
    it = sel_area_of_xarray(it, area)

    # Assert noew min/max values
    assert min(it[Coordinates.X.value]).data >= 1
    assert max(it[Coordinates.X.value]).data <= 2
    assert min(it[Coordinates.Y.value]).data >= 1
    assert max(it[Coordinates.X.value]).data <= 2


def test_take_max():
    it1 = create_intenisty_table_with_coords( Area(min_x=0, max_x=2, min_y=0, max_y=2), n_spots=10)
    it2 = create_intenisty_table_with_coords(Area(min_x=1, max_x=2, min_y=1, max_y=3), n_spots=20)

    concatenated = IntensityTable.concatanate_intensity_tables([it1, it2],
                                                               process_overlaps=True,
                                                               overlap_strategy=OverlapStrategy.TAKE_MAX)

    # The overlap section hits half of the spots from each intensity table, 5 from it1 and 10 from i21.
    # It2 wins and the resulting concatenated table should have all the spots from it2 (20) and 6 from
    # it1 (6) for a total of 26 spots
    assert concatenated.sizes[Features.AXIS] == 26
