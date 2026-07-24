import 'dart:typed_data';
import 'package:file_picker/file_picker.dart';

class Chat {
  int? id;
  String? title;
  dynamic timestamp;
  bool isGenerating;

  Chat({
    required this.id,
    this.title,
    this.timestamp,
    this.isGenerating = false,
  });

  Map<String, dynamic> toJson() {
    return {"id": id, "title": title, "timestamp": timestamp};
  }
}

class Message {
  int? id;
  String role;
  dynamic content;
  List<AttachmentBase>? attachments;
  Map<String, dynamic>? metrics;
  dynamic timestamp;

  Message({
    required this.id,
    required this.role,
    required this.content,
    required this.attachments,
    required this.metrics,
    required this.timestamp,
  });

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'role': role,
      'content': content,
      'atachments': attachments == null
          ? const []
          : attachments!.map((att) => att.name).toList(growable: false),
      'metrics': metrics,
      'timestamp': timestamp,
    };
  }
}

abstract class AttachmentBase {
  String get name;
  int get size;
}

class AttachmentRemote extends AttachmentBase {
  final int? id;
  @override
  final String name;
  @override
  final int size;
  final Uint8List? data;

  AttachmentRemote({
    required this.id,
    required this.name,
    required this.size,
    required this.data,
  });

  Map<String, dynamic> toJson() {
    return {'id': id, 'name': name, 'size': size};
  }
}

class AttachmentLocal extends AttachmentBase {
  final PlatformFile file;

  @override
  String get name => file.name;

  @override
  int get size => file.size;

  AttachmentLocal({required this.file});

  PlatformFile toPlatformFile() => file;
}
