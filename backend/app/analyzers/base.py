from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class RawObservation:
    def __init__(
        self,
        artifact_type: str,
        polarity: str, # supporting, contradicting, inconclusive
        observation: str,
        location_reference: Optional[str] = None,
        provenance: Optional[str] = None,
        artifact_id: Optional[int] = None,
        meta_info: Optional[Dict[str, Any]] = None
    ):
        self.artifact_type = artifact_type
        self.polarity = polarity
        self.observation = observation
        self.location_reference = location_reference
        self.provenance = provenance
        self.artifact_id = artifact_id
        self.meta_info = meta_info or {}

class BaseAnalyzer(ABC):
    @abstractmethod
    def analyze(self, project_dir: str, claims: List[Any], artifacts: List[Any]) -> List[RawObservation]:
        pass
