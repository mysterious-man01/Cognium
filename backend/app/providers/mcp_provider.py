import os
import json
import time

from mcp import Client, StdioServerParameters
from mcp.client.stdio import stdio_client

from config import PATH

class MCPClientProvider:
    def __init__(self, name: str, command: str, server_script: str):
        self._tools = None
        self._server_params = StdioServerParameters(
            command=command,
            args=[server_script],
        )
        self._server_name = name

    async def initialize(self):
        async with Client(stdio_client(self._server_params)) as client:
            self._tools = await client.list_tools()

    @property
    def server_name(self) -> str:
        return self._server_name

    @property
    def tools(self):
        if self._tools is None:
            return None

        return [
            f'{self._server_name}_{tool.name}'
            for tool in self._tools.tools
        ]

    @property
    def get_use_schema(self) -> list[dict]:
        if self._tools is None:
            return []

        return [
            {
                'type': 'function',
                'function': {
                    'name': f'{self._server_name}_{tool.name}',
                    'description': tool.description,
                    'parameters': {
                        'type': tool.input_schema['type'],
                        'properties': tool.input_schema['properties']
                    }
                }
            } for tool in self._tools.tools
        ]

    async def call_tool(self, tool_name: str, tool_args: dict):
        t_init = time.perf_counter()

        if f'{self._server_name}_' in tool_name:
            real_name = tool_name.replace(f'{self._server_name}_', '')
        else:
            real_name = tool_name

        async with Client(self._server_params) as client:
            response = await client.call_tool(real_name, tool_args)

        return json.dumps({
            'metadata': {
                'latency': time.perf_counter() - t_init
            },
            'content': response.structured_content.get('result')
        })

class MCPClientRegistry:
    _instance = None
    _providers = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def register(self, provider: MCPClientProvider) -> None:
        self._providers.append(provider)

    @property
    def providers(self) -> list[MCPClientProvider]:
        return self._providers

    async def warmup(self) -> None:
        config_path = os.path.join(
            PATH[0] if PATH[0] else PATH[1],
            "Config",
            "mcp_config.json",
        )

        os.makedirs(os.path.dirname(config_path), exist_ok=True)

        if not os.path.exists(config_path):
            with open(config_path, "w", encoding="utf-8") as file:
                json.dump({"mcpServers": []}, file, indent=4)

        with open(config_path, "r", encoding="utf-8") as file:
            try:
                config = json.load(file)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid MCP configuration: {config_path}"
                ) from exc

        servers = config.get("mcpServers", [])

        if not isinstance(servers, list):
            raise ValueError("'mcpServers' must be a list")

        new_providers = []

        for server in servers:
            if not isinstance(server, dict) or len(server) != 1:
                continue

            server_name, settings = next(iter(server.items()))

            if not isinstance(settings, dict):
                continue

            command = settings.get("command")
            script = settings.get("script")

            if not command or not script:
                continue

            provider = MCPClientProvider(
                name=server_name,
                command=command,
                server_script=script,
            )

            await provider.initialize()
            new_providers.append(provider)

        self._providers = new_providers
