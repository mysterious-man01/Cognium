from abc import ABC, abstractmethod
import time
import json
from os import path, listdir
from file_handlers.file_extractor import Extractor
from file_handlers.chunker import chunker
from providers import EmbeddingProvider, LlamacppProvider, WebSearchRegistry, WebFetchRegistry
import database as db
from config import MODELS_PATH, PLATFORM_SLASH, check_cfg_file

class Tool(ABC):
    @property
    def get_name(self) -> str:
        ...

    @property
    def get_use_schema(self) -> dict:
        ...

    @property
    def description(self) -> str:
        ...

    @abstractmethod
    def exec(self, **kwargs):
        ...

class ToolRegistry:
    _instance = None
    _tools = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def register(self, tool: Tool):
        self._tools[tool.get_name] = tool

    @property
    def tools(self):
        return [
            (tool[0], tool[1]) for tool in self._tools.items()
        ]

    def get(self, tool_name: str):
        if tool_name in self._tools:
            return self._tools[tool_name]

        return f'Error: "{tool_name}" is not a valid tool.'

class RagTool(Tool):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    @property
    def get_name(self):
        return "rag"

    @property
    def get_use_schema(self):
        return {
            "type": "function",
            "function": {
                "name": "rag",
                "description": self.get_description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_name": {
                            "type": "string",
                            "description": "Name of the uploaded document."
                        },
                        "query": {
                            "type": "string",
                            "description": "Question to search."
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Number of chunks."
                        }
                    },
                    "required": [
                        "file_name",
                        "query"
                    ]
                }
            }
        }

    @property
    def get_description(self):
        return "Search inside a text document and answer questions using its content."

    def exec(self, **kwargs):
        t_init = time.perf_counter()
        cfg = check_cfg_file()
        embedder = EmbeddingProvider()

        if cfg['embedding_model']:
            emb_model_path = path.join(MODELS_PATH, 'Embedding', cfg['embedding_model'])

            for file in listdir(emb_model_path):
                name = file.lower()

                if name.endswith('.gguf') and 'embedding' in name:
                    emb_model_path = path.join(emb_model_path, file)
                    break
        else:
            emb_model_path = LlamacppProvider.instance().get_model_path()

        # Verify if file chunks/embeddings was already saved on db
        # retrive it if true instead of regenerate all chunks end embeddings
        att = db.get_document_by_name(kwargs['file_name'])

        if not att:
            return json.dumps({
                'metadata': {
                    'document': kwargs['file_name'],
                    'latency': time.perf_counter() - t_init
                },
                'content': "File not found."
            })

        candidates = db.get_chunks(att['id'])

        if not candidates:
            file = Extractor.get(att['uri'])
            section = file.get_section()

            for chunk in chunker(section):
                chunk.embedding = embedder.generate(
                    emb_model_path,
                    text=chunk.text
                )

                # Save chunks and embedding in database
                db.save_chunk(
                    att['id'],
                    {
                        'page': chunk.page,
                        'section': chunk.section,
                        'model': path.dirname(emb_model_path).split(PLATFORM_SLASH)[-1],
                        'index': chunk.index,
                        'text': chunk.text,
                        'embedding': chunk.embedding
                    }
                )

        # Generate the query embedings for search
        query_emb = embedder.generate(emb_model_path, text=kwargs['query'])

        # Search chunks that matches with query
        candidates = db.chunk_similarity_search(att['id'], query_emb, kwargs.get('top_k', 5))

        # Retrieve resultant chunks
        return json.dumps({
            'metadata': {
                'document': kwargs['file_name'],
                'latency': time.perf_counter() - t_init,
                'chunks': len(candidates)
            },
            'content': [{
                'page': candidate['page'] + 1,
                'index': candidate['index'],
                'text': candidate['text']
            } for candidate in candidates]
        })

