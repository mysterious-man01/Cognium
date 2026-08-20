from .ai_provider import *
from .tool_provider import *

def bootstrap():
    ai_registry = AIRegistry()

    ai_registry.register(
        LlamacppProvider()
    )
    ai_registry.register(
        EmbeddingProvider()
    )

    tool_registry = ToolRegistry()

    tool_registry.register(
        RagTool()
    )
    tool_registry.register(
        SummarizeTool()
    )

bootstrap()
