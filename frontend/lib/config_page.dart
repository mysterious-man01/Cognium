import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';

import 'package:frontend/config.dart';
import 'package:frontend/services.dart';
import 'package:frontend/chat_controller.dart';

class ConfigPage extends StatefulWidget {
  const ConfigPage({super.key});

  @override
  State<ConfigPage> createState() => _ConfigPageState();
}

class _ConfigPageState extends State<ConfigPage> {
  ConfigParams config = ConfigParams(
    sysPrt:
        'You are an Artificial inteligence assistant built to answer in the question`s language.',
    llmModel: '',
    embdModel: '',
    diffusionModel: '',
    temp: 0.8,
    maxTokens: -1,
    topK: 40,
    topP: 0.95,
    minP: 0.05,
    ttsModel: '',
    voice: '',
    ttsSpeed: 1.0,
  );

  final List<dynamic> llmModels = [];
  final List<dynamic> embdModels = [];
  final List<dynamic> diffusionModels = [];
  final List<dynamic> ttsModels = [];

  final List<dynamic> voices = [];

  @override
  void initState() {
    super.initState();

    initConfig();
    getLlmModels();
    getEmbdModels();
    getDiffusionModels();
    getTTSModels();
    getVoices();
  }

  Future<void> initConfig() async {
    try {
      final fetchedCfg = await fetchData('/config', 'GET') as Map;

      if (!fetchedCfg.containsKey('detail')) {
        config.sysPrt = fetchedCfg['sys_prt'];
        config.llmModel = fetchedCfg['llm_model'];
        config.embdModel = fetchedCfg['embedding_model'];
        config.diffusionModel = fetchedCfg['diffusion_model'];
        config.temp = fetchedCfg['temp'];
        config.maxTokens = fetchedCfg['max_tokens'];
        config.topK = fetchedCfg['top_k'];
        config.topP = fetchedCfg['top_p'];
        config.minP = fetchedCfg['min_p'];
        config.ttsModel = fetchedCfg['tts_model'];
        config.voice = fetchedCfg['voice'];
        config.ttsSpeed = fetchedCfg['tts_speed'];

        setState(() {});
      }
    } catch (e) {
      print('ConfigPage -> initConfig: Error: $e');
    }
  }

  Future<void> saveCfg() async {
    try {
      await fetchData('/config', 'POST', data: config.toJson()) as Map;
    } catch (e) {
      print('ConfigPage -> saveCfg: Error: $e');
    }
  }

  Future<void> getLlmModels() async {
    try {
      final result = await fetchData('/models/Text', 'GET');

      if (result is Map && result.containsKey('models')) {
        setState(() => llmModels.addAll(result['models']));
      }
    } catch (e) {
      print('error: ConfigPage -> getLlmModels => $e');
    }
  }

  Future<void> getEmbdModels() async {
    try {
      final result = await fetchData("/models/Embedding", 'GET');

      if (result is Map && result.containsKey('models')) {
        setState(() => embdModels.addAll(result['models']));
      }
    } catch (e) {
      print("error: ConfigPage -> getEmbdModels => $e");
    }
  }

  Future<void> getDiffusionModels() async {
    try {
      final result = await fetchData('/models/Image', 'GET');

      if (result is Map && result.containsKey('models')) {
        setState(() => diffusionModels.addAll(result['models']));
      }
    } catch (e) {
      print("error: ConfigPage -> getDiffusionModels => $e");
    }
  }

  Future<void> getTTSModels() async {
    try {
      final result = await fetchData('/tts/models', 'GET');

      if (result is Map && result.containsKey('models')) {
        setState(() => ttsModels.addAll(result['models']));
      }
    } catch (e) {
      print("error: ConfigPage -> getTTSMModels => $e");
    }
  }

  Future<void> getVoices() async {
    try {
      final result = await fetchData('/voices', 'GET');

      if (result is Map && result.containsKey('voices')) {
        setState(() => voices.addAll(result['voices']));
      }
    } catch (e) {
      print("Error: ConfigPage -> getVoices => $e");
    }
  }

