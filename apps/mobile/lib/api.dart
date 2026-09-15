import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

class ApiError implements Exception {
  final int status;
  final String message;
  ApiError(this.status, this.message);
  @override
  String toString() => message;
}

/// Tokens deliberately live only in memory, including on the web.
class NutriApi {
  final http.Client client;
  final String baseUrl;
  String? _access;
  String? _refresh;
  Future<void>? _refreshing;
  NutriApi({
    http.Client? client,
    this.baseUrl = const String.fromEnvironment(
      'API_BASE_URL',
      defaultValue: 'http://127.0.0.1:8000',
    ),
  }) : client = client ?? http.Client();
  void clear() {
    _access = null;
    _refresh = null;
  }

  void dispose() => client.close();
  void _tokens(dynamic result) {
    _access = result['access_token'] as String;
    _refresh = result['refresh_token'] as String;
  }

  Future<void> login(String email, String password) async {
    _tokens(
      await request(
        'POST',
        '/auth/login',
        body: {'email': email, 'password': password},
        retry: false,
      ),
    );
  }

  Future<void> logout() async {
    try {
      if (_refresh != null) {
        await request(
          'POST',
          '/auth/logout',
          body: {'refresh_token': _refresh},
          retry: false,
        );
      }
    } finally {
      clear();
    }
  }

  Future<void> _rotate() async {
    try {
      _tokens(
        await request(
          'POST',
          '/auth/refresh',
          body: {'refresh_token': _refresh},
          retry: false,
        ),
      );
    } catch (_) {
      clear();
      rethrow;
    }
  }

  Future<dynamic> request(
    String method,
    String path, {
    Object? body,
    bool retry = true,
  }) async {
    final sentToken = _access;
    final req = http.Request(method, Uri.parse('$baseUrl/api/v1$path'));
    req.headers['Content-Type'] = 'application/json';
    if (sentToken != null) req.headers['Authorization'] = 'Bearer $sentToken';
    if (body != null) req.body = jsonEncode(body);
    http.Response response;
    try {
      response = await http.Response.fromStream(await client.send(req))
          .timeout(const Duration(seconds: 20));
    } on TimeoutException {
      throw ApiError(
        0,
        'The request timed out. Refresh before retrying a saved change.',
      );
    } on http.ClientException {
      throw ApiError(
        0,
        'Cannot reach NutriTwin. Check your connection and try again.',
      );
    }
    if (response.statusCode == 401 && retry && _refresh != null) {
      // Concurrent expired requests share one rotation. Late 401s reuse the new token.
      if (sentToken == _access) {
        final pending = _refreshing ??= _rotate();
        try {
          await pending;
        } finally {
          if (identical(_refreshing, pending)) _refreshing = null;
        }
      }
      return request(method, path, body: body, retry: false);
    }
    dynamic decoded;
    try {
      decoded = response.body.isEmpty ? null : jsonDecode(response.body);
    } on FormatException {
      throw ApiError(response.statusCode, 'Unexpected server response.');
    }
    if (response.statusCode >= 400) {
      if (response.statusCode == 401) clear();
      final detail = decoded is Map
          ? decoded['detail'] ?? decoded['error']
          : null;
      throw ApiError(
        response.statusCode,
        detail is String
            ? detail
            : 'Check the entered values. The server rejected this request (${response.statusCode}).',
      );
    }
    return decoded;
  }
}
