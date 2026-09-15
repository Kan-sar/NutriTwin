import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:nutritwin_mobile/api.dart';

void main() {
  test(
    'concurrent 401 responses rotate once and replay with the new token',
    () async {
      var rotations = 0;
      final api = NutriApi(
        client: MockClient((request) async {
          if (request.url.path.endsWith('/login')) {
            return http.Response(
              jsonEncode({'access_token': 'old', 'refresh_token': 'refresh'}),
              200,
            );
          }
          if (request.url.path.endsWith('/refresh')) {
            rotations++;
            await Future<void>.delayed(const Duration(milliseconds: 10));
            return http.Response(
              jsonEncode({'access_token': 'new', 'refresh_token': 'rotated'}),
              200,
            );
          }
          return request.headers['Authorization'] == 'Bearer new'
              ? http.Response('{"ok":true}', 200)
              : http.Response('{"detail":"expired"}', 401);
        }),
      );
      await api.login('student@example.com', 'test-only');
      final results = await Future.wait([
        api.request('GET', '/one'),
        api.request('GET', '/two'),
      ]);
      expect(rotations, 1);
      expect(results.every((r) => r['ok'] == true), isTrue);
      api.dispose();
    },
  );
  test(
    'logout clears credentials even if the server cannot revoke them',
    () async {
      String? authorization;
      final api = NutriApi(
        client: MockClient((request) async {
          if (request.url.path.endsWith('/login')) {
            return http.Response(
              '{"access_token":"old","refresh_token":"refresh"}',
              200,
            );
          }
          authorization = request.headers['Authorization'];
          return http.Response('{"detail":"offline"}', 503);
        }),
      );
      await api.login('student@example.com', 'test-only');
      await expectLater(api.logout(), throwsA(isA<ApiError>()));
      await expectLater(
        api.request('GET', '/private'),
        throwsA(isA<ApiError>()),
      );
      expect(authorization, isNull);
      api.dispose();
    },
  );
}
