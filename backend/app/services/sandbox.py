from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class SandboxVerdict:
    verdict: str
    score: float
    details: Dict[str, Any]


def enqueue_file_for_detonation(object_key: str) -> SandboxVerdict:
    """MVP stub: pretend to detonate and return a benign verdict.

    Later, integrate with Cuckoo/CAPEv2 or Firejail-based runners and feed
    execution logs into the ML pipeline.
    """
    return SandboxVerdict(verdict="allow", score=0.05, details={"object_key": object_key})


