import typing


class ImageBase(object):
    @property
    def numpy_array(self):
        """Retrieves the image data as a numpy array."""
        raise NotImplementedError()

    @property
    def raw_shape(self) -> typing.Optional[list]:
        """Retrieves the shape of the image data, as a list of the sizes of the indices."""
        raise NotImplementedError()

    @property
    def shape(self):
        """Retrieves the shape of the image data, as an ordered mapping between index names to the size of the index."""
        raise NotImplementedError()

    def write(self, filepath):
        """
        Writes the image out to disk.

        Args:
            filepath: The path of the file to write the image to.
        """
        raise NotImplementedError()
