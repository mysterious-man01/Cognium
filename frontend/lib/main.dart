import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'package:frontend/proxy_page.dart';
import 'package:frontend/chat_controller.dart';

void main() {
  runApp(MultiProvider(
    providers: [
      ChangeNotifierProvider(
        create: (context) => ChatController(),
      ),
    ],
    child: const MainApp()
  ));
}

class MainApp extends StatelessWidget {
  const MainApp({super.key});

  @override
  Widget build(BuildContext context) {
    return const MaterialApp(
      home: ProxyPage()
    );
  }
}
