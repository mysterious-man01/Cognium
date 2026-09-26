from typing import Any
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class ModelResponse:
    content_type: str
    content: Any
    metadata: dict | None = None

class AIProvider(ABC):
    _model_name = None
    _model_path = None
    _model = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    @property
    def name(self):
        ...

    @property
    def model_name(self):
        return self._model_name

    def get_model_path(self):
        return self._model_path

    def load_model(self, model_name: str, **config):
        if self._model_name == model_name:
            return

        self._model_name = model_name

        self._load(**config)

    @abstractmethod
    def _load(self, **config):
        ...

    @abstractmethod
    def generate(self, model_name: str, **config):
        ...

class AIRegistry:
    _instance = None
    _providers = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def register(self, provider: AIProvider):
        self._providers[provider.name] = provider

    @property
    def providers(self):
        return self._providers.keys()

    def get(self, provider_name: str):
        return self._providers[provider_name]