  @override
  Widget build(BuildContext context) {
    final chatCtrl = Provider.of<ChatController>(context, listen: true);

    return Stack(
      children: [
        Form(
          key: ValueKey(config.hashCode),
          child: ListView(
            children: [
              // General configuration
              Padding(
                padding: const EdgeInsets.all(10.0),
                child: ExpansionTile(
                  title: const Text('General'),
                  children: [
                    Padding(
                      padding: EdgeInsets.all(5.0),
                      child: Card(
                        child: ListTile(
                          leading: Icon(
                            Icons.brightness_auto,
                          ), // Add light and night themes
                          title: const Text('Theme'),
                          trailing: MenuAnchor(
                            menuChildren: [
                              MenuItemButton(
                                child: const Text('System'),
                                onPressed: () {
                                  setState(() {
                                    null;
                                  });
                                },
                              ),

                              MenuItemButton(
                                child: const Text('Dark'),
                                onPressed: () {
                                  setState(() {
                                    null;
                                  });
                                },
                              ),

                              MenuItemButton(
                                child: const Text('Light'),
                                onPressed: () {
                                  setState(() {
                                    null;
                                  });
                                },
                              ),
                            ],
                            builder:
                                (
                                  BuildContext context,
                                  MenuController controller,
                                  Widget? child,
                                ) {
                                  return TextButton(
                                    onPressed: () {
                                      if (controller.isOpen) {
                                        controller.close();
                                      } else {
                                        controller.open();
                                      }
                                    },
                                    child: Text('System'),
                                  );
                                },
                          ),
                        ),
                      ),
                    ),

                    Padding(
                      padding: const EdgeInsets.all(5.0),
                      child: Column(
                        children: [
                          const Text('System prompt'),

                          Card(
                            child: TextFormField(
                              maxLines: 5,
                              initialValue: config.sysPrt.trim(),
                              onChanged: (v) => config.sysPrt = v,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),

              // Models configuration
              Padding(
                padding: EdgeInsets.all(10),
                child: ExpansionTile(
                  title: const Text("Models configuration"),
                  children: [
                    Padding(
                      padding: const EdgeInsets.all(8.0),
                      child: Card(
                        child: ListTile(
                          leading: const Icon(Icons.chat),
                          title: const Text("LLM model"),
                          trailing: PopupMenuButton(
                            child: Text(
                              config.llmModel != '' ? config.llmModel : "None",
                            ),
                            itemBuilder: (context) => llmModels
                                .map(
                                  (m) => PopupMenuItem(
                                    child: Text(m),
                                    onTap: () => setState(() {
                                      config.llmModel = m;
                                      chatCtrl.setSelectedModel(m);
                                    }),
                                  ),
                                )
                                .toList(),
                          ),
                        ),
                      ),
                    ),

                    Padding(
                      padding: const EdgeInsets.all(8.0),
                      child: Card(
                        child: ListTile(
                          leading: const Icon(Icons.scatter_plot),
                          title: const Text("Embedding model"),
                          trailing: PopupMenuButton(
                            child: Text(
                              config.embdModel != ''
                                  ? config.embdModel
                                  : "None",
                            ),
                            itemBuilder: (context) => embdModels
                                .map(
                                  (m) => PopupMenuItem(
                                    child: Text(m),
                                    onTap: () =>
                                        setState(() => config.embdModel = m),
                                  ),
                                )
                                .toList(),
                          ),
                        ),
                      ),
                    ),

                    Padding(
                      padding: const EdgeInsets.all(8.0),
                      child: Card(
                        child: ListTile(
                          leading: const Icon(Icons.gradient),
                          title: const Text("Diffusion model"),
                          trailing: PopupMenuButton(
                            child: Text(
                              config.diffusionModel != ''
                                  ? config.diffusionModel
                                  : 'None',
                            ),
                            itemBuilder: (context) => diffusionModels
                                .map(
                                  (m) => PopupMenuItem(
                                    child: Text(m),
                                    onTap: () => setState(
                                      () => config.diffusionModel = m,
                                    ),
                                  ),
                                )
                                .toList(),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),

              // Sampling configuration
              Padding(
                padding: const EdgeInsets.all(10.0),
                child: ExpansionTile(
                  title: const Text('Sampling'),
                  children: [
                    Padding(
                      padding: const EdgeInsets.all(8.0),
                      child: Column(
                        children: [
                          const Text('Temperature'),

                          TextFormField(
                            maxLength: 4,
                            keyboardType: TextInputType.number,
                            inputFormatters: [
                              FilteringTextInputFormatter.allow(
                                RegExp(r'^\d*\.?\d*'),
                              ),
                            ],
                            initialValue: config.temp.toString(),
                            onChanged: (v) {
                              config.temp = double.tryParse(v) ?? config.temp;
                            },
                          ),
                        ],
                      ),
                    ),

                    Padding(
                      padding: const EdgeInsets.all(8.0),
                      child: Column(
                        children: [
                          const Text('Max tokens'),

                          TextFormField(
                            maxLength: 5,
                            keyboardType: TextInputType.number,
                            inputFormatters: [
                              FilteringTextInputFormatter.allow(
                                RegExp(r'^[+-]?\d*'),
                              ),
                            ],
                            initialValue: config.maxTokens.toString(),
                            onChanged: (v) {
                              config.maxTokens =
                                  int.tryParse(v) ?? config.maxTokens;
                            },
                          ),
                        ],
                      ),
                    ),

                    Padding(
                      padding: const EdgeInsets.all(8.0),
                      child: Column(
                        children: [
                          const Text('Top K'),

                          TextFormField(
                            maxLength: 3,
                            keyboardType: TextInputType.number,
                            inputFormatters: [
                              FilteringTextInputFormatter.digitsOnly,
                            ],
                            initialValue: config.topK.toString(),
                            onChanged: (v) {
                              config.topK = int.tryParse(v) ?? config.topK;
                            },
                          ),
                        ],
                      ),
                    ),

                    Padding(
                      padding: const EdgeInsets.all(8.0),
                      child: Column(
                        children: [
                          const Text('Top P'),

                          TextFormField(
                            maxLength: 4,
                            keyboardType: TextInputType.number,
                            inputFormatters: [
                              FilteringTextInputFormatter.allow(
                                RegExp(r'^\d*\.?\d*'),
                              ),
                            ],
                            initialValue: config.topP.toString(),
                            onChanged: (v) {
                              config.topP = double.tryParse(v) ?? config.topP;
                            },
                          ),
                        ],
                      ),
                    ),

                    Padding(
                      padding: const EdgeInsets.all(8.0),
                      child: Column(
                        children: [
                          const Text('Min P'),

                          TextFormField(
                            maxLength: 4,
                            keyboardType: TextInputType.number,
                            inputFormatters: [
                              FilteringTextInputFormatter.allow(
                                RegExp(r'^\d*\.?\d*'),
                              ),
                            ],
                            initialValue: config.minP.toString(),
                            onChanged: (v) {
                              config.minP = double.tryParse(v) ?? config.minP;
                            },
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),

              // TTS configuration
              Padding(
                padding: const EdgeInsets.all(10),
                child: ExpansionTile(
                  title: const Text("TTS"),
                  children: [
                    Padding(
                      padding: EdgeInsets.all(8.0),
                      child: Card(
                        child: ListTile(
                          leading: const Icon(Icons.graphic_eq),
                          title: const Text('TTS Model'),
                          trailing: PopupMenuButton(
                            child: Text(
                              config.ttsModel != ''
                                  ? config.ttsModel
                                  : (ttsModels.firstOrNull ?? 'None'),
                            ),
                            itemBuilder: (context) => ttsModels
                                .map(
                                  (m) => PopupMenuItem(
                                    child: Text(m),
                                    onTap: () =>
                                        setState(() => config.ttsModel = m),
                                  ),
                                )
                                .toList(),
                          ),
                        ),
                      ),
                    ),

                    Padding(
                      padding: EdgeInsets.all(8.0),
                      child: Card(
                        child: ListTile(
                          leading: const Icon(Icons.record_voice_over),
                          title: const Text('Voice'),
                          trailing: PopupMenuButton(
                            child: Text(
                              config.voice != '' ? config.voice : 'Default',
                            ),
                            itemBuilder: (context) => voices
                                .map(
                                  (v) => PopupMenuItem(
                                    child: Text(v),
                                    onTap: () =>
                                        setState(() => config.voice = v),
                                  ),
                                )
                                .toList(),
                          ),
                        ),
                      ),
                    ),

                    Padding(
                      padding: EdgeInsets.all(8.0),
                      child: Column(
                        children: [
                          const Text('Voice speed'),

                          Slider(
                            min: 0.5,
                            max: 2.0,
                            divisions: 15,
                            value: config.ttsSpeed,
                            label: "${config.ttsSpeed.toStringAsFixed(1)}x",
                            onChanged: (value) {
                              setState(() {
                                config.ttsSpeed = value;
                              });
                            },
                          ),

                          Text(
                            'Controls the speed of generated audio',
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),

              SizedBox(height: 40),
            ],
          ),
        ),

        Padding(
          padding: const EdgeInsets.all(10.0),
          child: Align(
            alignment: Alignment.bottomRight,
            child: TextButton(
              child: const Text('Save Settings'),
              onPressed: () {
                saveCfg();
              },
            ),
          ),
        ),
      ],
    );
  }
}
