import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:nutritwin_mobile/nutrient_explorer.dart';

void main() {
  final nutrients = [
    for (final entry in {'iron': 135, 'vitamin_c': 42, 'calcium': null}.entries)
      {
        'nutrient_code': entry.key,
        'consumed': {
          'daily': {'coverage_percent': entry.value},
          'rolling_7_day': {
            'coverage_percent': entry.value == null ? null : 60,
          },
          'rolling_30_day': {'coverage_percent': null},
        },
      },
  ];
  testWidgets(
    'focus, windows and target bars retain unknown and over-target values',
    (tester) async {
      String? focus;
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: SingleChildScrollView(
              child: NutrientExplorer(
                nutrients: nutrients,
                onSelected: (v) => focus = v,
              ),
            ),
          ),
        ),
      );
      expect(find.text('135.0%'), findsOneWidget);
      expect(find.text('Unknown'), findsOneWidget);
      await tester.tap(find.widgetWithText(OutlinedButton, 'iron'));
      await tester.pumpAndSettle();
      expect(focus, 'iron');
      await tester.tap(find.text('All nutrients'));
      await tester.pumpAndSettle();
      expect(focus, isNull);
      await tester.tap(find.text('7 days'));
      await tester.pumpAndSettle();
      expect(find.text('60.0%'), findsNWidgets(2));
      await tester.tap(find.text('Target bars'));
      await tester.pumpAndSettle();
      expect(find.byType(LinearProgressIndicator), findsNWidgets(2));
      expect(find.text('No coverage available'), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('nutrient controls fit a narrow screen with enlarged text', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(
      MaterialApp(
        home: MediaQuery(
          data: const MediaQueryData(textScaler: TextScaler.linear(1.3)),
          child: Scaffold(
            body: SingleChildScrollView(
              child: NutrientExplorer(nutrients: nutrients, onSelected: (_) {}),
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
  });

  testWidgets(
    'food ranking distinguishes zero from missing and adds the chosen food',
    (tester) async {
      final semantics = tester.ensureSemantics();
      dynamic added;
      final foods = [
        for (final entry in {
          'Unknown food': null,
          'Zero food': 0,
          'Rich food': 8,
        }.entries)
          {
            'name': entry.key,
            'source_code': 'TEST',
            'nutrients': [
              {
                'nutrient_code': 'iron',
                'unit': 'mg',
                'amount_per_100g': entry.value,
              },
            ],
          },
      ];
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: FoodNutrientExplorer(
              foods: foods,
              onAdd: (f) => added = f,
              onInspect: (_) {},
            ),
          ),
        ),
      );
      expect(
        tester.getTopLeft(find.text('Rich food')).dy,
        lessThan(tester.getTopLeft(find.text('Zero food')).dy),
      );
      expect(find.text('TEST · Unknown per 100 g'), findsOneWidget);
      expect(find.text('TEST · 0.00 mg per 100 g'), findsOneWidget);
      expect(
        tester.getSemantics(
          find.descendant(
            of: find.byTooltip('Add Rich food to draft'),
            matching: find.byType(TextButton),
          ),
        ),
        matchesSemantics(
          label: 'Add food',
          isButton: true,
          hasEnabledState: true,
          isEnabled: true,
          isFocusable: true,
          hasTapAction: true,
          hasFocusAction: true,
        ),
      );
      await tester.tap(find.byTooltip('Add Rich food to draft'));
      expect(added['name'], 'Rich food');
      semantics.dispose();
    },
  );
}
