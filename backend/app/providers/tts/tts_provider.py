from os import path, makedirs
from typing import Any
from time import perf_counter
import soundfile as sf
import io
import re
import numpy as np
from abc import ABC, abstractmethod
from dataclasses import dataclass
from kittentts import KittenTTS
from config import MODELS_PATH, check_cfg_file

def markdown_to_tts(text: str) -> str:
    # Code blocks
    text = re.sub(r"```(?:\w+)?\n?(.*?)```", r"\1", text, flags=re.DOTALL)

    # Inline code
    text = re.sub(r"`([^`]+)`", r"\1", text)

    # Headers
    text = re.sub(r"^\s*#{1,6}\s*", "", text, flags=re.MULTILINE)

    # Bold / italic / strikethrough
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"__(.*?)__", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"_(.*?)_", r"\1", text)
    text = re.sub(r"~~(.*?)~~", r"\1", text)

    # Links: [texto](url) -> texto
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

    # Images: ![alt](url) -> alt
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)

    # Unordered lists
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)

    # Ordered lists
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)

    # Blockquotes
    text = re.sub(r"^\s*>\s?", "", text, flags=re.MULTILINE)

    # Horizontal rules
    text = re.sub(r"^\s*([-*_]){3,}\s*$", "", text, flags=re.MULTILINE)

    # Remove leftover emphasis markers
    text = text.replace("*", "")
    
    # Normalize whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()

def pcm_2_wav(audio: np.ndarray, samplerate: int = 24000) -> bytes:
    buffer = io.BytesIO()
    
    sf.write(buffer, audio, samplerate, format='WAV')

    return buffer.getvalue()

@dataclass
class TTSResponse:
    metadata: dict | None = None
    samplerate: int = 24000
    audio: Any = None

class TTSProvider(ABC):
    @property
    def name(self):
        ...

    @property
    def models(self):
        ...

    @abstractmethod
    def synthesize(self, **kwargs) -> TTSResponse:
        ...

class TTSRegistry:
    _instance = None
    _providers = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def register(self, provider: TTSProvider):
        self._providers[provider.name] = provider

    @property
    def providers(self):
        return self._providers.keys()

    def get(self, provider_name: str) -> TTSProvider:
        return self._providers[provider_name]

class KittenttsProvider(TTSProvider):
    _instance = None
    _model = None
    _cache_path = ''

    def __new__(cls):
        cls._cache_path = path.join(
            MODELS_PATH,
            'TTS', 'Kitten'
        )

        if not path.exists(cls._cache_path):
            makedirs(cls._cache_path, exist_ok=True)

        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    @property
    def name(self):
        return "kitten"

    @property
    def models(self):
        return [
            'kitten-tts-mini-0.8',
            'kitten-tts-micro-0.8',
            'kitten-tts-nano-0.8',
            'kitten-tts-nano-0.8-int8'
        ]

    def get_voices(self, model_name: str):
        if self._model is None:
            self._model = KittenTTS(
                f"KittenML/{model_name if model_name not in ('', None) else self.models[1]}",
                cache_dir=self._cache_path
            )

        return self._model.available_voices

    def synthesize(self, **kwargs) -> TTSResponse:
        t_init = perf_counter()
        model = KittenTTS(
            f"KittenML/{kwargs.get('tts_model', self.models[0])}",
            cache_dir=self._cache_path
        )

        audio_pcm = model.generate(
            kwargs.get('text', ''),
            voice=kwargs.get('voice', 'Rosie'),
            speed=kwargs.get('speed', 1.0),
            clean_text=True
        )

        audio = pcm_2_wav(audio_pcm)

        return TTSResponse(
            metadata={'latency': perf_counter() - t_init},
            audio=audio
        )
