import 'dart:async';
import 'dart:convert';

import 'package:web_socket_channel/web_socket_channel.dart';

class WebSocket {
  static final WebSocket _instance = WebSocket._();
  WebSocketChannel? _channel;
  late final Stream _events;
  int _connectionAtempts = 5;
  String _error = '';

  WebSocket._() {
    _channel = WebSocketChannel.connect(Uri.parse('ws://127.0.0.1:8000/ws'));
    _channel?.ready.then((_) {}).catchError((e) {
      _error = 'WebSocket error => $e';
    });

    _events = _channel!.stream.asBroadcastStream();
  }

  factory WebSocket() {
    return _instance;
  }

  Stream get events => _events;

  Future<void> _connect() async {
    while (_connectionAtempts > 0) {
      _channel = WebSocketChannel.connect(Uri.parse('ws://127.0.0.1:8000/ws'));

      try {
        await _channel!.ready;
        _error = '';
        _connectionAtempts = 5;
      } catch (e) {
        _error = 'WebSocket Error => $e';
        _connectionAtempts--;
        continue;
      }
    }

    if (_error.isNotEmpty) {
      _connectionAtempts = 5;
      throw Exception(_error);
    }
  }

  Future<void> send(int chatIndex, Map<String, dynamic> content) async {
    if (_channel != null && _channel!.closeCode == null) {
      _channel!.sink.add(jsonEncode(content));
    } else {
      try {
        await _connect();

        send(chatIndex, content);
      } catch (e) {
        rethrow;
      }
    }
  }

  void dispose() async {
    await _channel?.sink.close();
  }
}
