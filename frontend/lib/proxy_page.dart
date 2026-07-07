import 'package:flutter/material.dart';
import 'package:frontend/config_page.dart';
import 'package:provider/provider.dart';
import 'package:frontend/services.dart';
import 'package:frontend/chat_page.dart';
import 'package:frontend/chat_controller.dart';

enum Pages { chatPage, imagePage, configPage }

class ProxyPage extends StatefulWidget {
  const ProxyPage({super.key});

  @override
  State<ProxyPage> createState() => _ProxyPageState();
}

class _ProxyPageState extends State<ProxyPage> {
  final TextEditingController renameController = TextEditingController();
  Pages pageType = Pages.chatPage;

  @override
  void initState() {
    super.initState();
  }

  Future<void> deleteChat(int chatId) async {
    try {
      fetchData('/chat/$chatId', 'DELETE');
    } catch (e) {
      print('deleteChat error -> $e');
    }
  }

  Future<void> renameChat(int chatId, String title) async {
    try {
      fetchData('/chat/$chatId', 'PATCH', data: {'title': title});
    } catch (e) {
      print('renameChat error -> $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    final controller = Provider.of<ChatController>(context, listen: false);

    return Scaffold(
      appBar: AppBar(),
      drawer: Drawer(
        child: ListView(
          padding: EdgeInsets.zero,
          children: [
            ListTile(
              leading: const Icon(Icons.add_comment_outlined),
              title: const Text("New Chat"),
              onTap: () {
                setState(() {
                  pageType = Pages.chatPage;
                });

                controller.modifyIndex(0);
              },
            ),

            ListTile(
              leading: const Icon(Icons.image_outlined),
              title: const Text("Image"),
              onTap: () {
                setState(() {
                  pageType = Pages.imagePage;
                });

                showDialog(
                  context: context,
                  builder: (context) {
                    return AlertDialog(
                      title: const Text("Alert"),
                      content: const Text("Images button pressed"),
                      actions: [
                        TextButton(
                          style: ButtonStyle(),
                          onPressed: () => Navigator.of(context).pop(),
                          child: const Text("OK"),
                        ),
                      ],
                    );
                  },
                );
              },
            ),

            ListTile(
              leading: const Icon(Icons.settings_outlined),
              title: const Text("Config"),
              onTap: () {
                setState(() {
                  pageType = Pages.configPage;
                });
              },
            ),
            const SizedBox(height: 20),

            const Text('Recent chats'),
            const Divider(thickness: 1.5),
            const SizedBox(height: 10),

            // Add a way to update this
            Consumer<ChatController>(
              builder: (_, controller, child) {
                if (controller.chatList.isEmpty) {
                  return Padding(
                    padding: EdgeInsetsGeometry.directional(top: 5),
                    child: Center(child: const Text('No conversations yet')),
                  );
                }

                // Update when tap on other chats
                final List<Widget> widgetList = [];
                for (final item in controller.chatList) {
                  widgetList.add(
                    ListTile(
                      leading: item.isGenerating
                          ? SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : null,
                      title: Text(item.title ?? item.id.toString()),
                      onTap: () {
                        setState(() {
                          pageType = Pages.chatPage;
                        });

                        controller.modifyIndex(item.id!);
                      },
                      trailing: PopupMenuButton<String>(
                        icon: const Icon(Icons.more_vert),
                        itemBuilder: (context) => [
                          PopupMenuItem(
                            onTap: () {
                              showDialog(
                                context: context,
                                builder: (context) {
                                  return AlertDialog(
                                    title: const Text('Rename'),
                                    content: TextField(
                                      controller: renameController,
                                      onSubmitted: (value) {
                                        renameChat(item.id!, value.trim());

                                        final chat = controller.chatList
                                            .where((e) => e.id! == item.id!)
                                            .first;

                                        setState(() {
                                          chat.title = value;
                                        });

                                        Navigator.of(context).pop();
                                      },
                                    ),
                                    actions: [
                                      TextButton(
                                        onPressed: () {
                                          renameChat(
                                            item.id!,
                                            renameController.text.trim(),
                                          );

                                          final chat = controller.chatList
                                              .where((e) => e.id! == item.id!)
                                              .first;

                                          setState(() {
                                            chat.title = renameController.text
                                                .trim();
                                          });

                                          Navigator.of(context).pop();
                                        },
                                        child: const Text('Save'),
                                      ),
                                    ],
                                  );
                                },
                              );
                            },
                            child: const Text('Rename'),
                          ),

                          PopupMenuItem(
                            onTap: () {
                              deleteChat(item.id!);

                              final chat = controller.chatList
                                  .where((e) => e.id! == item.id!)
                                  .first;

                              setState(() {
                                controller.chatList.remove(chat);
                              });

                              if (item.id! == controller.chatIndex) {
                                controller.modifyIndex(0);
                              }
                            },
                            child: const Text('Delete'),
                          ),
                        ],
                      ),
                    ),
                  );
                }

                return Column(children: widgetList);
              },
            ),
          ],
        ),
      ),
      // Update when tap on other chats
      body: switch (pageType) {
        Pages.chatPage => Consumer<ChatController>(
          builder: (_, controller, child) {
            final id = controller.chatIndex;
            final chats = controller.chatList;
            final chat = chats.where((c) => c.id == id).firstOrNull;

            return ChatPage(chat: chat);
          },
        ),

        Pages.imagePage => const Center(child: Text('Image Page')),

        Pages.configPage => ConfigPage(),
      },
    );
  }
}
