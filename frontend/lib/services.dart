import 'dart:convert';
import 'dart:typed_data';
import 'dart:html' as html;
import 'package:http/http.dart' as http;
import 'package:frontend/objects.dart';

Future<dynamic> fetchData(
  String endpoint,
  String method, {
  Map<String, dynamic>? data,
}) async {
  final request = http.Request(
    method.toUpperCase(),
    Uri.parse("http://127.0.0.1:8000$endpoint"),
  );

  if (data != null) {
    request.bodyBytes = utf8.encode(jsonEncode(data));
    request.headers['content-type'] = "application/json";
  }

  try {
    final response = await request.send();

    if (response.statusCode == 200 || response.statusCode == 201) {
      await for (final data in response.stream.transform(utf8.decoder)) {
        return jsonDecode(data);
      }
    } else {
      return {'detail': "Failed to fetch data\nCode: ${response.statusCode}"};
    }
  } catch (e) {
    return {'detail': 'Failed to connect to the server. Error: $e'};
  }
}

Future<dynamic> uploadFile(List<AttachmentLocal> files) async {
  final request = http.MultipartRequest(
    'POST',
    Uri.parse('http://127.0.0.1:8000/uploads'),
  );

  for (final file in files) {
    request.files.add(
      http.MultipartFile(
        'data',
        http.ByteStream(Stream.value(file.data!)),
        file.size,
        filename: file.name,
      ),
    );
  }

  try {
    final response = await request.send();
    if (response.statusCode == 200) {
      final body = await response.stream.transform(utf8.decoder).join();
      return jsonDecode(body);
    } else {
      return {'detail': "File upload has failed\nCode ${response.statusCode}"};
    }
  } catch (e) {
    return {'detail': "Failed to send archives -> $e"};
  }
}

Future<AttachmentRemote> getFile(String fileName) async {
  final request = http.Request(
    'GET',
    Uri.parse("http://127.0.0.1:8000/uploads/$fileName"),
  );

  final response = await request.send();

  if (response.statusCode != 200) {
    throw Exception("Failed to get data: Code => ${response.statusCode}");
  }

  final bytes = await response.stream.toBytes();

  return AttachmentRemote(
    id: int.parse(response.headers['attachment-id']!),
    name: response.headers['file-name']!,
    size: int.parse(response.headers['content-length']!),
    data: bytes,
  );
}

Future<Uint8List?> fetchTTSData({required int chatId, required int msgId}) async {
  final request = http.Request('POST', Uri.parse('http://127.0.0.1:8000/tts'));

  request.headers['content-type'] = 'application/json';

  request.body = jsonEncode({'chat_id': chatId, 'msg_id': msgId});

  try {
    final response = await request.send();

    if (response.statusCode == 200) {
      return await response.stream.toBytes();
    }

    return null;
  } catch (e) {
    print('Error: fetchTTSData -> $e');
    return null;
  }
}

Stream<String> fetchStreamData(Map<String, dynamic> data) async* {
  final client = http.Client();

  final request = http.Request(
    'POST',
    Uri.parse('http://127.0.0.1:8000/v1/chat/completions'),
  );

  request.bodyBytes = utf8.encode(jsonEncode(data));
  request.headers['content-type'] = 'application/json';

  try {
    final response = await client.send(request);

    if (response.statusCode == 200) {
      await for (final chunk in response.stream.transform(utf8.decoder)) {
        yield chunk;
      }
    } else {
      throw Exception("Failed to fetch data\nCode: ${response.statusCode}");
    }
  } catch (e) {
    throw Exception("Filed to connect to the server. Error: $e");
  }
}
