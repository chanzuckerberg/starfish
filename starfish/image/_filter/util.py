from typing import Set, Tuple, Union

import numpy as np
import xarray as xr
from skimage.morphology import binary_opening, disk

from starfish.types import Indices, Number


def bin_thresh(img: np.ndarray, thresh: Number) -> np.ndarray:
    """
    Performs binary thresholding of an image

    Parameters
    ----------
    img : np.ndarray
        Image to filter.
    thresh : int
        Pixel values >= thresh are set to 1, else 0.

    Returns
    -------
    np.ndarray :
        Binarized image, same shape as input

    """
    res = img >= thresh
    return res


def bin_open(img: np.ndarray, disk_size: int) -> np.ndarray:
    """
    Performs binary opening of an image

    img : np.ndarray
        Image to filter.
    masking_radius : int
        Radius of the disk-shaped structuring element.

    Returns
    -------
    np.ndarray :
        Filtered image, same shape as input

    """
    selem = disk(disk_size)
    res = binary_opening(img, selem)
    return res


def gaussian_kernel(shape: Tuple[int, int]=(3, 3), sigma: float=0.5):
    """
    Returns a gaussian kernel of specified shape and standard deviation.
    This is a simple python implementation of Matlab's fspecial('gaussian',[shape],[sigma])

    Parameters
    ----------
    shape : Tuple[int] (default = (3, 3))
        Kernel shape.
    sigma : float (default = 0.5)
        Standard deviation of gaussian kernel.

    Parameters
    ----------
    np.ndarray :
        Gaussian kernel.
    """
    m, n = [int((ss - 1.) / 2.) for ss in shape]
    y, x = np.ogrid[-m:m + 1, -n:n + 1]
    kernel = np.exp(-(x * x + y * y) / (2. * sigma * sigma))
    kernel[kernel < np.finfo(kernel.dtype).eps * kernel.max()] = 0
    sumh = kernel.sum()
    if sumh != 0:
        kernel /= sumh
    return kernel


def validate_and_broadcast_kernel_size(
        sigma: Union[Number, Tuple[Number, ...]],
        is_volume: bool
) -> Tuple[Number, ...]:
    """
    Check that the provided sigma is of the right dimensionality, and if necessary, broadcast it
    to full dimensionality.

    Parameters
    ----------
    sigma : Union[Number, Tuple[Number]]
    is_volume : bool

    Returns
    -------
    Tuple[Number] :
        2-d or 3-d kernel size.

    """
    if isinstance(sigma, tuple):
        message = ("if passing an anisotropic kernel, the dimensionality must match the data "
                   "shape ({shape}), not {passed_shape}")
        if is_volume and len(sigma) != 3:
            raise ValueError(message.format(shape=3, passed_shape=len(sigma)))
        if not is_volume and len(sigma) != 2:
            raise ValueError(message.format(shape=2, passed_shape=len(sigma)))
        valid_sigma = sigma
    else:
        if is_volume:
            valid_sigma = (sigma,) * 3
        else:
            valid_sigma = (sigma,) * 2

    return valid_sigma


def preserve_float_range(
        array: Union[xr.DataArray, np.ndarray],
        rescale: bool=False) -> Union[xr.DataArray, np.ndarray]:
    """
    Clips values below zero to zero. If values above one are detected, clips them
    to 1 unless `rescale` is True, in which case the input is scaled by
    the max value and the dynamic range is preserved.

    Parameters
    ----------
    array : Union[xr.DataArray, np.ndarray]
        Array whose values should be in the interval [0, 1] but may not be.
    rescale: bool
        If true, scale values by the max.

    Returns
    -------
    array : Union[xr.DataArray, np.ndarray]
        Array whose values are in the interval [0, 1].

    """
    array = array.copy()
    if isinstance(array, xr.DataArray):
        data = array.values
    else:
        data = array
    if np.any(data < 0):
        data[array < 0] = 0
    if np.any(array > 1):
        if rescale:
            data /= data.max()
        else:
            data[array > 1] = 1
    return array.astype(np.float32)


def determine_axes_to_group_by(is_volume: bool) -> Set[Indices]:
    """map is_volume to axes to group by when applying a function over an ImageStack"""
    if is_volume:
        return {Indices.ROUND, Indices.CH}
    else:
        return {Indices.ROUND, Indices.CH, Indices.Z}
