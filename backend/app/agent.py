from llama_cpp import Llama

class Engine:
    _instance = None
    _model_path = None
    _llm = None
    _sd = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def load_model(
        self,
        model_path,
        config,
        ctx=8192,
        use_gpu=True
    ):
        if self._model_path == model_path:
            return

        self._llm = Llama(
            model_path=model_path,
            n_ctx=ctx,
            n_gpu_layers=-1 if use_gpu else 0,
            flash_attn=True,
            verbose=False,
        )

        self._model_path = model_path

    def generate_txt(
        self,
        messages,
        model_path,
        config,
        stream=True
    ):
        self.load_model(model_path, config)

        yield from self._llm.create_chat_completion(
            messages=messages,
            max_tokens=config['max_tokens'],
            temperature=config['temp'],
            top_k=config['top_k'],
            top_p=config['top_p'],
            min_p=config['min_p'],
            stream=stream
        )

    def generete_img(self):
        raise NotImplementedError()
