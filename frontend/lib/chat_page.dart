import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'package:frontend/chat_controller.dart';
import 'package:frontend/services.dart';
import 'package:frontend/objects.dart';
import 'package:frontend/websocket.dart';

class ChatPage extends StatefulWidget {
  final Chat? chat;

  const ChatPage({super.key, required this.chat});

  @override
  State<ChatPage> createState() => _ChatPageState();
}

class _ChatPageState extends State<ChatPage> {
  late WebSocket _socket;
  StreamSubscription? _socSub;
  final ScrollController _scrollController = ScrollController();
  final TextEditingController _textController = TextEditingController();
  late int chatId;
  List<Message> msgList = [];
  List<dynamic> modelsList = [];

  @override
  void initState() {
    super.initState();

    _socket = WebSocket();

    chatId = widget.chat?.id ?? 0;

    _getModels();

    if (chatId != 0) _getData();

    _addSub();
  }

  @override
  void didUpdateWidget(ChatPage oldWidget) {
    super.didUpdateWidget(oldWidget);

    if (oldWidget.chat?.id != widget.chat?.id) {
      msgList.clear();

      _getModels();

      chatId = widget.chat?.id ?? 0;

      msgList.clear();

      setState(() {});

      if (chatId != 0) _getData();
    }
  }

  @override
  void dispose() {
    _socSub?.cancel();
    _scrollController.dispose();
    _textController.dispose();

    super.dispose();
  }

  void _addSub() {
    print('ADDING LISTENER');

    _socSub = _socket.events.listen(
      (raw) {
        final e = jsonDecode(raw);

        if (e.containsKey('id') &&
            e.containsKey('chat_id') &&
            e['chat_id'] == chatId &&
            e.containsKey('content')) {
          Message? message;

          try {
            message = msgList.where((x) => x.id == e['id']).first;
          } catch (_) {
            message = Message(
              id: e['id'],
              role: e['role'],
              content: e['content'],
              timestamp: e['timestamp'],
            );

            msgList.add(message);
          }

          message.content += e['content'];

          if (!mounted) return;

          setState(() {
            if (_isNearBottom()) {
              _scrollToBottom();
            }
          });
        }
      },
      onDone: () => print('STREAM CLOSED'),
      onError: (err) => print('STREAM ERROR: $err'),
    );
  }

  void _getModels() async {
    try {
      final result = await fetchData('/models', 'GET');

      if (result is Map && result.containsKey('models')) {
        modelsList = result['models'];
      }
    } catch (e) {
      print('error: ChatPage -> _getModels => $e');
    }
  }

  void _getData() async {
    try {
      final result = await fetchData('/chat/${widget.chat!.id}/message', 'GET');

      if (result is List) {
        for (final Map item in result) {
          if (item.containsKey('id') &&
              item.containsKey('role') &&
              item.containsKey('content') &&
              item.containsKey('timestamp')) {
            msgList.add(
              Message(
                id: item['id'],
                role: item['role'],
                content: item['content'],
                timestamp: item['timestamp'],
              ),
            );
          }
        }
        if (mounted) {
          setState(() {
            _scrollToBottom();
          });
        }
      }
    } catch (err) {
      print('Error: $err'); // Show it on UI
    }
  }

  bool _isNearBottom() {
    if (!_scrollController.hasClients) return true;

    final max = _scrollController.position.maxScrollExtent;
    final current = _scrollController.offset;

    return (max - current) < 200;
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scrollController.hasClients) return;

      _scrollController.jumpTo(_scrollController.position.maxScrollExtent);
    });
  }

  @override
  Widget build(BuildContext context) {
    final chatCtrl = Provider.of<ChatController>(context, listen: true);
    final isGenerating = widget.chat?.isGenerating ?? false;

    print('--- CHAT PAGE: Rebuilding.. Actual chat ID: $chatId ---');
    print('Models => $modelsList');

    return Column(
      children: [
        Expanded(
          child: ListView.builder(
            controller: _scrollController,
            itemCount: msgList.length,
            itemBuilder: (_, index) {
              final data = msgList[index];

              return Align(
                alignment: data.role == 'user'
                    ? Alignment.centerRight
                    : Alignment.center,
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    vertical: 8,
                    horizontal: 12,
                  ),
                  margin: const EdgeInsets.symmetric(vertical: 8),
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(12),
                    color: data.role == 'user'
                        ? Theme.of(context).colorScheme.secondary
                        : Theme.of(context).colorScheme.surface,
                  ),
                  child: Text(
                    data.content,
                    style: TextStyle(
                      color: data.role == 'user'
                          ? Theme.of(context).colorScheme.onSecondary
                          : Theme.of(context).colorScheme.onSurface,
                    ),
                  ),
                ),
              );
            },
          ),
        ),

        Align(
          alignment: Alignment.bottomCenter,
          child: Container(
            padding: const EdgeInsets.all(20),
            width: MediaQuery.of(context).size.width / 2,
            child: Column(
              children: [
                // Expanded(
                //   child:
                TextField(
                  controller: _textController,
                  keyboardType: TextInputType.multiline,
                  textInputAction: TextInputAction.newline,
                  enableInteractiveSelection: true,
                  minLines: 1,
                  maxLines: 10,
                  decoration: InputDecoration(labelText: "Type anything"),
                ),

                // ),
                Row(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    PopupMenuButton(
                      icon: const Icon(Icons.add),
                      itemBuilder: (context) => [
                        // Image selector
                        PopupMenuItem(
                          child: ListTile(
                            leading: const Icon(Icons.image),
                            title: const Text('Upload Image'),
                            subtitle: const Text('Not implemented yet'),
                            onTap: () {
                              null;
                            },
                          ),
                        ),

                        // Other buttons
                      ],
                    ),

                    const Spacer(),

                    // const SizedBox(width: 8),
                    PopupMenuButton(
                      child: Row(
                        children: [
                          const Icon(Icons.token),
                          Text(
                            chatCtrl.selectedModel == ''
                                ? 'Models'
                                : chatCtrl.selectedModel,
                          ),
                        ],
                      ),
                      itemBuilder: (context) => modelsList
                          .map(
                            (m) => PopupMenuItem(
                              child: Text(m),
                              onTap: () => chatCtrl.setSelectedModel(m),
                            ),
                          )
                          .toList(),
                    ),

                    isGenerating
                        ? IconButton(
                            icon: const CircularProgressIndicator(),
                            onPressed: null,
                            enableFeedback: false,
                          )
                        : IconButton(
                            icon: const Icon(Icons.send),
                            onPressed: () {
                              if (_textController.text.isEmpty || chatCtrl.selectedModel.isEmpty) return;

                              final msg = Message(
                                id: null,
                                role: 'user',
                                content: _textController.text.trim(),
                                timestamp: null,
                              );

                              setState(() {
                                msgList.add(msg);
                              });

                              final body = {
                                'model': chatCtrl.selectedModel,
                                'chat_id': chatId,
                                'content': _textController.text.trim(),
                              };

                              _textController.clear();

                              _socket.send(chatId, body);
                            },
                          ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}
