import 'dart:async';
import 'dart:js_interop';
import 'package:flutter/foundation.dart';
import 'dart:typed_data';
import 'package:web/web.dart' as web;
import 'package:record/record.dart' as rec;

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

    _audio?.remove();

    _audio = null;
    _url = null;
    _id = 0;
  }

  Future<void> play(Uint8List data, int msgId) async {
    if (_state) stop();

    _id = msgId;

    final blob = web.Blob(
      [data.toJS].toJS,
      web.BlobPropertyBag(type: 'audio/wav'),
    );

    _url = web.URL.createObjectURL(blob);

    _audio = web.HTMLAudioElement()
      ..src = _url!
      ..controls = false;

    web.document.body!.append(_audio!);

    _audio!.onPlay.listen((_) {
      _state = true;
      notifyListeners();
    });

    _audio!.onError.listen((_) {
      print(
        "error: TTSPlayer => Code: ${_audio!.error?.code}\nDetail: ${_audio!.error?.message}",
      );
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

class STTRecorder extends ChangeNotifier {
  rec.AudioRecorder? _recorder;
  StreamSubscription<Uint8List>? _subscription;
  bool _isRecording = false;
  final BytesBuilder _buffer = BytesBuilder();

  bool get isRecording => _isRecording;
  Uint8List? get data => _buffer.toBytes();

  Future<void> record() async {
    _recorder ??= rec.AudioRecorder();

    if (!await _recorder!.hasPermission()) {
      print("error: STTRecorder => Microphone permission denied");
      return;
    }

    _buffer.clear();

    final stream = await _recorder!.startStream(
      rec.RecordConfig(
        encoder: rec.AudioEncoder.pcm16bits,
        sampleRate: 16000,
        numChannels: 1,
      ),
    );

    _isRecording = true;
    notifyListeners();

    _subscription = stream.listen(_buffer.add);
  }

  Future<void> stop() async {
    if (_recorder == null || !await _recorder!.isRecording()) {
      return;
    }

    await _recorder!.stop();

    await _subscription?.cancel();
    _subscription = null;

    _isRecording = false;
    notifyListeners();
  }

  @override
  void dispose() async {
    if (_recorder == null) {
      return;
    }

    if (await _recorder!.isRecording()) {
      stop();
    }

    await _recorder!.dispose();
    super.dispose();
  }
}
