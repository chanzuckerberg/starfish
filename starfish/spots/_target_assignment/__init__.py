import os
from typing import Type

import numpy as np
from skimage.io import imread

import click

from starfish.intensity_table.intensity_table import IntensityTable
from starfish.pipeline import AlgorithmBase, PipelineComponent
from . import label
from ._base import TargetAssignmentAlgorithm


class TargetAssignment(PipelineComponent):

    @classmethod
    def _get_algorithm_base_class(cls) -> Type[AlgorithmBase]:
        return TargetAssignmentAlgorithm

    @classmethod
    def _cli_run(cls, ctx, instance):
        output = ctx.obj["output"]
        intensity_table = ctx.obj["intensity_table"]
        label_image = ctx.obj["label_image"]
        intensities = instance.run(intensity_table, label_image)
        print(f"Writing intensities, including cell ids to {output}")
        intensities.save(os.path.join(output))


@click.group("target_assignment")
@click.option("--label-image", required=True, type=click.Path(exists=True))
@click.option("--intensities", required=True, type=click.Path(exists=True))
@click.option("-o", "--output", required=True)
@click.pass_context
def _cli(ctx, coordinates_geojson, intensities, output):

    print('Assigning targets to cells...')
    ctx.obj = dict(
        component=TargetAssignment,
        output=output,
        intensity_table=IntensityTable.load(intensities)
    )


TargetAssignment._cli = _cli  # type: ignore
TargetAssignment._cli_register()
