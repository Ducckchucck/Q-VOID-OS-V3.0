from .llm_adapter import LLMAdapter, LLMResponse
from .prompts import *

__all__ = [
    "LLMAdapter",
    "LLMResponse",
    "THREAT_ANALYSIS_PROMPT",
    "COUNTER_EXPLOIT_PROMPT",
    "HONEYPOT_RESPONSE_PROMPT",
    "CODE_MUTATION_PROMPT",
    "NETWORK_DECEPTION_PROMPT"
]
