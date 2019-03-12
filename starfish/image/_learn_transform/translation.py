from typing import List, Mapping, Tuple, Union

import numpy as np
from skimage.feature import register_translation
from skimage.transform._geometric import SimilarityTransform

from starfish.imagestack.imagestack import ImageStack
from starfish.types import Axes
from starfish.util import click
from ._base import LearnTransformBase


class Translation(LearnTransformBase):

    def __init__(self, reference_stack: Union[str, ImageStack], upsampling: int=1):
        self.upsampling = upsampling
        if isinstance(reference_stack, ImageStack):
            self.reference_stack = reference_stack
        else:
            self.reference_stack = ImageStack.from_path_or_url(reference_stack)

    def run(self, stack: ImageStack, axis: Axes
            ) -> List[Tuple[Mapping[Axes, int], SimilarityTransform]]:
        """Iterate over the given axis of an imagestack and learn the Similarity transform based off the
        instantiated reference_image.
        Parameters
        ----------
        stack : ImageStack
            Stack to be transformed.
        axis:
            The aixs to iterate over
        Returns
        -------
        List[Tuple[Any, SimilarityTransform]] :
            A list of tuples containing the round of the Imagestack and associated transform.
        """

        transforms: List[Tuple[Mapping[Axes, int], SimilarityTransform]] = list()
        reference_image = np.squeeze(self.reference_stack.xarray)
        for a in stack.axis_labels(axis):
            target_image = np.squeeze(stack.sel({axis: a}).xarray)
            if len(target_image.shape) is not 2:
                raise ValueError(
                    "Only axes: " + axis.value + " can have a length > 1"
                )

            shift, error, phasediff = register_translation(src_image=target_image,
                                                           target_image=reference_image,
                                                           upsample_factor=self.upsampling)
            print(f"For {axis}: {a}, Shift: {shift}, Error: {error}")
            selectors = {axis: a}
            shift = shift[::-1]
            transforms.append((selectors, SimilarityTransform(translation=shift)))

        return transforms

    @staticmethod
    @click.command("Translation")
    @click.option("--reference-stack", required=True, type=click.Path(exists=True),
                  help="The image stack to align the input image stack to.")
    @click.pass_context
    def _cli(ctx, reference_stack):
        ctx.obj["component"]._cli_run(ctx, Translation(reference_stack=reference_stack))
