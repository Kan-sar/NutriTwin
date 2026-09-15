import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:nutritwin_mobile/api.dart';
import 'package:nutritwin_mobile/main.dart';

void main() {
  for (final operation in ['edit', 'delete']) {
    testWidgets('stale meal $operation is rejected and can be refreshed', (
      tester,
    ) async {
      tester.view.physicalSize = const Size(1400, 1800);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      var revision = 1;
      final mutations = <http.Request>[];
      final api = NutriApi(
        client: MockClient((request) async {
          final path = request.url.path;
          dynamic body;
          if (request.method == 'PUT' || request.method == 'DELETE') {
            mutations.add(request);
            return http.Response(
              jsonEncode({
                'detail': 'This meal changed since you loaded it. Refresh the journal before editing or deleting it again.',
              }),
              409,
            );
          }
          switch (path) {
            case '/api/v1/auth/login':
              body = {
                'access_token': 'test-access',
                'refresh_token': 'test-refresh',
              };
            case '/api/v1/users/me':
              body = {'email': 'test@example.com', 'role': 'student'};
            case '/api/v1/profiles/me':
              body = {
                'birth_date': '2000-01-01',
                'dietary_pattern': 'unrestricted',
                'allergens': [],
              };
            case '/api/v1/twin/summary':
              body = {
                'target_provisional': true,
                'logged_days_30': 1,
                'nutrients': [],
                'medical_disclaimer': 'Academic prototype.',
              };
            case '/api/v1/meals':
              body = [
                {
                  'id': 'meal-1',
                  'revision': revision,
                  'name': revision == 1 ? 'Original meal' : 'Changed elsewhere',
                  'local_date': '2026-09-15',
                  'eaten_at': '2026-09-15T12:00:00Z',
                  'ingredients': [
                    {'food_id': 'food-1', 'quantity_g': '100'},
                  ],
                },
              ];
            case '/api/v1/recommendations/history':
              body = [];
            case '/api/v1/preferences':
              body = {'maximum_preparation_minutes': 30, 'weights': {}};
            default:
              throw StateError('Unexpected request: ${request.method} $path');
          }
          return http.Response(jsonEncode(body), 200);
        }),
      );
      await tester.pumpWidget(NutriTwinApp(api: api));
      await tester.tap(find.widgetWithText(FilledButton, 'Sign in'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Food journal'));
      await tester.pumpAndSettle();
      revision = 2; // Another tab saves after this client loaded revision 1.
      if (operation == 'edit') {
        await tester.tap(find.byTooltip('Edit meal'));
        await tester.pumpAndSettle();
        final nameField = find.byWidgetPredicate(
          (w) => w is TextField && w.decoration?.labelText == 'Meal name',
        );
        await tester.enterText(nameField, 'My unsaved draft');
        final save = find.widgetWithText(FilledButton, 'Save changes');
        await tester.ensureVisible(save);
        await tester.tap(save);
        await tester.pumpAndSettle();
        expect(
          tester.widget<TextField>(nameField).controller!.text,
          'My unsaved draft',
        );
      } else {
        await tester.tap(find.byTooltip('Delete meal'));
        // The background loading indicator runs while confirmation is pending.
        await tester.pump(const Duration(milliseconds: 300));
        await tester.tap(find.widgetWithText(FilledButton, 'Delete'));
        await tester.pumpAndSettle();
        expect(find.text('Original meal'), findsOneWidget);
      }
      expect(mutations, hasLength(1));
      expect(mutations.single.url.queryParameters['expected_revision'], '1');
      expect(find.textContaining('This meal changed since'), findsOneWidget);
      final refresh = find.widgetWithText(FilledButton, 'Refresh journal');
      await tester.ensureVisible(refresh);
      await tester.tap(refresh);
      await tester.pumpAndSettle();
      expect(find.text('Changed elsewhere'), findsOneWidget);
      if (operation == 'edit') {
        expect(find.text('My unsaved draft'), findsOneWidget);
        await tester.tap(find.byTooltip('Edit meal'));
        await tester.pumpAndSettle();
        final save = find.widgetWithText(FilledButton, 'Save changes');
        await tester.ensureVisible(save);
        await tester.tap(save);
        await tester.pumpAndSettle();
        expect(mutations.last.url.queryParameters['expected_revision'], '2');
      }
      expect(tester.takeException(), isNull);
    });
  }
}
