import json
from enum import Enum
from dataclasses import dataclass, field
from typing import Any
from providers import AIRegistry, AIProvider, ToolRegistry
from .memory_module import AgentMemory

MAX_REPETITIONS = 8

class AgentStatus(Enum):
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELED = 'canceled'

class DecissorResponse:
    _tool_name = ''
    _parameters = ''

    def __init__(self, content: str):
        try:
            obj = json.loads(content)

            if obj.get('tool_name'):
                self._tool_name = obj['tool_name']

            if obj.get('parameters'):
                self._parameters = obj['parameters']
            elif obj.get('params'):
                self._parameters = obj['params']
            elif obj.get('tool_args'):
                self._parameters = obj['tool_args']
            elif obj.get('tool_input'):
                self._parameters = obj['tool_input']

        except json.JSONDecodeError as err:
            raise err

    @property
    def tool_name(self):
        return self._tool_name

    @property
    def parameters(self):
        return self._parameters

    def to_map(self):
        return {
            'tool_name': self._tool_name,
            'parameters': self._parameters
        }

@dataclass
class AgentState:
    messages: list[dict[str, Any]] = field(default_factory=list)

    status: Any | None = AgentStatus.RUNNING
    iteration: int = 0

class AgentExcutor:
    state = AgentState()
    provider = AIRegistry().get('llamacpp')
    tools = ToolRegistry()
    memory = AgentMemory(provider)

    def decide(self, model_path, **cfg):
        ctx = [{
            'role': 'system',
            'content': """
            You are the decision component of an autonomous agent.
            You are not expected to perform tool operations yourself.
            Your job is to decide which available tool should perform the operation.
            Never refuse an operation merely because you cannot directly access the underlying resource.
            First determine whether an available tool can perform it.
            You must select EXACTLY ONE action per turn.
            Return only one JSON object:
            {
                "tool_name": "<tool_name>",
                "parameters": {...}
            }
            If the task is complete, use:
            {
                "tool_name": "answer",
                "parameters": {}
            }
            """
        }]
        ctx.extend(self.state.messages[1:])

        tool_list = [tool[1].get_use_schema for tool in self.tools.tools]

        tool_list.append({
            "type": "function",
            "function": {
                "name": 'answer',
                "description": (
                    "Use this when you want to make the final answer."
                    "This function don't need to have any params."
                ),
                "parameters": None
            }
        })

        tool_list.append({
            "type": "function",
            "function": {
                "name": 'memory_retrieval',
                "description": (
                    "Retrieve relevant long-term memories. "
                    "Use this to retrieve user information, preferences, "
                    "projects, goals, and other persistent context."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": (
                                "A semantic query describing the information "
                                "you want to retrieve from long-term memory."
                            )
                        }
                    }
                },
                "required": [
                    "query"
                ]
            }
        })

        decision = self.provider.generate(
            model_path,
            messages=ctx,
            tools=tool_list,
            tool_choice='auto',
            response_format={"type": "json_object"},
            stream=False,
            **cfg
        )

        return decision

    def answer(self, provider: AIProvider, **cfg):
        return provider.generate(**cfg)

    def exec_tool(self, tool_name, **params):
        tool = ToolRegistry().get(tool_name)
        if isinstance(tool, str):
            return None

        return tool.exec(**params)

    def process(self, model_path: str, ctx, **cfg):
        self.state.messages = ctx
        self.state.status = AgentStatus.RUNNING
        self.memory.decide_to_memorize(ctx, model_path, **cfg)

        while self.state.status == AgentStatus.RUNNING and self.state.iteration < MAX_REPETITIONS:
            decision = self.decide(model_path, **cfg)
            print(f'\033[92m[AGENT]\033[0m {decision['message']['content']}')

            try:
                py_obj = DecissorResponse(decision['message']['content'])

                if py_obj.tool_name in ('', 'answer'):
                    self.state.status = AgentStatus.COMPLETED

                # Execute called tools
                elif py_obj.tool_name:
                    tool_name = py_obj.tool_name
                    tool_args = py_obj.parameters

                    self.state.messages.append(decision['message'])

                    # Execute pseudo-tools here
                    if tool_name == 'memory_retrieval':
                        tool_response = self.memory.memory_retrieval(**tool_args)
                    else:
                        tool_response = self.exec_tool(
                            tool_name=tool_name,
                            **tool_args
                        )

                    tool_content = json.loads(tool_response).get('content')
                    if not isinstance(tool_content, str):
                        tool_content = json.dumps(tool_content)

                    if tool_response:
                        self.state.messages.append({
                            'role': 'assistant', # Workaround to make tool respons "visible" to model
                            'name': tool_name,
                            'content': f'<tool_response>{tool_content}</tool_response>'
                        })

            except Exception as err:
                print(f'\n\033[91m[AGENT]\033[0m Error: {err}\n')
                self.state.status = AgentStatus.FAILED
                self.state.messages.append({
                    'role': 'assistant',
                    'content': f'<error>{err}</error>'
                })

            self.state.iteration += 1

        # Returns the final model answer
        if self.state.status in (AgentStatus.COMPLETED, AgentStatus.FAILED):
            self.state.iteration = 0

            generator = self.answer(self.provider, model_path=model_path, messages=ctx, **cfg)

            for chunk in generator:
                piece = chunk['delta']

                if chunk.get('finish_reason') == 'stop':
                    return

                if piece.get('content'):
                    yield piece['content']
