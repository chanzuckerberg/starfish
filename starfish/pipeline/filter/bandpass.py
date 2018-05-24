from functools import partial

from trackpy import bandpass

from ._base import FilterAlgorithmBase


class Bandpass(FilterAlgorithmBase):

    def __init__(self, lshort, llong, threshold, truncate, **kwargs):
        self.lshort = lshort
        self.llong = llong
        self.threshold = threshold
        self.truncate = truncate

    @classmethod
    def get_algorithm_name(cls):
        return "bandpass"

    @classmethod
    def add_arguments(cls, group_parser):
        group_parser.add_argument("--lshort", default=0.5, type=float, help="filter signals below this frequency")
        group_parser.add_argument("--llong", default=7, type=int, help="filter signals above this frequency")
        group_parser.add_argument("--threshold", default=1, type=int, help="clip pixels below this intensity value")
        group_parser.add_argument("--truncate", default=4, type=int)

    @staticmethod
    def bandpass(image, lshort, llong, threshold, truncate):
        """Apply a bandpass filter to remove noise and background variation

        Parameters
        ----------
        image : np.ndarray
        lshort : float
            filter frequencies below this value
        llong : int
            filter frequencies above this odd integer value
        threshold : float
            zero any pixels below this intensity value
        truncate : float
            # todo document

        Returns
        -------
        np.ndarray :
            bandpassed image

        """
        bandpassed = bandpass(
            image, lshort=lshort, llong=llong, threshold=threshold,
            truncate=truncate
        )
        return bandpassed

    def filter(self, stack) -> None:
        """Perform in-place filtering of an image stack and all contained aux images.

        Parameters
        ----------
        stack : starfish.Stack
            Stack to be filtered.

        """
        bandpass_ = partial(
            self.bandpass, lshort=self.lshort, llong=self.llong, threshold=self.threshold, truncate=self.truncate
        )
        stack.image.apply(bandpass_)

        # apply to aux dict too:
        for k, val in stack.aux_dict.items():
            stack.aux_dict[k].numpy_array = self.bandpass(
                val.numpy_array, self.lshort, self.llong, self.threshold, self.truncate)
