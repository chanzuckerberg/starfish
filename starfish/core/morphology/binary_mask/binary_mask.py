import os
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import (
    Any,
    Hashable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Optional,
    Sequence,
    Tuple,
    Union,
)

import numpy as np
import xarray as xr
from skimage.measure import regionprops
from skimage.measure._regionprops import _RegionProperties

from starfish.core.morphology.label_image import LabelImage
from starfish.core.morphology.util import (
    _get_axes_names,
    _normalize_physical_ticks,
    _normalize_pixel_ticks,
)
from starfish.core.types import ArrayLike, Axes, Coordinates, Number
from starfish.core.util.logging import Log
from .expand import fill_from_mask


@dataclass
class MaskData:
    binary_mask: np.ndarray
    offsets: Tuple[int, ...]
    region_properties: Optional[_RegionProperties]


class BinaryMaskCollection:
    """Collection of binary masks with a dict-like access pattern.

    Parameters
    ----------
    pixel_ticks : Union[Mapping[Axes, ArrayLike[int]], Mapping[str, ArrayLike[int]]]
        A map from the axis to the values for that axis.
    physical_ticks : Union[Mapping[Coordinates, ArrayLike[Number]],
                                   Mapping[str, ArrayLike[Number]]
        A map from the physical coordinate type to the values for axis.  For 2D label images,
        X and Y physical coordinates must be provided.  For 3D label images, Z physical
        coordinates must also be provided.
    masks : Sequence[MaskData]
        A sequence of data for binary masks.

    Attributes
    ----------
    max_shape : Mapping[Axes, int]
        Maximum index of contained masks.
    """
    def __init__(
            self,
            pixel_ticks: Union[Mapping[Axes, ArrayLike[int]], Mapping[str, ArrayLike[int]]],
            physical_ticks: Union[Mapping[Coordinates, ArrayLike[Number]],
                                  Mapping[str, ArrayLike[Number]]],
            masks: Sequence[MaskData],
            log: Optional[Log],
    ):
        self._pixel_ticks: Mapping[Axes, ArrayLike[int]] = _normalize_pixel_ticks(pixel_ticks)
        self._physical_ticks: Mapping[Coordinates, ArrayLike[Number]] = _normalize_physical_ticks(
            physical_ticks)
        self._masks: MutableMapping[int, MaskData] = {}
        self._log: Log = log or Log()

        for ix, mask_data in enumerate(masks):
            if mask_data.binary_mask.ndim not in (2, 3):
                raise TypeError(f"expected 2 or 3 dimensions; got {mask_data.binary_mask.ndim}")
            if mask_data.binary_mask.dtype != np.bool:
                raise ValueError(f"expected dtype of bool; got {mask_data.binary_mask.dtype}")

            self._masks[ix] = mask_data

        if len(self._pixel_ticks) != len(self._physical_ticks):
            raise ValueError(
                "pixel_ticks should have the same cardinality as physical_ticks")
        for axis, coord in zip(*_get_axes_names(len(self._pixel_ticks))):
            if axis not in self._pixel_ticks:
                raise ValueError(f"pixel ticks missing {axis.value} data")
            if coord not in self._physical_ticks:
                raise ValueError(f"physical coordinate ticks missing {coord.value} data")
            if len(self._pixel_ticks[axis]) != len(self._physical_ticks[coord]):
                raise ValueError(
                    f"pixel ticks for {axis.name} does not have the same cardinality as physical "
                    f"coordinates ticks for {coord.name}")

    def __getitem__(self, index: int) -> xr.DataArray:
        return self._format_mask_as_xarray(index)

    def __iter__(self) -> Iterator[Tuple[int, xr.DataArray]]:
        for mask_index in self._masks.keys():
            yield mask_index, self._format_mask_as_xarray(mask_index)

    def __len__(self) -> int:
        return len(self._masks)

    def _format_mask_as_xarray(self, index: int) -> xr.DataArray:
        """Convert a np-based mask into an xarray DataArray."""
        mask_data = self._masks[index]
        max_mask_name_len = len(str(len(self._masks) - 1))

        xr_dims: MutableSequence[str] = []
        xr_coords: MutableMapping[Hashable, Any] = {}

        for ix, (axis, coord) in enumerate(zip(*_get_axes_names(len(self._pixel_ticks)))):
            xr_dims.append(axis.value)
            start_offset = mask_data.offsets[ix]
            end_offset = mask_data.offsets[ix] + mask_data.binary_mask.shape[ix]
            xr_coords[axis.value] = self._pixel_ticks[axis.value][start_offset:end_offset]
            xr_coords[coord.value] = (
                axis.value, self._physical_ticks[coord.value][start_offset:end_offset])

        return xr.DataArray(
            mask_data.binary_mask,
            dims=xr_dims,
            coords=xr_coords,
            name=f"{index:0{max_mask_name_len}d}"
        )

    def uncropped_mask(self, index: int) -> xr.DataArray:
        """Some of the binary mask collections builders will crop the binary masks when constructing
        the collection.  The purpose is to exclude the regions of the image that are entirely False.
        Use this method to obtain the mask sized according to the pixel and physical shape provided
        for the entire binary mask collection, use this method."""
        mask_data = self._masks[index]
        uncropped_shape = tuple(
            len(self._pixel_ticks[axis])
            for axis, _ in zip(*_get_axes_names(len(self._pixel_ticks)))
        )

        if uncropped_shape == mask_data.binary_mask.shape:
            return self._format_mask_as_xarray(index)

        max_mask_name_len = len(str(len(self._masks) - 1))

        xr_dims: MutableSequence[str] = []
        xr_coords: MutableMapping[Hashable, Any] = {}

        for ix, (axis, coord) in enumerate(zip(*_get_axes_names(len(self._pixel_ticks)))):
            xr_dims.append(axis.value)
            xr_coords[axis.value] = self._pixel_ticks[axis.value]
            xr_coords[coord.value] = (axis.value, self._physical_ticks[coord.value])

        image = np.zeros(
            shape=tuple(
                len(self._pixel_ticks[axis])
                for axis, _ in zip(*_get_axes_names(len(self._pixel_ticks)))
            ),
            dtype=np.bool,
        )
        fill_from_mask(
            mask_data.binary_mask,
            mask_data.offsets,
            1,
            image,
        )
        return xr.DataArray(
            image,
            dims=xr_dims,
            coords=xr_coords,
            name=f"{index:0{max_mask_name_len}d}"
        )

    def masks(self) -> Iterator[xr.DataArray]:
        for mask_index in self._masks.keys():
            yield self._format_mask_as_xarray(mask_index)

    def mask_regionprops(self, mask_id: int) -> _RegionProperties:
        """
        Return the region properties for a given mask.

        Parameters
        ----------
        mask_id : int
            The mask ID for the mask.

        Returns
        -------
        _RegionProperties
            The region properties for that mask.
        """
        mask_data = self._masks[mask_id]
        if mask_data.region_properties is None:
            # recreate the label image (but with just this mask)
            image = np.zeros(
                shape=tuple(
                    len(self._pixel_ticks[axis])
                    for axis, _ in zip(*_get_axes_names(len(self._pixel_ticks)))
                ),
                dtype=np.uint32,
            )
            fill_from_mask(
                mask_data.binary_mask,
                mask_data.offsets,
                mask_id + 1,
                image,
            )
            mask_data.region_properties = regionprops(image.data)
        return mask_data.region_properties

    @property
    def max_shape(self) -> Mapping[Axes, int]:
        return {
            axis: len(self._pixel_ticks[axis])
            for ix, (axis, _) in enumerate(zip(*_get_axes_names(len(self._pixel_ticks))))
        }

    @classmethod
    def from_label_image(cls, label_image: LabelImage) -> "BinaryMaskCollection":
        """Creates binary masks from a label image.  Masks are cropped to the smallest size that
        contains the non-zero values, but pixel and physical coordinates ticks are retained.  Masks
        extracted from BinaryMaskCollections will be cropped.  To extract masks sized to the
        original label image, use :py:meth:`starfish.BinaryMaskCollection.uncropped_mask`.

        Parameters
        ----------
        label_image : LabelImage
            LabelImage to extract binary masks from.

        Returns
        -------
        masks : BinaryMaskCollection
            Masks generated from the label image.
        """
        props = regionprops(label_image.xarray.data)

        pixel_ticks = {
            axis.value: label_image.xarray.coords[axis.value]
            for axis, _ in zip(*_get_axes_names(label_image.xarray.ndim))
            if axis.value in label_image.xarray.coords
        }
        physical_ticks = {
            coord.value: label_image.xarray.coords[coord.value]
            for _, coord in zip(*_get_axes_names(label_image.xarray.ndim))
            if coord.value in label_image.xarray.coords
        }
        masks: Sequence[MaskData] = [
            MaskData(prop.image, prop.bbox[:label_image.xarray.ndim], prop)
            for prop in props
        ]
        log = deepcopy(label_image.log)

        return cls(
            pixel_ticks,
            physical_ticks,
            masks,
            log,
        )

    @classmethod
    def from_binary_arrays_and_ticks(
            cls,
            arrays: Sequence[np.ndarray],
            pixel_ticks: Optional[Union[
                Mapping[Axes, ArrayLike[int]],
                Mapping[str, ArrayLike[int]]]],
            physical_ticks: Union[
                Mapping[Coordinates, ArrayLike[Number]],
                Mapping[str, ArrayLike[Number]]],
            log: Optional[Log],
    ) -> "BinaryMaskCollection":
        """Constructs a BinaryMaskCollection from an array containing the labels, a set of physical
        coordinates, and an optional log of how this label image came to be.  Masks are cropped to
        the smallest size that contains the non-zero values, but pixel and physical coordinates
        ticks are retained.  Masks extracted from BinaryMaskCollections will be cropped.  To extract
        masks sized to the original label image, use
        :py:meth:`starfish.BinaryMaskCollection.uncropped_mask`.


        Parameters
        ----------
        arrays : Sequence[np.ndarray]
            A set of 2D or 3D binary arrays.  The ordering of the axes must be Y, X for 2D images
            and ZPLANE, Y, X for 3D images.  The arrays must have identical sizes and match the
            sizes of pixel_ticks and physical_ticks.
        pixel_ticks : Optional[Union[Mapping[Axes, ArrayLike[int]],
                                     Mapping[str, ArrayLike[int]]]]
            A map from the axis to the values for that axis.  For any axis that exist in the array
            but not in pixel_ticks, the pixel coordinates are assigned from 0..N-1, where N is
            the size along that axis.
        physical_ticks : Union[Mapping[Coordinates, ArrayLike[Number]],
                               Mapping[str, ArrayLike[Number]]]
            A map from the physical coordinate type to the values for axis.  For 2D label images,
            X and Y physical coordinates must be provided.  For 3D label images, Z physical
            coordinates must also be provided.
        log : Optional[Log]
            A log of how this label image came to be.

        Returns
        -------
        masks : BinaryMaskCollection
            Masks generated from the label image.
        """
        array_shapes = set(array.shape for array in arrays)
        array_dtypes = set(array.dtype for array in arrays)
        if len(array_shapes) > 1:
            raise ValueError("all masks must be identically sized")
        for array_dtype in array_dtypes:
            if array_dtype != np.bool:
                raise TypeError("arrays must be binary data")

        # normalize the pixel coordinates to Mapping[Axes, ArrayLike[int]]
        pixel_ticks = _normalize_pixel_ticks(pixel_ticks)
        # normalize the physical coordinates to Mapping[Coordinates, ArrayLike[Number]]
        physical_ticks = _normalize_physical_ticks(physical_ticks)

        # If we have 1 or more arrays, verify that the physical coordinate array's size matches the
        # array's size.  In BinaryMaskCollection's constructor, it is verified that the pixel
        # tick array's size matches that of the physical coordinate array's size.
        if len(array_shapes) == 1:
            array_shape = next(iter(array_shapes))

            # verify that we don't have extra
            expected_axes, expected_physical_coords = _get_axes_names(len(array_shape))
            actual_real_coordinates_provided = set(expected_physical_coords)
            actual_real_coordinates_provided.intersection_update(set(physical_ticks.keys()))

            if len(array_shape) != len(actual_real_coordinates_provided):
                raise ValueError(
                    f"physical coordinates provided for {len(actual_real_coordinates_provided)} "
                    f"axes ({actual_real_coordinates_provided}), but the data has "
                    f"{len(array_shape)} axes"
                )

            for ix, (axis, coord) in enumerate(zip(*_get_axes_names(len(array_shape)))):
                if (coord in physical_ticks
                        and len(physical_ticks[coord]) != array_shape[ix]):
                    raise ValueError(
                        f"The size of the array for physical coordinates for {coord.name} "
                        f"({len(physical_ticks[coord])} does not match the array's shape "
                        f"({array_shape[ix]})."
                    )

        # Add all pixel ticks not present.
        for axis, coord in zip(*_get_axes_names(3)):
            if coord in physical_ticks and axis not in pixel_ticks:
                pixel_ticks[axis] = np.arange(0, len(physical_ticks[coord]))

        masks: MutableSequence[MaskData] = list()
        for array in arrays:
            selection_range: Sequence[slice] = BinaryMaskCollection._crop_mask(array)

            masks.append(MaskData(
                array[selection_range],
                tuple(selection.start for selection in selection_range),
                None
            ))

        log = deepcopy(log)

        return cls(
            pixel_ticks,
            physical_ticks,
            masks,
            log,
        )

    @staticmethod
    def _crop_mask(array: np.ndarray) -> Sequence[slice]:
        selection_range: MutableSequence[slice] = list()

        # calculate the first and last True pixel across each axis.
        for axis_num in range(array.ndim):
            projection_axes = tuple(dim for dim in range(array.ndim) if dim != axis_num)
            # max project across the projections
            max_projection = np.amax(array, axis=projection_axes)
            # get the indices of the non-zero elements.  the [0] is because np.nonzero captures
            # the indices of each dimension separately, and we want the one and only dimension.
            non_zero_indices = np.nonzero(max_projection)[0]

            if len(non_zero_indices) == 0:
                selection_range.append(slice(0, 0))
            else:
                selection_range.append(slice(non_zero_indices[0], non_zero_indices[-1] + 1))

        return selection_range

    @classmethod
    def from_label_array_and_ticks(
            cls,
            array: np.ndarray,
            pixel_ticks: Optional[Union[
                Mapping[Axes, ArrayLike[int]],
                Mapping[str, ArrayLike[int]]]],
            physical_ticks: Union[
                Mapping[Coordinates, ArrayLike[Number]],
                Mapping[str, ArrayLike[Number]]],
            log: Optional[Log],
    ) -> "BinaryMaskCollection":
        """Constructs a BinaryMaskCollection from an array containing the labels, a set of physical
        coordinates, and an optional log of how this label image came to be.  Masks are cropped to
        the smallest size that contains the non-zero values, but pixel and physical coordinates
        ticks are retained.  Masks extracted from BinaryMaskCollections will be cropped.  To extract
        masks sized to the original label image, use
        :py:meth:`starfish.BinaryMaskCollection.uncropped_mask`.

        Parameters
        ----------
        array : np.ndarray
            A 2D or 3D array containing the labels.  The ordering of the axes must be Y, X for 2D
            images and ZPLANE, Y, X for 3D images.
        pixel_ticks : Optional[Union[Mapping[Axes, ArrayLike[int]],
                                     Mapping[str, ArrayLike[int]]]]
            A map from the axis to the values for that axis.  For any axis that exist in the array
            but not in pixel_ticks, the pixel coordinates are assigned from 0..N-1, where N is
            the size along that axis.
        physical_ticks : Union[Mapping[Coordinates, ArrayLike[Number]],
                               Mapping[str, ArrayLike[Number]]]
            A map from the physical coordinate type to the values for axis.  For 2D label images,
            X and Y physical coordinates must be provided.  For 3D label images, Z physical
            coordinates must also be provided.
        log : Optional[Log]
            A log of how this label image came to be.

        Returns
        -------
        masks : BinaryMaskCollection
            Masks generated from the label image.
        """
        # normalize the pixel coordinates to Mapping[Axes, ArrayLike[int]]
        pixel_ticks = _normalize_pixel_ticks(pixel_ticks)
        # normalize the physical coordinates to Mapping[Coordinates, ArrayLike[Number]]
        physical_ticks = _normalize_physical_ticks(physical_ticks)

        for ix, (axis, coord) in enumerate(zip(*_get_axes_names(array.ndim))):
            # We verify that the physical coordinate array's size matches the array's size.  In
            # BinaryMaskCollection's constructor, it is verified that the pixel coordinate array's
            # size matches that of the physical coordinate array's size.
            if coord not in physical_ticks:
                raise ValueError(f"Missing physical coordinates for {coord.name}")
            if len(physical_ticks[coord]) != array.shape[ix]:
                raise ValueError(
                    f"The size of the array for physical coordinates for {coord.name} "
                    f"({len(physical_ticks[coord])} does not match the array's shape "
                    f"({array.shape[ix]})."
                )
            if axis not in pixel_ticks:
                pixel_ticks[axis] = np.arange(0, array.shape[ix])

        props = regionprops(array)

        masks: Sequence[MaskData] = [
            MaskData(prop.image, prop.bbox[:array.ndim], prop)
            for prop in props
        ]
        log = deepcopy(log)

        return cls(
            pixel_ticks,
            physical_ticks,
            masks,
            log,
        )

    def to_label_image(self) -> LabelImage:
        shape = tuple(
            len(self._pixel_ticks[axis])
            for axis in (Axes.ZPLANE, Axes.Y, Axes.X)
            if axis in self._pixel_ticks
        )
        label_image_array = np.zeros(shape=shape, dtype=np.uint16)
        for ix, mask_data in self._masks.items():
            fill_from_mask(
                mask_data.binary_mask,
                mask_data.offsets,
                ix + 1,
                label_image_array,
            )

        return LabelImage.from_label_array_and_ticks(
            label_image_array,
            self._pixel_ticks,
            self._physical_ticks,
            self._log,
        )

    @classmethod
    def open_targz(cls, path: Union[str, Path]) -> "BinaryMaskCollection":
        """Load the collection saved as a .tar.gz file from disk

        Parameters
        ----------
        path : Union[str, Path]
            Path of the tar file to instantiate from.

        Returns
        -------
        masks : BinaryMaskCollection
            Collection of binary masks.
        """
        with open(os.fspath(path), "rb") as fh:
            return _io.BinaryMaskIO.read_versioned_binary_mask(fh)

    def to_targz(self, path: Union[str, Path]):
        """Save the binary masks to disk as a .tar.gz file.

        Parameters
        ----------
        path : Union[str, Path]
            Path of the tar file to write to.
        """
        with open(os.fspath(path), "wb") as fh:
            _io.BinaryMaskIO.write_versioned_binary_mask(fh, self)


# these need to be at the end to avoid recursive imports
from . import _io  # noqa
