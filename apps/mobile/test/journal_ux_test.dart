import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:nutritwin_mobile/api.dart';
import 'package:nutritwin_mobile/main.dart';
import 'package:nutritwin_mobile/palettes.dart';

void main() {
  testWidgets(
    'palette picker works on a narrow screen and preserves sign-in input',
    (tester) async {
      tester.view.physicalSize = const Size(390, 844);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      await tester.pumpWidget(const NutriTwinApp());
      final email = find.byWidgetPredicate(
        (w) => w is TextField && w.decoration?.labelText == 'Email',
      );
      await tester.enterText(email, 'demo@example.com');
      for (final palette in appPalettes) {
        await tester.ensureVisible(find.text('Color palette'));
        await tester.tap(find.text('Color palette'));
        await tester.pumpAndSettle();
        final option = find.descendant(
          of: find.byType(AlertDialog),
          matching: find.text(palette.name),
        );
        await tester.ensureVisible(option);
        await tester.tap(option);
        await tester.pumpAndSettle();
        expect(
          tester
              .widget<MaterialApp>(find.byType(MaterialApp))
              .theme!
              .scaffoldBackgroundColor,
          palette.background,
        );
        expect(
          tester.widget<TextField>(email).controller!.text,
          'demo@example.com',
        );
        expect(tester.takeException(), isNull);
      }
    },
  );
  test('palette fallbacks and primary text remain readable', () {
    expect(paletteById('obsolete').id, 'nutritwin');
    for (final p in appPalettes) {
      double contrast(Color a, Color b) {
        final x = a.computeLuminance(), y = b.computeLuminance();
        return ((x > y ? x : y) + .05) / ((x < y ? x : y) + .05);
      }

      expect(
        contrast(p.text, p.surface),
        greaterThanOrEqualTo(4.5),
        reason: p.name,
      );
      for (final pair in [
        [p.onNavigation, p.navigation],
        [p.text, p.container],
        [p.text, p.theme.colorScheme.surfaceContainerHighest],
      ]) {
        expect(
          contrast(pair[0], pair[1]),
          greaterThanOrEqualTo(4.5),
          reason: p.name,
        );
      }
      expect(
        contrast(p.onAccent, p.accent),
        greaterThanOrEqualTo(4.5),
        reason: p.name,
      );
    }
  });

  testWidgets(
    'journal guides empty search, validates drafts and retains them across palette changes',
    (tester) async {
      tester.view.physicalSize = const Size(1400, 2200);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      var saves = 0;
      final api = NutriApi(
        client: MockClient((r) async {
          dynamic body;
          switch (r.url.path) {
            case '/api/v1/auth/login':
              body = {'access_token': 'test', 'refresh_token': 'refresh'};
            case '/api/v1/users/me':
              body = {'email': 'demo@example.com', 'role': 'student'};
            case '/api/v1/profiles/me':
              body = {
                'birth_date': '2000-01-01',
                'dietary_pattern': 'vegetarian',
                'allergens': [],
              };
            case '/api/v1/twin/summary':
              body = {
                'target_provisional': true,
                'logged_days_30': 0,
                'nutrients': [],
                'medical_disclaimer': 'Prototype',
              };
            case '/api/v1/preferences':
              body = {'maximum_preparation_minutes': 30, 'weights': {}};
            case '/api/v1/recommendations/history':
              body = [];
            case '/api/v1/meals':
              if (r.method == 'POST') {
                saves++;
                body = {'id': 'saved'};
              } else {
                body = [];
              }
            case '/api/v1/foods':
              body = r.url.queryParameters['query'] == 'nothing'
                  ? []
                  : [
                      {
                        'id': 'f1',
                        'name': 'Test lentils',
                        'source_code': 'TEST',
                        'nutrients': [
                          {
                            'nutrient_code': 'iron',
                            'unit': 'mg',
                            'amount_per_100g': '3',
                          },
                        ],
                      },
                    ];
            default:
              throw StateError(r.url.toString());
          }
          return http.Response(jsonEncode(body), 200);
        }),
      );
      await tester.pumpWidget(NutriTwinApp(api: api));
      await tester.tap(find.widgetWithText(FilledButton, 'Sign in'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Food journal'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Build a meal'));
      await tester.pumpAndSettle();
      expect(find.textContaining('Your draft is empty'), findsOneWidget);
      Finder field(String name) => find.byWidgetPredicate(
        (w) => w is TextField && w.decoration?.labelText == name,
      );
      await tester.enterText(field('Search foods'), 'nothing');
      await tester.testTextInput.receiveAction(TextInputAction.done);
      await tester.pumpAndSettle();
      expect(find.textContaining('No foods found'), findsOneWidget);
      await tester.enterText(field('Search foods'), 'lentils');
      await tester.tap(find.widgetWithText(FilledButton, 'Search'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Test lentils'));
      await tester.pumpAndSettle();
      expect(find.text('Composition per 100 g'), findsOneWidget);
      expect(find.text('3.00 mg'), findsOneWidget);
      expect(find.text('Source: TEST'), findsOneWidget);
      await tester.tap(find.text('Close'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Add food'));
      await tester.pumpAndSettle();
      await tester.tap(find.byTooltip('Choose meal date'));
      await tester.pumpAndSettle();
      expect(find.byType(DatePickerDialog), findsOneWidget);
      await tester.tap(find.text('Cancel'));
      await tester.pumpAndSettle();
      await tester.tap(find.byTooltip('Choose meal time'));
      await tester.pumpAndSettle();
      expect(find.byType(TimePickerDialog), findsOneWidget);
      await tester.tap(find.text('Cancel'));
      await tester.pumpAndSettle();
      expect(find.textContaining('Review draft · 1'), findsNothing);
      await tester.ensureVisible(find.text('Saved entries'));
      await tester.tap(find.text('Saved entries'));
      await tester.pumpAndSettle();
      expect(find.textContaining('Review draft · 1'), findsOneWidget);
      await tester.tap(find.textContaining('Review draft · 1'));
      await tester.pumpAndSettle();
      expect(find.textContaining('Review draft · 1'), findsNothing);
      final grams = find.byType(TextFormField);
      await tester.enterText(grams, '-5');
      await tester.tap(find.widgetWithText(FilledButton, 'Save meal'));
      await tester.pumpAndSettle();
      expect(saves, 0);
      expect(find.textContaining('greater than zero'), findsOneWidget);
      await tester.enterText(grams, '125');
      await tester.enterText(field('Meal date (YYYY-MM-DD)'), '2026-02-31');
      await tester.tap(find.widgetWithText(FilledButton, 'Save meal'));
      await tester.pumpAndSettle();
      expect(saves, 0);
      expect(find.textContaining('valid meal date'), findsOneWidget);
      await tester.enterText(field('Meal date (YYYY-MM-DD)'), '2026-01-01');
      await tester.tap(find.text('Color palette'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Nord'));
      await tester.pumpAndSettle();
      expect(
        tester
            .widget<MaterialApp>(find.byType(MaterialApp))
            .theme!
            .scaffoldBackgroundColor,
        paletteById('nord').background,
      );
      expect(find.text('125'), findsOneWidget);
      expect(find.textContaining('Review draft · 1'), findsNothing);
      await tester.tap(find.widgetWithText(FilledButton, 'Save meal'));
      await tester.pumpAndSettle();
      expect(saves, 1);
      expect(find.textContaining('My meal saved.'), findsOneWidget);
      expect(find.textContaining('Your draft is empty'), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );
}
