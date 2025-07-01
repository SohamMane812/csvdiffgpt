"""Package for restructure analyzers."""

from .base import BaseRestructureAnalyzer, register_analyzer, get_all_analyzers
from .redundancy_analyzer import RedundancyAnalyzer
from .normalization_analyzer import NormalizationAnalyzer
from .type_consistency_analyzer import TypeConsistencyAnalyzer
from .relationship_analyzer import RelationshipAnalyzer

__all__ = [
    "BaseRestructureAnalyzer", 
    "register_analyzer", 
    "get_all_analyzers",
    "RedundancyAnalyzer",
    "NormalizationAnalyzer",
    "TypeConsistencyAnalyzer",
    "RelationshipAnalyzer"
]