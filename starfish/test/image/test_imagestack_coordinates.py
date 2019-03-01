from typing import Mapping, Tuple, Union

import numpy as np
from slicedimage import ImageFormat

from starfish.experiment.builder import FetchedTile, tile_fetcher_factory
from starfish.imagestack.imagestack import ImageStack
from starfish.imagestack.physical_coordinate_calculator import get_physical_coordinates_of_z_plane
from starfish.types import Coordinates, Number
from .imagestack_test_utils import verify_physical_coordinates

NUM_ROUND = 8
NUM_CH = 1
NUM_Z = 1
HEIGHT = 10
WIDTH = 10


X_COORDS = 100, 1000
Y_COORDS = .1, 10
Z_COORDS = 0.01, 0.001

def round_to_z(r: int) -> Tuple[float, float]:
    return (r + 1) * 0.01, (r + 1) * 0.001


def round_to_x(r: int) -> Tuple[float, float]:
    return (r + 1) * 0.001, (r + 1) * 0.0001


def round_to_y(r: int) -> Tuple[float, float]:
    return (r + 1) * 0.1, (r + 1) * 1


class AlignedTiles(FetchedTile):
    """Tiles that are physically offset based on round."""

    def __init__(self, fov: int, _round: int, ch: int, z: int) -> None:
        super().__init__()
        self._round = _round

    @property
    def shape(self) -> Tuple[int, ...]:
        return HEIGHT, WIDTH

    @property
    def coordinates(self) -> Mapping[Union[str, Coordinates], Union[Number, Tuple[Number, Number]]]:
        return {
            Coordinates.X: X_COORDS,
            Coordinates.Y: Y_COORDS,
            Coordinates.Z: Z_COORDS,
        }

    @property
    def format(self) -> ImageFormat:
        return ImageFormat.TIFF

    def tile_data(self) -> np.ndarray:
        return np.ones((HEIGHT, WIDTH), dtype=np.float32)


def test_coordinates():
    """Set up an ImageStack with tiles that are aligned.  Verify that the coordinates
    retrieved match.
    """
    stack = ImageStack.synthetic_stack(
        NUM_ROUND, NUM_CH, NUM_Z,
        HEIGHT, WIDTH,
        tile_fetcher=tile_fetcher_factory(
            AlignedTiles,
            True,
        )
    )

    verify_physical_coordinates(
        stack,
        X_COORDS,
        Y_COORDS,
        get_physical_coordinates_of_z_plane(Z_COORDS),
    )


class ScalarTiles(FetchedTile):
    """Tiles that have a single scalar coordinate."""
    def __init__(self, fov: int, _round: int, ch: int, z: int) -> None:
        super().__init__()
        self._round = _round

    @property
    def shape(self) -> Tuple[int, ...]:
        return HEIGHT, WIDTH

    @property
    def coordinates(self) -> Mapping[Union[str, Coordinates], Union[Number, Tuple[Number, Number]]]:
        return {
            Coordinates.X: X_COORDS[0],
            Coordinates.Y: Y_COORDS[0],
            Coordinates.Z: Z_COORDS[0],
        }

    @property
    def format(self) -> ImageFormat:
        return ImageFormat.TIFF

    def tile_data(self) -> np.ndarray:
        return np.ones((HEIGHT, WIDTH), dtype=np.float32)


class OffsettedTiles(FetchedTile):
    """Tiles that are physically offset based on round."""
    def __init__(self, fov: int, _round: int, ch: int, z: int) -> None:
        super().__init__()
        self._round = _round

    @property
    def shape(self) -> Tuple[int, ...]:
        return HEIGHT, WIDTH

    @property
    def coordinates(self) -> Mapping[Union[str, Coordinates], Union[Number, Tuple[Number, Number]]]:
        return {
            Coordinates.X: round_to_x(self._round),
            Coordinates.Y: round_to_y(self._round),
            Coordinates.Z: round_to_z(self._round),
        }

    @property
    def format(self) -> ImageFormat:
        return ImageFormat.TIFF

    def tile_data(self) -> np.ndarray:
        return np.ones((HEIGHT, WIDTH), dtype=np.float32)


def test_unaligned_tiles():
    """Test that imagestack error is thrown when constructed with unaligned tiles"""

    try:
        ImageStack.synthetic_stack(
            NUM_ROUND, NUM_CH, NUM_Z,
            HEIGHT, WIDTH,
            tile_fetcher=tile_fetcher_factory(
                OffsettedTiles,
                True,
            )
        )
    except ValueError as e:
        # Assert value error is thrown with right message
        assert e.args[0] == "Tiles must be aligned"


def test_scalar_coordinates():
    """Set up an ImageStack where only a single scalar physical coordinate is provided per axis.
    Internally, this should be converted to a range where the two endpoints are identical to the
    physical coordinate provided.
    """
    stack = ImageStack.synthetic_stack(
        NUM_ROUND, NUM_CH, NUM_Z,
        HEIGHT, WIDTH,
        tile_fetcher=tile_fetcher_factory(
            ScalarTiles,
            True,
        )
    )

    expected_x = X_COORDS[0]
    expected_y = Y_COORDS[0]
    expected_z = Z_COORDS[0]

    verify_physical_coordinates(
        stack,
        (expected_x, expected_x),
        (expected_y, expected_y),
        (expected_z, expected_z)
    )
