from abc import abstractmethod
from typing import Type

from starfish._imagestack.imagestack import ImageStack
from starfish._pipeline.algorithmbase import AlgorithmBase
from starfish._pipeline.pipelinecomponent import PipelineComponent
from starfish._util import click
from starfish._util.click.indirectparams import ImageStackParamType


class Filter(PipelineComponent):
    @classmethod
    def _cli_run(cls, ctx, instance):
        output = ctx.obj["output"]
        stack = ctx.obj["stack"]
        filtered = instance.run(stack)
        filtered.export(output)

    @staticmethod
    @click.group("Filter")
    @click.option("-i", "--input", type=ImageStackParamType)
    @click.option("-o", "--output", required=True)
    @click.pass_context
    def _cli(ctx, input, output):
        """smooth, sharpen, denoise, etc"""
        print("Filtering images...")
        ctx.obj = dict(
            component=Filter,
            input=input,
            output=output,
            stack=input,
        )


class FilterAlgorithmBase(AlgorithmBase):
    @classmethod
    def get_pipeline_component_class(cls) -> Type[PipelineComponent]:
        return Filter

    @abstractmethod
    def run(self, stack: ImageStack, *args) -> ImageStack:
        """Perform filtering of an image stack"""
        raise NotImplementedError()
