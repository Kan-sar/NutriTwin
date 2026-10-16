import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:nutritwin_mobile/api.dart';
import 'package:nutritwin_mobile/dishes.dart';

Map<String, dynamic> nutrient(
  String? value,
  String unit, {
  bool complete = true,
}) => {'amount': value, 'canonical_unit': unit, 'complete': complete};
Map<String, dynamic> composition() => {
  'portion_weight_g': '100',
  'ingredients': [
    {
      'food_id': 'food',
      'name': 'Cooked lentils',
      'quantity_g': '100',
      'nutrients': {
        'protein': nutrient('9', 'g'),
        'iron': nutrient(null, 'mg', complete: false),
      },
    },
  ],
  'nutrients': {
    'protein': nutrient('9', 'g'),
    'iron': nutrient(null, 'mg', complete: false),
  },
};
void main() {
  testWidgets('composition views retain nutrient focus when switching', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SingleChildScrollView(
            child: CompositionView(data: composition()),
          ),
        ),
      ),
    );
    await tester.tap(find.byType(DropdownButtonFormField<String>));
    await tester.pumpAndSettle();
    await tester.tap(find.text('iron').last);
    await tester.pumpAndSettle();
    expect(find.text('Unknown mg'), findsOneWidget);
    await tester.ensureVisible(find.text('Nutrient bubbles'));
    await tester.tap(find.text('Nutrient bubbles'));
    await tester.pumpAndSettle();
    expect(find.text('Unknown mg'), findsNothing);
    expect(find.text('Plate builder · nutrient bubbles'), findsOneWidget);
    await tester.tap(find.text('Ingredient breakdown'));
    await tester.pumpAndSettle();
    expect(find.text('Unknown mg'), findsOneWidget);
    expect(find.text('Plate builder · nutrient bubbles'), findsNothing);
    expect(tester.takeException(), isNull);
  });
  testWidgets(
    'composition switches focus and preserves unknown contributions',
    (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: SingleChildScrollView(
              child: CompositionView(data: composition()),
            ),
          ),
        ),
      );
      expect(find.text('9 g'), findsOneWidget);
      await tester.ensureVisible(find.byType(DropdownButtonFormField<String>));
      await tester.tap(find.byType(DropdownButtonFormField<String>));
      await tester.pumpAndSettle();
      await tester.tap(find.text('iron').last);
      await tester.pumpAndSettle();
      expect(find.text('Unknown mg'), findsOneWidget);
      expect(
        find.textContaining('Some ingredient values are unknown'),
        findsOneWidget,
      );
      expect(tester.takeException(), isNull);
    },
  );
  testWidgets('dish logs directly and retries with the same request key', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1100, 2000);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final logs = <Map<String, dynamic>>[];
    var refreshed = 0;
    final api = NutriApi(
      client: MockClient((r) async {
        dynamic body = [];
        if (r.url.path.endsWith('/recipes')) {
          body = [
            {
              'id': 'recipe',
              'name': 'Lentil bowl',
              'kind': 'recipe',
              'source': 'Test source',
              'portions': {'g': '1'},
            },
          ];
        }
        if (r.url.path.endsWith('/composition/preview')) body = composition();
        if (r.url.path.endsWith('/food-log')) {
          logs.add(Map<String, dynamic>.from(jsonDecode(r.body)));
          if (logs.length == 1) throw http.ClientException('offline');
          body = {'id': 'meal', 'revision': 1};
        }
        return http.Response(jsonEncode(body), 200);
      }),
    );
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SingleChildScrollView(
            child: DishWorkspace(
              api: api,
              onChanged: () async {
                refreshed++;
              },
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.text('Lentil bowl'));
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.widgetWithText(FilledButton, 'Log food'));
    await tester.tap(find.widgetWithText(FilledButton, 'Log food'));
    await tester.pumpAndSettle();
    expect(find.text('Retry log'), findsOneWidget);
    await tester.ensureVisible(find.text('Retry log'));
    await tester.tap(find.text('Retry log'));
    await tester.pumpAndSettle();
    expect(logs.length, 2);
    expect(logs[0], logs[1]);
    expect(logs[0]['recipe_id'], 'recipe');
    expect(refreshed, 1);
    expect(find.text('Undo log'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
  testWidgets('private recipe records batch yield and ingredient amounts', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1100, 2200);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    Map<String, dynamic>? saved;
    final api = NutriApi(
      client: MockClient((r) async {
        dynamic body = [];
        if (r.url.path.endsWith('/foods')) {
          body = [
            {
              'id': 'food',
              'name': 'Cooked lentils',
              'source_code': 'Test source',
            },
          ];
        }
        if (r.url.path.endsWith('/composition/preview')) body = composition();
        if (r.method == 'POST' && r.url.path.endsWith('/recipes')) {
          saved = Map<String, dynamic>.from(jsonDecode(r.body));
          body = {
            'id': 'recipe',
            'name': saved!['name'],
            'portions': {'serving': '100'},
            'source': 'Your recipe',
          };
        }
        return http.Response(jsonEncode(body), 200);
      }),
    );
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SingleChildScrollView(
            child: DishWorkspace(api: api, onChanged: () async {}),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.text('Create recipe'));
    await tester.pumpAndSettle();
    await tester.enterText(
      find.widgetWithText(TextField, 'Recipe name'),
      'My bowl',
    );
    await tester.enterText(
      find.widgetWithText(TextField, 'Finished batch weight (g)'),
      '200',
    );
    await tester.enterText(
      find.widgetWithText(TextField, 'Servings in this batch'),
      '2',
    );
    await tester.enterText(
      find.widgetWithText(TextField, 'Find an ingredient'),
      'lentils',
    );
    await tester.testTextInput.receiveAction(TextInputAction.done);
    await tester.pumpAndSettle();
    await tester.tap(find.text('Cooked lentils').first);
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.text('Save private recipe'));
    await tester.tap(find.text('Save private recipe'));
    await tester.pumpAndSettle();
    expect(saved?['yield_g'], '200');
    expect(saved?['servings'], '2');
    expect(saved?['ingredients'], [
      {'food_id': 'food', 'quantity_g': '100'},
    ]);
    expect(
      find.text('Recipe saved privately. Choose a portion to log it.'),
      findsOneWidget,
    );
    expect(tester.takeException(), isNull);
  });
}