class SummarizeTool(Tool):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    @property
    def get_name(self):
        return "summarize"

    @property
    def get_use_schema(self):
        return {
            "type": "function",
            "function": {
                "name": "summarize",
                "description": self.get_description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_name": {
                            "type": "string",
                            "description": "Name of the uploaded document."
                        }
                    },
                    "required": [
                        "file_name"
                    ]
                }
            }
        }

    @property
    def get_description(self):
        return "Make a summary and extract important information from text."

    def exec(self, **kwargs):
        t_init = time.perf_counter()
        # Verify if file summary was already saved on db
        # retrive it if true instead of generate a new summary
        doc = db.get_document_by_name(
            kwargs['file_name']
        )

        if not doc:
            return json.dumps({
                'metadata': {
                    'file_name': kwargs['file_name'],
                    'latency': time.perf_counter() - t_init
                },
                'content': "File not found."
            })

        summary = db.get_summary({
            'document_id': doc['id']
        })

        if summary:
            return json.dumps({
                'metadata': {
                    'file_name': doc['name'],
                    'latency': time.perf_counter() - t_init
                },
                'content': summary['text']
            })

        command = {
            'role': 'system',
            'content': (
                "You are a document summarization system. "
                "Summarize the supplied document directly. "
                "Do not output a template, schema, or instructions."
            )
        }

        file = Extractor.get(doc['uri'])
        section = file.get_section()
        model = LlamacppProvider.instance()

        # Sumarize (and extract key points) from all chunks using LLM model
        raw_summary = ''
        for chunk in chunker(section):
            resume_from_model = model.generate(
                model.get_model_path(),
                messages=[
                    command, {
                        'role': 'user',
                        'content': chunk.text
                    }
                ]
            )

            for chunk in resume_from_model:
                piece = chunk.get('delta')
                if piece.get('content') is not None:
                    raw_summary += piece['content']

            raw_summary += '\n'

        # Re-run the resultant sumarization (and key point) to refine result
        refined_summary = ''
        resume_from_model = model.generate(
            model.get_model_path(),
            messages=[
                command, {
                    'role': 'user',
                    'content': raw_summary
                }
            ]
        )

        for chunk in resume_from_model:
            piece = chunk.get('delta')
            if piece.get('content') is not None:
                refined_summary += piece['content']

        refined_summary += '\n'

        # Save in database and retrieve the result
        db.save_summary(doc['id'], text=refined_summary)

        return json.dumps({
            'metadata': {
                'file_name': doc['name'],
                'latency': time.perf_counter() - t_init
            },
            'content': raw_summary
        })

class WebSearchTool(Tool):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    @property
    def get_name(self):
        return "web_search"

    @property
    def get_use_schema(self):
        return {
            "type": "function",
            "function": {
                "name": self.get_name,
                "description": self.get_description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "query for web search."
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Number of returned results."
                        }
                    },
                    "required": [
                        "query"
                    ]
                }
            }
        }

    @property
    def get_description(self):
        return (
            "Search the internet for factual and up-to-date information."
            "Returns ranked web results containing titles, URLs, domains and snippets."
            "Use this when information may be recent, uncertain or unavailable locally."
        )

    def exec(self, **kwargs):
        t_init = time.perf_counter()
        web_engine = WebSearchRegistry().get('ddgs')

        if not kwargs.get('query'):
            return json.dumps({
                'metadata': {
                    'latency': time.perf_counter() - t_init
                },
                'content': 'No query to search'
            })

        result = web_engine.search(
            query=kwargs['query'],
            max_results=kwargs.get('max_results', 10)
        )

        return json.dumps({
            'metadata': {
                'query': kwargs['query'],
                'latency': time.perf_counter() - t_init
            },
            'content': result
        })

class WebFetchTool(Tool):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    @property
    def get_name(self):
        return "web_fetch"

    @property
    def get_use_schema(self):
        return {
            "type": "function",
            "function": {
                "name": self.get_name,
                "description": self.get_description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "Target URL to fetch."
                        }
                    },
                    "required": [
                        "url"
                    ]
                }
            }
        }

    @property
    def get_description(self):
        return (
            "Search a specific url on the internet"
            "Use this for deeper information search inside a web page"
        )

    def exec(self, **kwargs):
        t_init = time.perf_counter()
        engine = WebFetchRegistry().get('trafilatura')

        if not kwargs.get('url'):
            return json.dumps({
                'metadata': {
                    'latency': time.perf_counter() - t_init
                },
                'content': 'No URL to search'
            })

        content = engine.fetch(url=kwargs['url'])

        return json.dumps({
            'metadata': {
                'url': kwargs['url'],
                'latency': time.perf_counter() - t_init
            },
            'content': {
                'url': content.url,
                'title': content.title,
                'author': content.author,
                'date': content.date,
                'page_text': content.content
            }
        })
