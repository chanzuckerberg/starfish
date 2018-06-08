from typing import Tuple

import numpy as np
import pandas as pd
from skimage.feature import blob_log

from starfish.constants import Indices
from starfish.munge import melt
from starfish.pipeline.features.encoded_spots import EncodedSpots
from starfish.pipeline.features.spot_attributes import SpotAttributes
from ._base import SpotFinderAlgorithmBase


class GaussianSpotDetector(SpotFinderAlgorithmBase):

    def __init__(self, min_sigma, max_sigma, num_sigma, threshold, blobs_image_name, measurement_type='max', **kwargs):
        """Multi-dimensional gaussian spot detector

        Parameters
        ----------
        min_sigma : float
            The minimum standard deviation for Gaussian Kernel. Keep this low to
            detect smaller blobs.
        max_sigma : float
            The maximum standard deviation for Gaussian Kernel. Keep this high to
            detect larger blobs.
        num_sigma : int
            The number of intermediate values of standard deviations to consider
            between `min_sigma` and `max_sigma`.
        threshold : float
            The absolute lower bound for scale space maxima. Local maxima smaller
            than thresh are ignored. Reduce this to detect blobs with less
            intensities.
        blobs_image_name : str
            name of the image containing blobs. Must be present in the auxiliary_images of the Stack passed to `find`
        measurement_type : str ['max', 'mean']
            name of the function used to calculate the intensity for each identified spot area

        """
        self.min_sigma = min_sigma
        self.max_sigma = max_sigma
        self.num_sigma = num_sigma
        self.threshold = threshold
        self.blobs = blobs_image_name

        try:
            self.measurement_function = getattr(np, measurement_type)
        except AttributeError:
            raise ValueError(
                f'measurement_type must be a numpy reduce function such as "max" or "mean". {measurement_type} '
                f'not found.')

    @staticmethod
    def measure_blob_intensity(image, spots, measurement_function) -> pd.Series:
        def fn(row):
            x_min = int(round(row.x_min))
            x_max = int(round(row.x_max))
            y_min = int(round(row.y_min))
            y_max = int(round(row.y_max))
            return measurement_function(image[x_min:x_max, y_min:y_max])
        return spots.apply(
            fn,
            axis=1
        )

    def encode(self, stack, spot_attributes):
        # create stack squeeze map
        squeezed = stack.squeeze()
        mapping: pd.DataFrame = stack.image.tile_metadata
        inds = range(mapping.shape[0])
        intensities = [
            self.measure_blob_intensity(image, spot_attributes, self.measurement_function)
            for image in squeezed
        ]
        d = dict(zip(inds, intensities))
        d['spot_id'] = range(spot_attributes.shape[0])

        res = pd.DataFrame(d)

        res: pd.DataFrame = melt(
            df=res,
            new_index_name='barcode_index',
            new_value_name='intensity',
            melt_columns=inds
        )
        res = pd.merge(res, mapping, on='barcode_index', how='left')
        return EncodedSpots(res)

    def fit(self, blobs_image):
        fitted_blobs = pd.DataFrame(
            data=blob_log(blobs_image, self.min_sigma, self.max_sigma, self.num_sigma, self.threshold),
            columns=['x', 'y', 'r'],
        )
        # TODO ambrosejcarr: why is this necessary? (check docs)
        fitted_blobs['r'] *= np.sqrt(2)
        fitted_blobs[['x', 'y']] = fitted_blobs[['x', 'y']].astype(int)

        fitted_blobs['x_min'] = np.clip(np.floor(fitted_blobs.x - fitted_blobs.r), 0, None)
        fitted_blobs['x_max'] = np.clip(np.ceil(fitted_blobs.x + fitted_blobs.r), None, blobs_image.shape[0])
        fitted_blobs['y_min'] = np.clip(np.floor(fitted_blobs.y - fitted_blobs.r), 0, None)
        fitted_blobs['y_max'] = np.clip(np.ceil(fitted_blobs.y + fitted_blobs.r), None, blobs_image.shape[1])

        # TODO ambrosejcarr this should be barcode intensity or position intensity
        fitted_blobs['intensity'] = self.measure_blob_intensity(blobs_image, fitted_blobs, self.measurement_function)
        fitted_blobs['spot_id'] = np.arange(fitted_blobs.shape[0])

        return SpotAttributes(fitted_blobs)

    def find(self, image_stack) -> Tuple[SpotAttributes, EncodedSpots]:
        blobs = image_stack.auxiliary_images[self.blobs].max_proj(Indices.HYB, Indices.CH, Indices.Z)
        spot_attributes = self.fit(blobs)
        encoded_spots = self.encode(image_stack, spot_attributes.data)
        return spot_attributes, encoded_spots

    @classmethod
    def get_algorithm_name(cls):
        return 'gaussian_spot_detector'

    @classmethod
    def add_arguments(cls, group_parser):
        group_parser.add_argument("--blobs-image-name", type=str, help='aux image key')
        group_parser.add_argument(
            "--min-sigma", default=4, type=int, help="Minimum spot size (in standard deviation)")
        group_parser.add_argument(
            "--max-sigma", default=6, type=int, help="Maximum spot size (in standard deviation)")
        group_parser.add_argument("--num-sigma", default=20, type=int, help="Number of scales to try")
        group_parser.add_argument("--threshold", default=.01, type=float, help="Dots threshold")
        group_parser.add_argument(
            "--show", default=False, action='store_true', help="display results visually")
