from copy import deepcopy
from typing import Union

import numpy as np
import xarray as xr
from skimage import transform
from skimage.transform._geometric import GeometricTransform
from tqdm import tqdm

from starfish.config import StarfishConfig
from starfish.image._registration._apply_transform._base import ApplyTransformBase
from starfish.image._registration.transforms_list import TransformsList
from starfish._imagestack.imagestack import ImageStack
from starfish.types import Axes
from starfish._util import click


class Warp(ApplyTransformBase):
    """
    Applies a list of geometric transformations to an ImageStack using
    :py:func:skimage.transform.warp

    Parameters
    ----------
    stack : ImageStack
        Stack to be transformed.
    transforms_list : TransformsList
        The list of skimage transform objects to apply to the ImageStack. See a list of valid
        transform objects at https://scikit-image.org/docs/dev/api/skimage.transform.html
    in_place : bool
        if True, process ImageStack in-place, otherwise return a new stack
    verbose : bool
        if True, report on transformation progress (default = False)


    Returns
    -------
    ImageStack :
        If `in_place` is False, return the results of the transforms as a new stack.
        Otherwise return the original stack.
    """

    def run(self, stack: ImageStack, transforms_list: TransformsList,
            in_place: bool=False, verbose: bool=False, *args, **kwargs) -> ImageStack:
        if not in_place:
            # create a copy of the ImageStack, call apply on that stack with in_place=True
            image_stack = deepcopy(stack)
            return self.run(image_stack, transforms_list, in_place=True, **kwargs)
        if verbose and StarfishConfig().verbose:
            transforms_list.transforms = tqdm(transforms_list.transforms)
        all_axes = {Axes.ROUND, Axes.CH, Axes.ZPLANE}
        for selector, _, transformation_object in transforms_list.transforms:
            other_axes = all_axes - set(selector.keys())
            # iterate through remaining axes
            for axes in stack._iter_axes(other_axes):
                # combine all axes data to select one tile
                selector.update(axes)  # type: ignore
                selected_image, _ = stack.get_slice(selector)
                warped_image = warp(selected_image, transformation_object, **kwargs
                                    ).astype(np.float32)
                stack.set_slice(selector, warped_image)
        return stack

    @staticmethod
    @click.command("Warp")
    @click.pass_context
    def _cli(ctx):
        ctx.obj["component"]._cli_run(ctx, Warp())


def warp(image: Union[xr.DataArray, np.ndarray],
         transformation_object: GeometricTransform,
         **kwargs
         ) -> np.ndarray:
    """
    Wrapper around :py:func:`skimage.transform.warp`. Warps an image according to a
    given coordinate transformation.

    Parameters
    ----------
    image : np.ndarray
        The image to be transformed
    transformation_object : :py:class:`~skimage.transform._geometric.GeometricTransform`
        The transformation object to apply.

    Returns
    -------
    np.ndarray :
        the warped image.
    """
    return transform.warp(image, transformation_object, **kwargs)
