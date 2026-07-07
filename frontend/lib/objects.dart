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
  dynamic timestamp;

  Message({
    required this.id,
    required this.role,
    required this.content,
    required this.timestamp,
  });

  Map<String, dynamic> toJson() {
    return {'id': id, 'role': role, 'content': content, 'timestamp': timestamp};
  }
}
