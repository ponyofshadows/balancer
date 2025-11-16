from __future__ import annotations
from typing import Protocol, TypeVar, Generic, Sequence
from .pipeline_contracts import Context, Bundle

InT = TypeVar("InT")
OutT = TypeVar("OutT")

class Stage(Protocol):
    def process(self, bundle: Bundle) -> Bundle:
        ...


class Pipeline(Generic[InT, OutT]):
    """Executes a series of stages in sequence."""
    def __init__(self, *stages: Sequence[Stage]):
        self.stages = stages

    def run(self, data: InT) -> OutT:
        bundle = Bundle(context=Context(), stream=data)

        for stage in self.stages:
            bundle = stage.process(bundle)
        return bundle

