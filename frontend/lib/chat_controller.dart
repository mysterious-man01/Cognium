import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';

import 'package:frontend/objects.dart';
import 'package:frontend/services.dart';
import 'package:frontend/websocket.dart';

class ChatController extends ChangeNotifier {
  final WebSocket _socket = WebSocket();
  late final StreamSubscription _sub;
  final List<Chat> _chatList = [];
  int _chatIndex = 0;
  String _selectedModel = '';

  ChatController() {
    updateChatList();

    _sub = _socket.events.listen((raw) {
      final data = jsonDecode(raw);

      if (data.containsKey('chat_id')) {
        if (data.containsKey('new_id')) {
          updateChatList();

          if (data['chat_id'] == _chatIndex) {
            modifyIndex(data['new_id']);
          }
        }

        if (data.containsKey('status')) {
          final chat = _chatList.where((e) => e.id == data['chat_id']).first;
          if (data['status'] == 'generating' && chat.isGenerating == false) {
            generating(chat.id!);
          }

          if (data['status'] == 'completed') {
            stopGenerating(chat.id!);
          }
        }
      }
    });
  }

  @override
  void dispose() {
    _sub.cancel();

    super.dispose();
  }

  List<Chat> get chatList => _chatList;
  int get chatIndex => _chatIndex;
  String get selectedModel => _selectedModel;

  void setSelectedModel(String model) {
    _selectedModel = model;

    notifyListeners();
  }

  void generating(int chatId) {
    final result = _chatList.where((chat) => chat.id == chatId);
    if (result.isNotEmpty) {
      result.first.isGenerating = true;
      notifyListeners();
    }
  }

  void stopGenerating(int chatId) {
    final result = _chatList.where((chat) => chat.id == chatId);
    if (result.isNotEmpty) {
      result.first.isGenerating = false;
      notifyListeners();
    }
  }

  void updateChatList() async {
    try {
      final result = await fetchData('/chat', 'GET');

      if (result is List && _chatList.length < result.length) {
        final slice = _chatList.isEmpty
            ? result
            : result.sublist(_chatList.length);

        for (final item in slice) {
          if (item.containsKey('id') &&
              item.containsKey('title') &&
              item.containsKey('timestamp')) {
            _chatList.add(
              Chat(
                id: item['id'],
                title: item['title'],
                timestamp: item['timestamp'],
                isGenerating: false,
              ),
            );
          }
        }
      }
    } catch (e) {
      print('Error: $e'); // Show it on UI
    }

    notifyListeners();
  }

  void modifyIndex(int index) {
    if (_chatIndex == index) return;

    print('--- CONTROLLER: Novo índice setado para: $index ---');
    _chatIndex = index;

    notifyListeners();
  }
}
