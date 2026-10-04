from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
from trafilatura import fetch_url, extract

@dataclass
class WebFetchResponse:
    url: str
    title: str
    author: str | None
    date: str | None
    content: str

class WebFetchProvider(ABC):
    @property
    def name(self):
        ...

    @abstractmethod
    def fetch(self, **kwargs) -> WebFetchResponse:
        ...

class WebFetchRegistry:
    _instance = None
    _engines = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def register(self, instance: WebFetchProvider):
        self._engines[instance.name] = instance

    @property
    def extractors(self):
        return [(ext[0], ext[1]) for ext in self._engines.items()]

    def get(self, name: str):
        if name in self._engines:
            return self._engines[name]

        return f"Error: {name} is not a valid web fetch engine."

class TrafilaturaWebFetch(WebFetchProvider):
    @property
    def name(self):
        return "trafilatura"

    def fetch(self, **kwargs):
        if not kwargs.get('url'):
            return 'URL not found'

        html_page = fetch_url(kwargs['url'])
        if not html_page:
            return f"page from \"{kwargs['url']}\" not found"

        extracted_content = extract(
            html_page,
            with_metadata=True,
            output_format='json',
            include_comments=False
        )
        if not extracted_content:
            return f"Extraction of \"{kwargs['url']}\" has failed"

        content = json.loads(extracted_content)

        return WebFetchResponse(
            url=kwargs['url'],
            title=content['title'],
            author=content['author'],
            date=content['date'],
            content=content['raw_text']
        )
