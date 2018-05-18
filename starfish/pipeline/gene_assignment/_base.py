class GeneAssignmentAlgorithm(object):
    @classmethod
    def get_algorithm_name(cls):
        """
        Returns the name of the algorithm.  This should be a valid python identifier, i.e.,
        https://docs.python.org/3/reference/lexical_analysis.html#identifiers
        """
        raise NotImplementedError()

    @classmethod
    def add_arguments(cls, parser):
        """Adds the arguments for the algorithm."""
        raise NotImplementedError()

    def assign_genes(self, spots, regions):
        """Performs gene assignment given the spots and the regions."""
        raise NotImplementedError()
