from abc import ABC, abstractmethod
from typing import override
from llama_cpp import Llama

class AIProvider(ABC):
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

    def get_model_path(self):
        return self._model_path

    def load_model(self, model_path: str, **config):
        if self._model_path == model_path:
            return

        self._model_path = model_path

        self._load(**config)

    @abstractmethod
    def _load(self, **config):
        ...

    @abstractmethod
    def generate(self, model_path: str, **config):
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

class EmbeddingProvider(AIProvider):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            return cls._instance

        return cls._instance

    @override
    def _load(self, **config):
        self._model = Llama(
            model_path=self._model_path,
            embedding=True,
            verbose=False,
            **config
        )

    @property
    def name(self):
        return 'embedding'

    @override
    def generate(self, model_path, **config):
        self.load_model(model_path, **config)

        embeddings = self._model.create_embedding(config.get('text'))

        return embeddings['data'][0]['embedding']
