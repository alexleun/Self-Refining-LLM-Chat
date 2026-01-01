from dataclasses import dataclass, field
from typing import Dict

@dataclass
class TokenCounter:
    role_usage: Dict[str, Dict[str,int]] = field(default_factory=dict)
    total: int = 0

    def add(self, role: str, usage: Dict[str,int]):
        self.role_usage.setdefault(role, {"prompt":0,"completion":0,"total":0})
        self.role_usage[role]["prompt"] += usage.get("prompt_tokens", 0)
        self.role_usage[role]["completion"] += usage.get("completion_tokens", 0)
        t = usage.get("total_tokens", 0)
        self.role_usage[role]["total"] += t
        self.total += t