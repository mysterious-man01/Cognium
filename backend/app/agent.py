import json
from providers import AIRegistry, AIProvider, ToolRegistry

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

class AgentExcutor:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def answer(self, provider: AIProvider, **cfg):
        return provider.generate(**cfg)

    def exec_tool(self, tool_name, **params):
        tool = ToolRegistry().get(tool_name)
        if isinstance(tool, str):
            return None

        return tool.exec(**params)

    # bad responses, low precission in tool response interpretation
    def process(self, model_path: str, ctx, **cfg):
        provider = AIRegistry().get('llamacpp')
        tools = ToolRegistry()

        decission = provider.generate(
            model_path,
            messages=ctx,
            tools=[
                tool[1].get_use_schema for tool in tools.tools
            ],
            tool_choice='auto',
            response_format={"type": "json_object"},
            stream=False,
            **cfg
        )

        try:
            py_obj = DecissorResponse(decission['message']['content'])

            # Execute called tools
            ctx.append(decission['message'])

            if py_obj.tool_name:
                tool_name = py_obj.tool_name
                tool_args = py_obj.parameters

                tool_response = self.exec_tool(
                    tool_name=tool_name,
                    **tool_args
                )

                if tool_response:
                    ctx.append({
                        'role': 'assistant', # Workaround to make tool respons "visible" to model
                        'name': tool_name,
                        'content': json.loads(tool_response).get('content')
                    })

        except Exception as err:
            raise err

        # Returns the final model answer
        generator = self.answer(provider, model_path=model_path, messages=ctx, **cfg)

        for chunk in generator:
            piece = chunk['delta']

            if chunk.get('finish_reason') == 'stop':
                return

            if piece.get('content'):
                yield piece['content']
