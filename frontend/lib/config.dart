class ConfigParams {
  String sysPrt;
  String embdModel;
  double temp;
  int maxTokens;
  int topK;
  double topP;
  double minP;

  ConfigParams({
    required this.sysPrt,
    required this.embdModel,
    required this.temp,
    required this.maxTokens,
    required this.topK,
    required this.topP,
    required this.minP,
  });

  Map<String, dynamic> toJson() {
    return {
      'sys_prt': sysPrt,
      'embedding_model': embdModel,
      'temp': temp,
      'max_tokens': maxTokens,
      'top_k': topK,
      'top_p': topP,
      'min_p': minP,
    };
  }
}
