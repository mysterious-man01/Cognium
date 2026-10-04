import 'dart:js_interop';
import 'package:flutter/foundation.dart';
import 'package:web/web.dart' as web;

class TTSPlayer extends ChangeNotifier {
  web.HTMLAudioElement? _audio;
  String? _url;
  bool _state = false;
  int _id = 0;

  bool get isPlaying => _state;
  int get id => _id;

  void _cleanUp() {
    if (_url != null) {
      web.URL.revokeObjectURL(_url!);
    }

    _audio = null;
    _url = null;
    _id = 0;
  }

  Future<void> play(Uint8List data, int msgId) async {
    stop();
    
    _id = msgId;

    final blob = web.Blob(
      [data.toJS].toJS,
      web.BlobPropertyBag(type: 'audio/wav'),
    );

    _url = web.URL.createObjectURL(blob);

    _audio = web.HTMLAudioElement()
      ..src = _url!
      ..controls = false;

    _audio!.onPlay.listen((_) {
      _state = true;
      notifyListeners();
    });

    _audio!.onPause.listen((_) {
      _state = false;
      notifyListeners();
    });

    _audio!.onEnded.listen((_) {
      _state = false;
      notifyListeners();

      _cleanUp();
    });

    await _audio!.play().toDart;
  }

  void stop() {
    _audio?.pause();
    _cleanUp();

    if (_state) {
      _state = false;
      notifyListeners();
    }
  }
}
