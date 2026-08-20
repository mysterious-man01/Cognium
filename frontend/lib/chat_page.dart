import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:frontend/widgets/attachment_card.dart';
import 'package:provider/provider.dart';
import 'package:flutter_markdown_plus/flutter_markdown_plus.dart';
import 'package:file_picker/file_picker.dart';

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
  final List<Message> msgList = [];
  final List<dynamic> modelsList = [];
  final List<AttachmentLocal> attachments = [];

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
      modelsList.clear();

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
    _socSub = _socket.events.listen(
      (raw) {
        final e = jsonDecode(raw);

        if (e.containsKey('id') &&
            e.containsKey('chat_id') &&
            e['chat_id'] == chatId) {
          if (e.containsKey('content')) {
            Message? message;

            for (final m in msgList) {
              if (m.id == e['id']) {
                message = m;
                break;
              }
            }

            if (message == null) {
              message = message = Message(
                id: e['id'],
                role: e['role'],
                content: '',
                attachments: null,
                metrics: null,
                timestamp: e['timestamp'],
              );

              msgList.add(message);
            }

            message.content += e['content'];
            message.metrics = e['metrics'];

            if (!mounted) return;

            setState(() {
              if (_isNearBottom()) {
                _scrollToBottom();
              }
            });
          }

          if (e.containsKey('metrics')) {
            final message = msgList.last;

            setState(() {
              message.metrics = e['metrics'];
            });
          }
        }
      },
      onDone: () => print('STREAM CLOSED'),
      onError: (err) => print('STREAM ERROR: $err'),
    );
  }

  void _getModels() async {
    try {
      final result = await fetchData('/models/Text', 'GET');

      if (result is Map && result.containsKey('models')) {
        modelsList.addAll(result['models']);
      }
    } catch (e) {
      print('error: ChatPage -> _getModels => $e');
    }
  }

  void _getData() async {
    try {
      final resultMsg = await fetchData(
        '/chat/${widget.chat!.id}/message',
        'GET',
      );

      if (resultMsg is List) {
        for (final Map item in resultMsg) {
          if (item.containsKey('id') &&
              item.containsKey('role') &&
              item.containsKey('content') &&
              item.containsKey('attachments') &&
              item.containsKey('timestamp')) {
            msgList.add(
              Message(
                id: item['id'],
                role: item['role'],
                content: item['content'],
                attachments: (item['attachments'] as List<dynamic>?)
                    ?.map(
                      (e) => AttachmentRemote(
                        id: e['id'],
                        name: e['name'],
                        size: e['size'],
                        data: null,
                      ),
                    )
                    .toList(growable: false),
                metrics: null,
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

  Future<void> pickFiles() async {
    FilePickerResult? result = await FilePicker.pickFiles(
      allowMultiple: true,
      withData: true,
      withReadStream: true,
    );

    if (result != null) {
      final List<AttachmentLocal> files = [];
      for (final file in result.files) {
        files.add(AttachmentLocal(file: file));
      }

      setState(() {
        attachments.addAll(files);
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final chatCtrl = Provider.of<ChatController>(context, listen: true);
    final isGenerating = widget.chat?.isGenerating ?? false;

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
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      if (data.attachments != null)
                        Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            for (final att in data.attachments!)
                              AttachmentCard(file: att, onRemove: null),
                          ],
                        ),

                      MarkdownBody(
                        data: data.content,
                        selectable: true,
                        styleSheet:
                            MarkdownStyleSheet.fromTheme(
                              Theme.of(context),
                            ).copyWith(
                              p: TextStyle(
                                color: data.role == 'user'
                                    ? Theme.of(context).colorScheme.onSecondary
                                    : Theme.of(context).colorScheme.onSurface,
                              ),
                            ),
                        onTapLink: (text, href, title) {
                          null;
                        },
                      ),

                      if (data.role != 'user' && data.metrics != null)
                        Padding(
                          padding: const EdgeInsets.only(top: 8),
                          child: Text(
                            "Generated ${data.metrics!['generated']} tokens • "
                            "${data.metrics!['time']} s • "
                            "${data.metrics!['tps']} t/s",
                            style: Theme.of(context).textTheme.bodySmall,
                            textAlign: TextAlign.center,
                          ),
                        ),
                    ],
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
                if (attachments.isNotEmpty)
                  SizedBox(
                    height: 80,
                    child: ListView.builder(
                      scrollDirection: Axis.horizontal,
                      itemCount: attachments.length,
                      itemBuilder: (_, index) {
                        final file = attachments[index];

                        return AttachmentCard(
                          file: file,
                          onRemove: () {
                            fetchData(
                              '/uploads',
                              'DELETE',
                              data: {'file_name': attachments[index].name},
                            );

                            setState(() => attachments.removeAt(index));
                          },
                        );
                      },
                    ),
                  ),

                TextField(
                  controller: _textController,
                  keyboardType: TextInputType.multiline,
                  textInputAction: TextInputAction.newline,
                  enableInteractiveSelection: true,
                  minLines: 1,
                  maxLines: 10,
                  decoration: InputDecoration(labelText: "Type anything"),
                ),

                Row(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    PopupMenuButton(
                      icon: const Icon(Icons.add),
                      itemBuilder: (context) => [
                        PopupMenuItem(
                          child: ListTile(
                            leading: const Icon(Icons.attach_file),
                            title: const Text('Attach File'),
                            onTap: () async {
                              await pickFiles();
                              uploadFile(attachments);
                            },
                          ),
                        ),

                        // Other buttons
                      ],
                    ),

                    const Spacer(),

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
                              if (_textController.text.isEmpty ||
                                  chatCtrl.selectedModel.isEmpty)
                                return;

                              final msg = Message(
                                id: null,
                                role: 'user',
                                content: _textController.text.trim(),
                                attachments: attachments.toList(
                                  growable: false,
                                ),
                                metrics: null,
                                timestamp: null,
                              );

                              setState(() {
                                msgList.add(msg);
                              });

                              final body = {
                                'model': chatCtrl.selectedModel,
                                'chat_id': chatId,
                                'content': _textController.text.trim(),
                                'attachments': attachments.map((e) {
                                  return {'name': e.name};
                                }).toList(),
                              };

                              if (attachments.isNotEmpty) {
                                setState(() {
                                  attachments.clear();
                                });
                              }

                              _socket.send(chatId, body);

                              _textController.clear();
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
