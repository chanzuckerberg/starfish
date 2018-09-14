import argparse
import io
import os
from datetime import datetime
from typing import IO, Tuple

from skimage.external import tifffile
from skimage.io import imread
from slicedimage import ImageFormat

from starfish.experiment.builder import FetchedTile, TileFetcher, write_experiment_json
from starfish.types import Indices
from starfish.util.argparse import FsExistsType

SHAPE = 1044, 1390


class IssCroppedBreastTile(FetchedTile):
    def __init__(self, file_path):
        self.file_path = file_path

    @property
    def shape(self) -> Tuple[int, ...]:
        return SHAPE

    @property
    def format(self) -> ImageFormat:
        return ImageFormat.TIFF

    @staticmethod
    def crop(img):
        crp = img[40:1084, 20:1410]
        return crp

    @property
    def tile_data_handle(self) -> IO:
        im = self.crop(imread(self.file_path))
        fh = io.BytesIO()
        with tifffile.TiffWriter(fh) as tifffh:
            tifffh.save(
                im,
                # always write with a fixed timestamp so we don't get different tile files each time
                # we run this script.
                datetime=datetime.fromtimestamp(0)
            )
        fh.seek(0)
        return fh


class ISSCroppedBreastPrimaryTileFetcher(TileFetcher):
    def __init__(self, input_dir):
        self.input_dir = input_dir

    @property
    def ch_dict(self):
        ch_dict = {0: 'FITC', 1: 'Cy3', 2: 'Cy3 5', 3: 'Cy5'}
        return ch_dict

    @property
    def hyb_dict(self):
        hyb_str = ['1st', '2nd', '3rd', '4th']
        hyb_dict = dict(enumerate(hyb_str))
        return hyb_dict

    def get_tile(self, fov: int, hyb: int, ch: int, z: int) -> FetchedTile:
        filename = 'slideA_{}_{}_{}.TIF'.format(str(fov + 1),
                                                self.hyb_dict[hyb],
                                                self.ch_dict[ch]
                                                )
        file_path = os.path.join(self.input_dir, filename)
        return IssCroppedBreastTile(file_path)


class ISSCroppedBreastAuxTileFetcher(TileFetcher):
    def __init__(self, input_dir, aux_type):
        self.input_dir = input_dir
        self.aux_type = aux_type

    def get_tile(self, fov: int, hyb: int, ch: int, z: int) -> FetchedTile:
        if self.aux_type == 'nuclei':
            filename = 'slideA_{}_DO_DAPI.TIF'.format(str(fov + 1))
        elif self.aux_type == 'dots':
            filename = 'slideA_{}_DO_Cy3.TIF'.format(str(fov + 1))
        else:
            msg = 'invalid aux type: {}'.format(self.aux_type)
            msg += ' expected either nuclei or dots'
            raise ValueError(msg)

        file_path = os.path.join(self.input_dir, filename)

        return IssCroppedBreastTile(file_path)


def format_data(input_dir, output_dir):
    def add_codebook(experiment_json_doc):
        experiment_json_doc['codebook'] = "codebook.json"
        return experiment_json_doc

    num_fovs = 16

    hyb_dimensions = {
        Indices.ROUND: 4,
        Indices.CH: 4,
        Indices.Z: 1,
    }

    aux_name_to_dimensions = {
        'nuclei': {
            Indices.ROUND: 1,
            Indices.CH: 1,
            Indices.Z: 1,
        },
        'dots': {
            Indices.ROUND: 1,
            Indices.CH: 1,
            Indices.Z: 1,
        }
    }

    write_experiment_json(output_dir,
                          num_fovs,
                          hyb_dimensions,
                          aux_name_to_dimensions,
                          primary_tile_fetcher=ISSCroppedBreastPrimaryTileFetcher(input_dir),
                          aux_tile_fetcher={
                              'nuclei': ISSCroppedBreastAuxTileFetcher(input_dir, 'nuclei'),
                              'dots': ISSCroppedBreastAuxTileFetcher(input_dir, 'dots'),
                          },
                          postprocess_func=add_codebook,
                          default_shape=SHAPE
                          )


if __name__ == "__main__":

    s3_bucket = "s3://czi.starfish.data.public/browse/raw/20180820/iss_breast/"
    input_help_msg = "Path to raw data. Raw data can be downloaded from: {}".format(s3_bucket)
    output_help_msg = "Path to output experment.json and all formatted images it references"
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir", type=FsExistsType(), help=input_help_msg)
    parser.add_argument("output_dir", type=FsExistsType(), help=output_help_msg)

    args = parser.parse_args()
    format_data(args.input_dir, args.output_dir)
