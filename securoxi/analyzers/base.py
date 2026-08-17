"""
SECUROXI AI Base Security Analyzer
"""

from abc import ABC, abstractmethod
from typing import List
from securoxi.models import TextSpan, SecurityFinding


class BaseAnalyzer(ABC):
    """Abstract base class for security analyzers."""

    @abstractmethod
    def analyze(self, spans: List[TextSpan], file_path: str = "") -> List[SecurityFinding]:
        """
        Analyze a list of TextSpan objects and return security findings.
        """
        pass
