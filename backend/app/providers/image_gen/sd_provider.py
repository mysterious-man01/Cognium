import os
from providers import AIProvider
from config import MODELS_PATH
from stable_diffusion_cpp import StableDiffusion
try:
    from typing import override
except ImportError:
    from typing_extensions import override

class SDCppProvider(AIProvider):
    _instance = None
    _suports = ['image']

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    @property
    def name(self):
        return 'sdcpp'

    @override
    def _load(self, **config):
        temp_path = os.path.join(
            MODELS_PATH,
            'Image',
            self._model_name
        )

        for file in os.listdir(temp_path):
            name = file.lower()

            if name.split('.')[-1] in ('gguf', 'safetensors', 'pt'):
                self._model_path = os.path.join(temp_path, file)
                break
        
        self._model = StableDiffusion(
            model_path=self._model_path,
            llm_path='',        # For future implementation
            llm_vision_path='', # For future implementation
            t5xxl_path='',      # For future implementation
            taesd_path='',      # For future implementation
            vae_path='',        # For future implementation
            lora_model_dir='',  # For future implementation
            wtype="default",
            verbose=False,
        )

    def _generation_status(self, step: int, steps: int, time: float):
        print(f'\033[92m[IMAGE GEN]\033[0m step {step} of {steps}')

    @override
    def generate(self, model_name: str, **config):
        self.load_model(model_name, **config)

        output = self._model.generate_image(
            progress_callback=self._generation_status,
            preview_interval=2,
            prompt=config.get('prompt'),
            negative_prompt=config.get('negative_prompt', ''),
            clip_skip=config.get('clip_skip', -1),
            init_image=None, # For future implementation
            ref_images=None, # For future implementation
            mask_image=None, # For future implementation
            width=config.get('width', 512),
            height=config.get('height', 512),
            cfg_scale=config.get('cfg_scale', 7.0),
            scheduler=config.get('scheduler', "default"),
            sample_method=config.get('sample_method', "default"),
            sample_steps=config.get('sample_steps', 20),
            strength=config.get('strength', 0.75),
            seed=config.get('seed', -1),
            batch_count=config.get('batch_count', 1),
            control_image=None, # For future implementation
            control_strength=config.get('control_strength', 0.9)
        )

        return output
