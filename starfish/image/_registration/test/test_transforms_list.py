import tempfile

import numpy as np

from starfish import data
from starfish.image._registration._learn_transform.translation import Translation
from starfish.image._registration.transforms_list import TransformsList
from starfish.types import Axes, TransformType


ISS_SHIFTS = [[-23, 6], [-22, 2], [-22, -3], [-15, -4]]


def test_export_import_transforms_object():
    exp = data.ISS(use_test_data=True)
    stack = exp.fov().get_image('primary')
    reference_stack = exp.fov().get_image('dots')
    translation = Translation(reference_stack=reference_stack, axes=Axes.ROUND)
    # Calculate max_proj accrss CH/Z
    stack = stack.max_proj(Axes.CH, Axes.ZPLANE)
    transform_list = translation.run(stack)
    _, filename = tempfile.mkstemp()
    # save to tempfile and import
    transform_list.to_json(filename)
    imported = TransformsList.from_json(filename)
    for (_, transform_type, transform), shift in zip(imported.transforms, ISS_SHIFTS):
        # assert that each TransformationObject has the correct translation shift
        assert transform_type == TransformType.SIMILARITY
        assert np.array_equal(transform.translation, shift)
