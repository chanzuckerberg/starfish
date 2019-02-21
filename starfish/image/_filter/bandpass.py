from functools import partial
from typing import Optional

import numpy as np
import xarray as xr
from trackpy import bandpass

from starfish.imagestack.imagestack import ImageStack
from starfish.types import Number
from starfish.util import click
from ._base import FilterAlgorithmBase
from .util import determine_axes_to_group_by, preserve_float_range


class Bandpass(FilterAlgorithmBase):

    def __init__(
            self, lshort: Number, llong: int, threshold: Number=0, truncate: Number=4,
            is_volume: bool=False) -> None:
        """

        Parameters
        ----------
        lshort : float
            filter frequencies below this value
        llong : int
            filter frequencies above this odd integer value
        threshold : float
            zero any spots below this intensity value after background subtraction (default 0)
        truncate : float
            truncate the gaussian kernel, used by the gaussian filter, at this many standard
            deviations (default 4)
        is_volume : bool
            If True, 3d (z, y, x) volumes will be filtered. By default, filter 2-d (y, x) planes
        """
        self.lshort = lshort
        self.llong = llong

        if threshold is None:
            raise ValueError("Threshold cannot be None, please pass a float or integer")

        self.threshold = threshold
        self.truncate = truncate
        self.is_volume = is_volume

    _DEFAULT_TESTING_PARAMETERS = {"lshort": 1, "llong": 3, "threshold": 0.01}

    @staticmethod
    def _bandpass(
            image: xr.DataArray, lshort: Number, llong: int, threshold: Number, truncate: Number
    ) -> np.ndarray:
        """Apply a bandpass filter to remove noise and background variation

        Parameters
        ----------
        image : np.ndarray
        lshort : float
            filter frequencies below this value
        llong : int
            filter frequencies above this odd integer value
        threshold : float
            zero any spots below this intensity value after background subtraction (default 0)
        truncate : float
            truncate the gaussian kernel, used by the gaussian filter, at this many standard
            deviations

        Returns
        -------
        np.ndarray :
            bandpassed image

        """
        bandpassed = bandpass(
            image, lshort=lshort, llong=llong, threshold=threshold,
            truncate=truncate
        )
        return preserve_float_range(bandpassed)

    def run(
            self, stack: ImageStack, in_place: bool = False, verbose: bool = False,
            n_processes: Optional[int] = None
    ) -> ImageStack:
        """Perform filtering of an image stack

        Parameters
        ----------
        stack : ImageStack
            Stack to be filtered.
        in_place : bool
            if True, process ImageStack in-place, otherwise return a new stack
        verbose : bool
            if True, report the filtering progress across the tiles or volumes of the ImageStack
        n_processes : Optional[int]
            Number of parallel processes to devote to calculating the filter

        Returns
        -------
        ImageStack :
            If in-place is False, return the results of filter as a new stack.  Otherwise return the
            original stack.

        """
        bandpass_ = partial(
            self._bandpass,
            lshort=self.lshort, llong=self.llong, threshold=self.threshold, truncate=self.truncate
        )

        group_by = determine_axes_to_group_by(self.is_volume)

        result = stack.apply(
            bandpass_,
            group_by=group_by,
            in_place=in_place,
            n_processes=n_processes,
        )
        return result

    @staticmethod
    @click.command("Bandpass")
    @click.option(
        "--lshort", type=float, help="filter signals below this frequency")
    @click.option(
        "--llong", type=int, help="filter signals above this frequency")
    @click.option(
        "--threshold", default=0, type=float, help="zero pixels below this intensity value")
    @click.option(
        "--truncate", default=4, type=float,
        help="truncate the filter at this many standard deviations")
    @click.pass_context
    def _cli(ctx, lshort, llong, threshold, truncate):
        ctx.obj["component"]._cli_run(ctx, Bandpass(lshort, llong, threshold, truncate))
