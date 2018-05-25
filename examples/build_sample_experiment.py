import argparse
import json
import os
from typing import IO, Tuple

from io import BytesIO

import numpy
from skimage.io import imsave
from slicedimage import (
    Collection,
    ImageFormat,
    Tile,
    TileSet,
    Writer,
)

from starfish.constants import Coordinates, Indices
from starfish.util.argparse import FsExistsType


AUX_IMAGE_NAMES = {
    'nuclei',
    'dots',
}


def tile_opener(toc_path, tile, file_ext):
    tile_basename = os.path.splitext(toc_path)[0]
    return open(
        "{}-Z{}-H{}-C{}.{}".format(
            tile_basename,
            tile.indices[Indices.Z],
            tile.indices[Indices.HYB],
            tile.indices[Indices.CH],
            ImageFormat.TIFF.file_ext,
        ),
        "wb")


def tile_writer(tile, fh):
    tile.copy(fh)
    return ImageFormat.TIFF


def fov_path_generator(parent_toc_path, toc_name):
    toc_basename = os.path.splitext(os.path.basename(parent_toc_path))[0]
    return os.path.join(
        os.path.dirname(parent_toc_path),
        "{}-{}.json".format(toc_basename, toc_name),
    )


class FetchedImage:
    """
    This is the contract for providing the data for constructing a :class:`slicedimage.Tile`.
    """
    @property
    def shape(self) -> Tuple[int, ...]:
        raise NotImplementedError()

    @property
    def format(self) -> ImageFormat:
        raise NotImplementedError()

    @property
    def image_data_handle(self) -> IO:
        raise NotImplementedError()


class ImageFetcher:
    """
    This is the contract for providing the image data for constructing a :class:`slicedimage.Collection`.
    """
    def get_image(self, fov: int, hyb: int, ch: int, z: int) -> FetchedImage:
        """
        Given fov, hyb, ch, and z, return an instance of a :class:`.FetchedImage` that can be queried for the image
        data.
        """
        raise NotImplementedError()


class RandomNoiseImage(FetchedImage):
    """
    This is a simple implementation of :class:`.FetchedImage` that simply regenerates random data for the image.
    """
    @property
    def shape(self) -> Tuple[int, ...]:
        return 1536, 1024

    @property
    def format(self) -> ImageFormat:
        return ImageFormat.TIFF

    def image_data_handle(self) -> IO:
        arr = numpy.random.randint(0, 256, size=self.shape, dtype=numpy.uint8)
        output = BytesIO()
        imsave(output, arr, plugin="tifffile")
        output.seek(0)
        return output


class RandomNoiseImageFetcher(ImageFetcher):
    """
    This is a simple implementation of :class:`.ImageFetcher` that simply returns a :class:`.RandomNoiseImage` for every
    fov, hyb, ch, z combination.
    """
    def get_image(self, fov: int, hyb: int, ch: int, z: int) -> FetchedImage:
        return RandomNoiseImage()


def build_image(fov_count, hyb_count, ch_count, z_count, image_fetcher: ImageFetcher, default_shape=(1536, 1024)):
    """
    Build and returns an image set with the following characteristics:

    Parameters
    ----------
    fov_count : int
        Number of fields of view in this image set.
    hyb_count : int
        Number for hybridizations in this image set.
    ch_count : int
        Number for channels in this image set.
    z_count : int
        Number of z-layers in this image set.
    default_shape : Tuple[int, int]
        Default shape of the individual tiles in this image set.

    Returns
    -------
    The slicedimage collection representing the image.
    """
    collection = Collection()
    for fov_ix in range(fov_count):
        fov_images = TileSet(
            [Coordinates.X, Coordinates.Y, Indices.Z, Indices.HYB, Indices.CH],
            {Indices.HYB: hyb_count, Indices.CH: ch_count, Indices.Z: z_count},
            default_shape,
            ImageFormat.TIFF,
        )

        for z_ix in range(z_count):
            for hyb_ix in range(hyb_count):
                for ch_ix in range(ch_count):
                    image = image_fetcher.get_image(fov_ix, hyb_ix, ch_ix, z_ix)
                    tile = Tile(
                        {
                            Coordinates.X: (0.0, 0.0001),
                            Coordinates.Y: (0.0, 0.0001),
                            Coordinates.Z: (0.0, 0.0001),
                        },
                        {
                            Indices.Z: z_ix,
                            Indices.HYB: hyb_ix,
                            Indices.CH: ch_ix,
                        },
                        image.shape,
                    )
                    tile.set_source_fh_contextmanager(image.image_data_handle, image.format)
                    fov_images.add_tile(tile)
        collection.add_partition("fov_{:03}".format(fov_ix), fov_images)
    return collection


