"""
SECUROXI AI Base Document Parser
"""

from abc import ABC, abstractmethod
from typing import List
from securoxi.models import TextSpan


class BaseParser(ABC):
    """Abstract base class for document parsers."""

    @abstractmethod
    def parse(self, file_path: str) -> List[TextSpan]:
        """
        Extract text spans and layout/style metadata from a document file.
        Returns a list of TextSpan objects.
        """
        pass
