from abc import ABC, abstractmethod
from typing import override
from ddgs import DDGS

class SearchResult:
    ...

class WebSearchProvider(ABC):
    @property
    def name(self):
        ...

    @abstractmethod
    def search(self, **kwargs):
        ...

class WebSearchRegistry:
    _instance = None
    _search_engines = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def register(self, instance: WebSearchProvider):
        self._search_engines[instance.name] = instance

    @property
    def engines(self):
        return [
            (eng[0], eng[1]) for eng in self._search_engines.items()
        ]

    def get(self, name: str):
        if name in self._search_engines:
            return self._search_engines[name]

        return f"Error: {name} is not a valid web search engine."

class DDGSWebSearch(WebSearchProvider):
    @property
    def name(self):
        return "ddgs"

    @override
    def search(self, **kwargs):
        result = DDGS().text(
            kwargs['query'],
            max_results=kwargs['max_results']
        )

        return result
