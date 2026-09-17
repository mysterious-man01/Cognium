from .ai_provider import *
from .llamacpp.llamacpp_provider import LlamacppProvider, LlamacppEmbedProvider
from .web_search_provider import *
from .web_fetch_provider import *
from .tool_provider import *

def bootstrap():
    # AI Registry
    ai_registry = AIRegistry()

    ai_registry.register(
        LlamacppProvider()
    )
    ai_registry.register(
        LlamacppEmbedProvider()
    )

    # Web Search Engine Register
    search_registry = WebSearchRegistry()

    search_registry.register(
        DDGSWebSearch()
    )

    # Web Fetch Engine Register
    fetch_registry = WebFetchRegistry()

    fetch_registry.register(
        TrafilaturaWebFetch()
    )

    # Tool Resgistry
    tool_registry = ToolRegistry()

    tool_registry.register(
        RagTool()
    )
    tool_registry.register(
        SummarizeTool()
    )
    tool_registry.register(
        WebSearchTool()
    )
    tool_registry.register(
        WebFetchTool()
    )

bootstrap()
