# from dataclasses import dataclass, field
# from typing import Dict

# @dataclass
# class TokenCounter:
    # role_usage: Dict[str, Dict[str,int]] = field(default_factory=dict)
    # total: int = 0

    # def add(self, role: str, usage: Dict[str,int]):
        # self.role_usage.setdefault(role, {"prompt":0,"completion":0,"total":0})
        # self.role_usage[role]["prompt"] += usage.get("prompt_tokens", 0)
        # self.role_usage[role]["completion"] += usage.get("completion_tokens", 0)
        # t = usage.get("total_tokens", 0)
        # self.role_usage[role]["total"] += t
        # self.total += t
        
import tiktoken

class TokenCounter:
    def __init__(self):
        self.usage_log = {}

    def add(self, role, usage):
        # usage is expected to be a dict with 'prompt_tokens', 'completion_tokens', 'total_tokens'
        self.usage_log.setdefault(role, []).append(usage)

    def count(self, text: str) -> int:
        try:
            import tiktoken
            enc = tiktoken.get_encoding("cl100k_base")
            return len(enc.encode(text))
        except Exception:
            return len(text.split())

    @property
    def total(self) -> int:
        """Return total tokens used across all roles."""
        total = 0
        for role_usages in self.usage_log.values():
            for u in role_usages:
                if "total_tokens" in u:
                    total += u["total_tokens"]
                elif "prompt_tokens" in u or "completion_tokens" in u:
                    total += u.get("prompt_tokens", 0) + u.get("completion_tokens", 0)
        return total