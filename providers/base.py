"""Abstract provider interfaces (the contract every model backend implements).

PURPOSE
    Define *what* a provider can do — without saying *how*. The chains and graph
    nodes import these interfaces, never a concrete provider, so cloud (Gemini)
    and local (opus-mt) backends can be swapped transparently.

WHAT TO BUILD HERE
    - Abstract base classes for chat/completion and translation.
    - A standardized result type (text, tokens_used, model, confidence).
    - Abstract methods like complete(), translate(), is_available().
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ProviderResult:
    text: str
    tokens_used: int
    model: str
    confidence: float


class ChatProvider(ABC):
    """Interface for providers that support chat/completion (QA, summarization, extraction)."""

    @abstractmethod
    def complete(self, prompt: str, **kwargs) -> ProviderResult: ...

    @abstractmethod
    def is_available(self) -> bool: ...


class TranslationProvider(ABC):
    """Interface for providers that support source_lang -> target_lang translation."""

    @abstractmethod
    def translate(self, text: str, source_lang: str, target_lang: str) -> ProviderResult: ...

    @abstractmethod
    def is_available(self) -> bool: ...
