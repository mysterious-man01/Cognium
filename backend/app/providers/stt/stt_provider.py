from abc import ABC, abstractmethod
import numpy as np
import os
import io
import wave
from pywhispercpp.model import Model
from config import MODELS_PATH, PLATFORM_SLASH

class STTProvider(ABC):
    @property
    def name(self):
        ...

    @abstractmethod
    def transcript(self, **kwargs):
        ...

class STTRegistry:
    _instance = None
    _providers = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def register(self, provider: STTProvider):
        self._providers[provider.name] = provider

    @property
    def providers(self):
        return self._providers.keys()

    def get(self, provider_name: str) -> STTProvider:
        return self._providers[provider_name]

class WhispercppProvider(STTProvider):
    _instance = None
    _model = None
    _model_path = ''
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def _get_model(self, model_name: str):
        stt_model_path = os.path.join(
            MODELS_PATH,
            'STT',
            'whisper.cpp',
            model_name
        )
        current_model = os.path.dirname(self._model_path)

        if not current_model or self._model is None or current_model != model_name:
            if not os.path.exists(stt_model_path):
                os.makedirs(stt_model_path, exist_ok=True)

            for file_name in os.listdir(stt_model_path):
                if file_name.endswith('.bin'):
                    self._model_path = os.path.join(
                        stt_model_path,
                        file_name
                    )
                    break

            self._model = Model(self._model_path)


    @property
    def name(self):
        return "whispercpp"

    def transcript(self, **kwargs):
        if self._model is None:
            self._get_model(kwargs.get('stt_model'))

        if kwargs.get('audio'):
            np_array = np.frombuffer(kwargs.get('audio'), dtype=np.int16)
            np_array = np_array.astype(np.float32) / 32768.0 # pywhispercpp uses float32

            segments = self._model.transcribe(
                np_array
            )

            text = ''
            for segment in segments:
                text += segment.text

            return text
