class ConfigParams {
  String sysPrt;
  String llmModel;
  String embdModel;
  String diffusionModel;
  double temp;
  int maxTokens;
  int topK;
  double topP;
  double minP;

  ConfigParams({
    required this.sysPrt,
    required this.llmModel,
    required this.embdModel,
    required this.diffusionModel,
    required this.temp,
    required this.maxTokens,
    required this.topK,
    required this.topP,
    required this.minP,
  });

  Map<String, dynamic> toJson() {
    return {
      'sys_prt': sysPrt,
      'llm_model': llmModel,
      'embedding_model': embdModel,
      'diffusion_model': diffusionModel,
      'temp': temp,
      'max_tokens': maxTokens,
      'top_k': topK,
      'top_p': topP,
      'min_p': minP,
    };
  }
}
