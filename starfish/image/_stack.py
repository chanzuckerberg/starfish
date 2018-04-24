import os

import numpy
from slicedimage import Reader, Writer

from ._base import ImageBase


class ImageStack(ImageBase):
    def __init__(self, image_partition):
        self._image_partition = image_partition
        self._num_hybs = image_partition.get_dimension_shape('hyb')
        self._num_chs = image_partition.get_dimension_shape('ch')
        self._tile_shape = tuple(image_partition.default_tile_shape)

        self._data = numpy.zeros((self._num_hybs, self._num_chs) + self._tile_shape)
        self._data_needs_writeback = False

        for tile in image_partition.tiles():
            h = tile.indices['hyb']
            c = tile.indices['ch']
            self._data[h, c, :] = tile.numpy_array

    @classmethod
    def from_image_stack(cls, image_stack_name_or_url, baseurl):
        image_partition = Reader.parse_doc(image_stack_name_or_url, baseurl)

        return ImageStack(image_partition)

    @property
    def numpy_array(self):
        result = self._data.view()
        result.setflags(write=False)
        return result

    @numpy_array.setter
    def numpy_array(self, data):
        self._data = data.view()
        self._data_needs_writeback = True
        data.setflags(write=False)

    @property
    def shape(self):
        if self._data is None:
            return None
        else:
            return self._data.shape

    @property
    def num_hybs(self):
        return self._num_hybs

    @property
    def num_chs(self):
        return self._num_chs

    @property
    def tile_shape(self):
        return self._tile_shape

    def write(self, filepath, tile_opener=None):
        if self._data_needs_writeback:
            for tile in self._image_partition.tiles():
                h = tile.indices['hyb']
                c = tile.indices['ch']
                tile.numpy_array = self._data[h, c, :]
            self._data_needs_writeback = False

        seen_x_coords, seen_y_coords = set(), set()
        for tile in self._image_partition.tiles():
            seen_x_coords.add(tile.coordinates['x'])
            seen_y_coords.add(tile.coordinates['y'])

        sorted_x_coords = sorted(seen_x_coords)
        sorted_y_coords = sorted(seen_y_coords)
        x_coords_to_idx = {coords: idx for idx, coords in enumerate(sorted_x_coords)}
        y_coords_to_idx = {coords: idx for idx, coords in enumerate(sorted_y_coords)}
        # TODO: should handle Z.

        if tile_opener is None:
            def tile_opener(toc_path, tile, ext):
                tile_basename = os.path.splitext(toc_path)[0]
                xcoord = tile.coordinates['x']
                ycoord = tile.coordinates['y']
                xcoord = tuple(xcoord) if isinstance(xcoord, list) else xcoord
                ycoord = tuple(ycoord) if isinstance(ycoord, list) else ycoord
                xval = x_coords_to_idx[xcoord]
                yval = y_coords_to_idx[ycoord]
                return open(
                    "{}-X{}-Y{}-H{}-C{}.{}".format(
                        tile_basename,
                        xval,
                        yval,
                        tile.indices['hyb'],
                        tile.indices['ch'],
                        ext,
                    ),
                    "wb")

        Writer.write_to_path(
            self._image_partition,
            filepath,
            pretty=True,
            tile_opener=tile_opener)

    def max_proj(self, dim):
        valid_dims = ['hyb', 'ch', 'z']
        if dim not in valid_dims:
            msg = "Dimension: {} not supported. Expecting one of: {}".format(dim, valid_dims)
            raise ValueError(msg)

        if dim == 'hyb':
            res = numpy.max(self._data, axis=0)
        elif dim == 'ch':
            res = numpy.max(self._data, axis=1)
        elif dim == 'z' and len(self._tile_shape) > 2:
            res = numpy.max(self._data, axis=4)
        else:
            res = self._data

        return res
