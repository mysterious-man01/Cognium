import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'package:frontend/config.dart';
import 'package:frontend/services.dart';

class ConfigPage extends StatefulWidget {
  const ConfigPage({super.key});

  @override
  State<ConfigPage> createState() => _ConfigPageState();
}

class _ConfigPageState extends State<ConfigPage> {
  ConfigParams config = ConfigParams(
    sysPrt:
        'You are an Artificial inteligence assistant built to answer in the question`s language.',
    temp: 0.8,
    maxTokens: -1,
    topK: 40,
    topP: 0.95,
    minP: 0.05,
  );

  @override
  void initState() {
    super.initState();

    initConfig();
  }

  void initConfig() async {
    try {
      final fetchedCfg = await fetchData('/config', 'GET') as Map;

      if (!fetchedCfg.containsKey('detail')) {
        config.sysPrt = fetchedCfg['sys_prt'];
        config.temp = fetchedCfg['temp'];
        config.maxTokens = fetchedCfg['max_tokens'];
        config.topK = fetchedCfg['top_k'];
        config.topP = fetchedCfg['top_p'];
        config.minP = fetchedCfg['min_p'];

        setState(() {});
      }
    } catch (e) {
      print('ConfigPage -> initConfig: Error: $e');
    }
  }

  void saveCfg() async {
    try {
      await fetchData('/config', 'POST', data: config.toJson()) as Map;
    } catch (e) {
      print('ConfigPage -> saveCfg: Error: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        Form(
          key: ValueKey(config.hashCode),
          child: ListView(
            children: [
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
