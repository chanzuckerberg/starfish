import json
import os

import numpy as np
import pandas as pd
from slicedimage import ImageFormat, TileSet, Tile
from slicedimage.io import resolve_path_or_url, Writer

from starfish.constants import Coordinates, Indices
from .image import ImageStack
from .munge import list_to_stack


class Stack:
    def __init__(self):
        # data organization
        self.org = None
        self.image = None

        # auxilary images
        self.aux_dict = dict()

        # readers and writers
        self.write_fn = np.save  # asserted for now

        # backend & baseurl
        self.backend = None
        self.baseurl = None

    def read(self, in_json_path_or_url):
        self.backend, name, self.baseurl = resolve_path_or_url(in_json_path_or_url)
        with self.backend.read_file_handle(name) as fh:
            self.org = json.load(fh)

        self.image = ImageStack.from_url(self.org['hybridization_images'], self.baseurl)
        self._read_aux()

    def _read_aux(self):
        for aux_key, aux_data in self.org['auxiliary_images'].items():
            self.aux_dict[aux_key] = ImageStack.from_url(aux_data, self.baseurl)

    # TODO should this thing write npy?
    def write(self, dir_name):
        self._write_stack(dir_name)
        self._write_aux(dir_name)
        self._write_metadata(dir_name)

    def _write_metadata(self, dir_name):
        with open(os.path.join(dir_name, 'experiment.json'), 'w') as outfile:
            json.dump(self.org, outfile, indent=4)

    def _write_stack(self, dir_name):
        stack_path = os.path.join(dir_name, "hybridization.json")
        self.image.write(stack_path)
        self.org['hybridization_images'] = stack_path

    def _write_aux(self, dir_name):
        for aux_key, aux_data in self.org['auxiliary_images'].items():
            self.aux_dict[aux_key].write(os.path.join(dir_name, aux_data))

    def set_stack(self, new_stack):
        if self.image.raw_shape != new_stack.shape:
            msg = "Shape mismatch. Current data shape: {}, new data shape: {}".format(
                self.image.shape, new_stack.shape)
            raise AttributeError(msg)
        self.image.numpy_array = new_stack

    def set_aux(self, key, img):
        if key in self.aux_dict:
            old_img = self.aux_dict[key]
            if old_img.shape != img.shape:
                msg = "Shape mismatch. Current data shape: {}, new data shape: {}".format(
                    old_img.shape, img.shape)
                raise AttributeError(msg)
            self.aux_dict[key].numpy_array = img
        else:
            # TODO: (ttung) major hack alert
            tileset = TileSet(
                {
                    Indices.HYB,
                    Indices.CH,
                    Indices.Z,
                    Coordinates.X,
                    Coordinates.Y,
                },
                {
                    Indices.HYB: 1,
                    Indices.CH: 1,
                    Indices.Z: 1,
                }
            )
            tile = Tile(
                {
                    Coordinates.X: (0.000, 0.001),
                    Coordinates.Y: (0.000, 0.001),
                },
                {
                    Indices.HYB: 0,
                    Indices.CH: 0,
                    Indices.Z: 0,
                },
                img.shape,
            )
            tile.numpy_array = img
            tileset.add_tile(tile)

            self.aux_dict[key] = ImageStack(tileset)
            self.org['auxiliary_images'][key] = f"{key}.json"

    def max_proj(self, *dims):
        return self.image.max_proj(*dims)

    def squeeze(self, bit_map_flag=False):
        first_dim = self.image.num_hybs * self.image.num_chs * self.image.num_zlayers

        new_shape = (first_dim,) + self.image.tile_shape
        new_data = self.image.numpy_array.reshape(new_shape)

        ind = np.arange(first_dim)

        # e.g., 0, 1, 2, 3 --> 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3
        hyb = np.tile(np.repeat(np.arange(self.image.num_hybs), self.image.num_chs), self.image.num_zlayers)

        # e.g., 0, 1, 2, 3 --> 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3
        ch = np.tile(np.arange(self.image.num_chs), self.image.num_hybs * self.image.num_zlayers)

        # e.g., 0, 1, 2, 3 --> 0 (repeated 16 times), 1 (repeated 16 times), ...
        zlayers = np.repeat(np.arange(self.image.num_zlayers), self.image.num_hybs * self.image.num_chs)

        self.squeeze_map = pd.DataFrame(dict(ind=ind, hyb=hyb, ch=ch, zlayers=zlayers))

        if bit_map_flag:
            mp = [(d[Indices.HYB], d[Indices.CH], d['bit']) for d in self.org['data']]
            mp = pd.DataFrame(mp, columns=[Indices.HYB, Indices.CH, 'bit'])
            self.squeeze_map = pd.merge(self.squeeze_map, mp, on=[Indices.CH, Indices.HYB], how='left')

        return new_data

    def un_squeeze(self, stack):
        if type(stack) is list:
            stack = list_to_stack(stack)

        new_shape = (self.image.num_hybs, self.image.num_chs, self.image.num_zlayers) + self.image.tile_shape
        res = stack.reshape(new_shape)
        return res
