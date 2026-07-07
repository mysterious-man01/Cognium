import 'dart:convert';
import 'package:http/http.dart' as http;

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