def write_experiment_json(
        path,
        fov_count,
        hyb_dimensions,
        aux_name_to_dimensions,
        hyb_image_fetcher=None,
        aux_image_fetcher=None,
        postprocess_func=None,
):
    """
    Build and returns a top-level experiment description with the following characteristics:

    Parameters
    ----------
    path : str
        Directory to write the files to.
    fov_count : int
        Number of fields of view in this experiment.
    hyb_dimensions : Mapping[str, int]
        Dictionary mapping dimension name to dimension size for the hybridization image.
    aux_name_to_dimensions : Mapping[str, Mapping[str, int]]
        Dictionary mapping the auxiliary image type to dictionaries, which map from dimension name to dimension size.
    hyb_image_fetcher : Optional[ImageFetcher]
        ImageFetcher for hybridization images.  If not provided, defaults to :class:`RandomNoiseImageFetcher`.
    aux_image_fetcher : Optional[Mapping[str, ImageFetcher]]
        ImageFetchers for auxiliary images.  If an entry is not found for the auxiliary image type, this defaults to
        :class:`RandomNoiseImageFetcher`.
    postprocess_func : Optional[Callable[[dict], dict]]
        If provided, this is called with the experiment document for any postprocessing.  The callable should return
        what is to be written as the experiment document.
    """
    if hyb_image_fetcher is None:
        hyb_image_fetcher = DumbImageFetcher()
    if aux_image_fetcher is None:
        aux_image_fetcher = {}
    if postprocess_func is None:
        postprocess_func = lambda doc: doc

    experiment_doc = {
        'version': "0.0.0",
        'auxiliary_images': {},
        'extras': {},
    }
    hybridization_image = build_image(
        fov_count,
        hyb_dimensions[Indices.HYB], hyb_dimensions[Indices.CH], hyb_dimensions[Indices.Z],
        hyb_image_fetcher)
    Writer.write_to_path(
        hybridization_image,
        os.path.join(path, "hybridization.json"),
        pretty=True,
        partition_path_generator=fov_path_generator,
        tile_opener=tile_opener,
        tile_writer=tile_writer,
    )
    experiment_doc['hybridization_images'] = "hybridization.json"

    for aux_name, aux_dimensions in aux_name_to_dimensions.items():
        if aux_dimensions is None:
            continue
        auxiliary_image = build_image(
            fov_count,
            aux_dimensions[Indices.HYB], aux_dimensions[Indices.CH], aux_dimensions[Indices.Z],
            aux_image_fetcher.get(aux_name, DumbImageFetcher())
        )
        Writer.write_to_path(
            auxiliary_image,
            os.path.join(path, "{}.json".format(aux_name)),
            pretty=True,
            partition_path_generator=fov_path_generator,
            tile_opener=tile_opener,
            tile_writer=tile_writer,
        )
        experiment_doc['auxiliary_images'][aux_name] = "{}.json".format(aux_name)

    experiment_doc = postprocess_func(experiment_doc)
    with open(os.path.join(path, "experiment.json"), "w") as fh:
        json.dump(experiment_doc, fh, indent=4)


class StarfishIndex:
    def __call__(self, spec_json):
        try:
            spec = json.loads(spec_json)
        except json.decoder.JSONDecodeError:
            raise argparse.ArgumentTypeError("Could not parse {} into a valid index specification.".format(spec_json))

        return {
            Indices.HYB: spec.get(Indices.HYB, 1),
            Indices.CH: spec.get(Indices.CH, 1),
            Indices.Z: spec.get(Indices.Z, 1),
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "output_dir",
        type=FsExistsType())
    parser.add_argument(
        "--fov-count",
        type=int,
        required=True,
        help="Number of FOVs in this experiment.")
    parser.add_argument(
        "--hybridization-dimensions",
        type=StarfishIndex(),
        required=True,
        help="Dimensions for the hybridization images.  Should be a json dict, with {}, {}, and {} as the possible "
             "keys.  The value should be the shape along that dimension.  If a key is not present, the value is "
             "assumed to be 0.".format(
            Indices.HYB.value,
            Indices.CH.value,
            Indices.Z.value))
    name_arg_map = dict()
    for aux_image_name in AUX_IMAGE_NAMES:
        arg = parser.add_argument(
            "--{}-dimensions".format(aux_image_name),
            type=StarfishIndex(),
            help="Dimensions for the {} images.  Should be a json dict, with {}, {}, and {} as the possible keys.  The "
                 "value should be the shape along that dimension.  If a key is not present, the value is assumed to be "
                 "0.".format(aux_image_name, Indices.HYB.value, Indices.CH.value, Indices.Z.value))
        name_arg_map[aux_image_name] = arg.dest

    args = parser.parse_args()

    write_experiment_json(
        args.output_dir, args.fov_count, args.hybridization_dimensions,
        {
            aux_image_name: getattr(args, name_arg_map[aux_image_name])
            for aux_image_name in AUX_IMAGE_NAMES
        }
    )
