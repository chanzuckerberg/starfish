from enum import Enum


class AugmentedEnum(Enum):
    def __hash__(self):
        return self.value.__hash__()

    def __eq__(self, other):
        if isinstance(other, type(self)) or isinstance(other, str):
            return self.value == other
        return False

    def __str__(self) -> str:
        return self.value


class Coordinates(AugmentedEnum):
    Z = 'zc'
    Y = 'yc'
    X = 'xc'


PHYSICAL_COORDINATE_DIMENSION = "physical_coordinate"

"""
This is the xarray dimension name for the physical coordinates of the tiles.
"""

STARFISH_EXTRAS_KEY = 'starfish'
"""
Attribute on Imagestack and IntensityTable for storing starfish related info
"""
LOG = "log"
"""
This is name of the provenance log attribute stored on the IntensityTable
"""
CORE_DEPENDENCIES = ['numpy', 'scikit-image', 'pandas', 'scikit-learn', 'scipy', 'xarray', 'sympy']
"""
The set of dependencies whose versions are are logged for each starfish session
"""


class PhysicalCoordinateTypes(AugmentedEnum):
    """
    These are more accurately the xarray coordinates for the physical coordinates of a tile.
    """
    Z_MAX = 'zmax'
    Z_MIN = 'zmin'
    Y_MAX = 'ymax'
    Y_MIN = 'ymin'
    X_MAX = 'xmax'
    X_MIN = 'xmin'


class Axes(AugmentedEnum):
    ROUND = 'r'
    CH = 'c'
    ZPLANE = 'z'
    Y = 'y'
    X = 'x'


class Features:
    """
    contains constants relating to the codebook and feature (spot/pixel) representations of the
    image data
    """

    AXIS = 'features'
    TARGET = 'target'
    CODEWORD = 'codeword'
    CODE_VALUE = 'v'
    SPOT_RADIUS = 'radius'
    DISTANCE = 'distance'
    PASSES_THRESHOLDS = 'passes_thresholds'
    CELL_ID = 'cell_id'
    SPOT_ID = 'spot_id'
    INTENSITY = 'intensity'
