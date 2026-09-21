"""Base abstract class for all health data source parsers."""

from abc import ABC, abstractmethod
from typing import BinaryIO, TextIO, Union
import pandas as pd


class BaseHealthParser(ABC):
    """Abstract parser defining standard ingest and parse contracts."""

    @abstractmethod
    def parse(self, file_or_buffer: Union[str, BinaryIO, TextIO]) -> list[any]:
        """Parse raw file or buffer and return normalized Pydantic records."""
        pass
