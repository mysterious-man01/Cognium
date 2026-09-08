from typing import override
import os
import base64
from providers.ai_provider import AIProvider
from llama_cpp import Llama
import llama_cpp.llama_chat_format as lcf
from database import get_document_by_name

class LlamacppProvider(AIProvider):
    _instance = None
    _suports = ['text', 'tokenize']

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            return cls._instance

        return cls._instance

    def _load_mmproj(self):
        model_dir = os.path.dirname(self._model_path)

        for file_name in os.listdir(model_dir):
            if 'mmproj' in file_name:
                return os.path.join(model_dir, file_name)

        return None

    def _load_chat_handler(self):
        model_path = self._model_path.lower()
        mmproj_path = self._load_mmproj()
        if not mmproj_path:
            return None

        self._suports.append('vision')

        if 'qwen2.5-vl' in model_path:
            return lcf.Qwen25VLChatHandler(
                clip_model_path=mmproj_path
            )
        elif 'llava-v1.5' in model_path:
            return lcf.Llava15ChatHandler(
                clip_model_path=mmproj_path
            )
        elif 'llava-v1.6' in model_path:
            return lcf.Llava16ChatHandler(
                clip_model_path=mmproj_path
            )
        elif 'moondream2' in model_path:
            return lcf.MoondreamChatHandler(
                clip_model_path=mmproj_path
            )
        elif 'nanollava' in model_path:
            return lcf.NanoLlavaChatHandler(
                clip_model_path=mmproj_path
            )
        elif 'llama-3-vision-alpha' in model_path:
            return lcf.Llama3VisionAlphaChatHandler(
                clip_model_path=mmproj_path
            )
        elif 'minicpm-v-2.6' in model_path:
            return lcf.MiniCPMv26ChatHandler(
                clip_model_path=mmproj_path
            )
        elif 'gemma-4' in model_path:
            return lcf.Gemma4ChatHandler(
                clip_model_path=mmproj_path
            )

    @override
    def _load(self, **config):
        chat_handler = self._load_chat_handler()

        self._model = Llama(
            model_path=self._model_path,
            chat_handler=chat_handler,
            chat_format=None,
            verbose=False,
            n_gpu_layers=-1, #config.get('n_gpu_layers', 99),
            flash_attn=config.get('flash_attn', False),
            n_ctx=config.get('n_ctx', 8192)
        )

    def format_ctx(self, ctx):
        messages = []

        if 'vision' in self._suports:
            for msg in ctx:
                if isinstance(msg['content'], list):
                    continue

                message = {
                    'role': msg['role'],
                    'content': []
                }
                atts = msg.get('attachments', [])

                att_str = ''
                for att_name in atts:
                    extension = att_name.split('.')[-1].lower()
                    if extension in ('jpeg', 'jpg', 'png', 'mp4'):
                        att = get_document_by_name(att_name)
                        if att:
                            message['content'].append({
                                'type': 'image_url',
                                'image_url': {'url': self._convert_img_2_base64(att['uri'])}
                            })
                    else:
                        att_str += f'<attachment>{att_name}</attachment>\n'

                message['content'].append({
                    'type': 'text',
                    'text': att_str + msg['content']
                })

                messages.append(message)
        else:
            for msg in ctx:
                atts = msg.get('attachments', [])
                att_str = ''
                if len(atts) > 0:
                    att_str = "<attachment>\n"
                    att_str += '\n'.join(atts)
                    att_str += "</attachment>\n"

                messages.append({
                    'role': msg['role'],
                    'content': att_str + msg['content']
                })

        return messages

    def _convert_img_2_base64(self, img_path: str):
        with open(img_path, 'rb') as img:
            b64_data = base64.b64encode(img.read()).decode('utf-8')
            return f'data:image/{img_path.split('.')[-1]};base64,{b64_data}'

    @property
    def name(self):
        return 'llamacpp'

    def tokenize(self, data: str):
        if not self._model_path:
            raise RuntimeError("Model not loaded")

        if not self._model:
            self.load_model(self._model_path)

        return self._model.tokenize(text=data.encode())

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

        messages = self.format_ctx(config.get('messages', []))

        streaming = config.get('stream', True)

        response = self._model.create_chat_completion(
            messages=messages,
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
