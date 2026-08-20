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

class LlamacppProvider(AIProvider):
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
            chat_format=None, #config.get('chat_format', "chatml-function-calling"),
            verbose=False,
            n_gpu_layers=-1, #config.get('n_gpu_layers', 99),
            flash_attn=config.get('flash_attn', False),
            n_ctx=config.get('n_ctx', 8192)
        )

    @property
    def name(self):
        return 'llamacpp'

    def tokenize(self, data: str):
        if self._model:
            return self._model.tokenize(text=data.encode())

        raise RuntimeError("Model not loaded")

    def _stream_generator(self, stream):
        for chunk in stream:
            yield chunk['choices'][0]

    @override
    def generate(
        self,
        model_path,
        **config
    ):
        self.load_model(model_path, **config)

        streaming = config.get('stream', True)

        response = self._model.create_chat_completion(
            messages=config.get('messages', []),
            tools=config.get('tools', []),
            tool_choice=config.get('tool_choice', 'none'),
            response_format=config.get('response_format', None),
            max_tokens=config.get('max_tokens', -1),
            temperature=config.get('temp', 0.8),
            top_k=config.get('top_k', 40),
            top_p=config.get('top_p', 0.95),
            min_p=config.get('min_p', 0.05),
            stream=streaming
        )

        if streaming:
            return self._stream_generator(response)

        return response['choices'][0]

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
