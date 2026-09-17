import json
from os import path, listdir
import database as db
from config import MODELS_PATH, PLATFORM_SLASH, check_cfg_file
from providers import AIProvider, AIRegistry

GREEN = '\033[92m'
DEFAULT = '\033[0m'

class AgentMemory:
    _provider = None
    _embedder = None
    _emb_model_path = ''

    def __init__(self, provider: AIProvider):
        self._provider = provider
        self._embedder = AIRegistry().get('embedding')
        from_cfg_file = check_cfg_file()

        if from_cfg_file.get('embedding_model'):
            self._emb_model_path = path.join(
                MODELS_PATH,
                'Embedding',
                from_cfg_file['embedding_model']
            )

            for file in listdir(self._emb_model_path):
                name = file.lower()

                if name.endswith('.gguf') and 'embedding' in name:
                    self._emb_model_path = path.join(self._emb_model_path, file)
                    break
        else:
            self._emb_model_path = AIRegistry().get('llamacpp').instance().get_model_path()

    def decide_to_memorize(self, messages, model_path, **cfg):
        ctx = [{
            'role': 'system',
            'content': """
            You are the memory decision component of an autonomous agent.
            Your job is to determine whether the conversation contains information
            that is useful to remember in future conversations.

            Only memorize information that is:
            - relevant beyond the current conversation;
            - useful for understanding the user, their preferences, projects,
            goals, knowledge, or recurring behavior;
            - sufficiently explicit and reliable.

            Do NOT memorize:
            - casual conversation;
            - temporary information;
            - greetings or acknowledgements;
            - information that is only relevant to the current task;
            - guesses or assumptions about the user.

            If there is information worth remembering, transform it into a concise,
            self-contained atomic memory that can be understood without the original conversation.
            You must select EXACTLY ONE action.
            Return only one JSON object:
            {
                "memo": "<memory_string>"
            }
            If there is no information to memorize, use:
            {
                "memo": null
            }
            """
        }]
        ctx.extend(messages[1:])

        response = self._provider.generate(
            model_path,
            messages=ctx,
            response_format={"type": "json_object"},
            stream=False,
            **cfg
        )

        resp_obj = json.loads(response['message']['content'])

        if resp_obj.get('memo') is not None:
            used_model = path.dirname(self._emb_model_path).split(PLATFORM_SLASH)[-1]

            embed_query = self._embedder.generate(self._emb_model_path, text=resp_obj['memo'])

            # Search for similar memories
            mem_result = db.search_memory(embed_query, top_k=5)
            if mem_result:
                # Use LLM to compare memories and see if memory will be created, updated or ignored
                decision = self.compare_memories(
                    resp_obj['memo'],
                    mem_result,
                    model_path,
                    **cfg
                )

                json_obj = json.loads(decision)
                action = json_obj.get('action')
                content = json_obj.get('content')

                # Ignore possible memory
                if action.lower() == 'ignore':
                    return

                # Update an existing conflitant memory
                if action.lower() == 'update':
                    for m in content:
                        embedding = self._embedder.generate(
                            self._emb_model_path,
                            text=m['new_content']
                        )

                        modded = db.update_memory(
                            m['mem_id'],
                            content=m['new_content'],
                            embedding=embedding,
                            used_model=used_model
                        )

                        print(f'\n{GREEN}[MEMORY]{DEFAULT} MODIFIED: {modded}\n')

                # Create a new bach of memories
                if action.lower() == 'create':
                    for m in content:
                        embedding = self._embedder.generate(
                            self._emb_model_path,
                            text=m
                        )

                        saved = db.create_memory(
                            content=m,
                            embedding=embedding,
                            used_model=used_model
                        )

                        print(f'\n{GREEN}[MEMORY]{DEFAULT} CREATED: {saved}\n')
            else:
                # Create a new memory if there is no saved memory
                embedding = self._embedder.generate(
                    self._emb_model_path,
                    text=resp_obj['memo']
                )

                saved = db.create_memory(
                    content=resp_obj['memo'],
                    embedding=embedding,
                    used_model=used_model
                )

                print(f'\n{GREEN}[MEMORY]{DEFAULT} CREATED: {saved}\n')

    def compare_memories(self, new_mem: str, memories: list, model_path: str, **cfg):
        mem_content = [
            {
                "memo_id": mem['id'],
                "content": mem['content']
            } for mem in memories
        ]

        ctx = [{
            'role': 'system',
            'content': """
            Your job is to compare memories and find if a memory is conflitant with the new one.
            You will decide if a memory must be UPDATED, CREATED or IGNORED.
            Avoid redundant memories and normalize or decompose to be an atomic memory or batch of memories if necessary.
            If CREATE or UPDATE is chosen, certify that memory is auto-suficient and is not redundant compared
            with existing memories.
            Return ONLY valid JSON object:
            If update was chosen, use:
            {
                "action": "update",
                "content": [
                    {
                        "mem_id": "<memory_id>",
                        "new_content": "<new_memory>"
                    },
                    ...
                ]
            }
            If create is chosen, use:
            {
                "action": "create",
                "content": [
                    "<new_memory>",
                    ...
                ]
            }
            If memory is ignored, use:
            {
                "action": "ignore",
                "content": null
            }
            """
        }]

        ctx.append({
            "role": "user",
            "content": f"""
            <new_memory>{new_mem}</new_memory>
            <current_memories>
            {mem_content}
            </current_memories>
            """
        })

        decision = self._provider.generate(
            model_path,
            messages=ctx,
            response_format={'type': 'json_object'},
            stream=False,
            **cfg
        )

        return decision['message']['content']

    def memory_retrieval(self, query):

        embed_query = self._embedder.generate(self._emb_model_path, text=query)

        # Retrieve memories from db
        memories = db.search_memory(embed_query, top_k=5)

        return json.dumps({
            "metadata": {
                'query': query
            },
            "content": [
                {
                    "mem_id": mem['id'],
                    "text": mem['content']
                } for mem in memories
            ]
        })
