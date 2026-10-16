import 'dart:convert';

import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:nutritwin_mobile/api.dart';
import 'package:nutritwin_mobile/composition_analytics.dart';

final stats = <String, dynamic>{
  'nutrient_code': 'iron',
  'unit': 'mg',
  'count': 5,
  'missing': 1,
  'minimum': '0',
  'q1': '1',
  'median': '2',
  'q3': '3',
  'maximum': '100',
  'mean': '21.2',
  'lower_whisker': '0',
  'upper_whisker': '3',
  'outliers': ['100'],
};

void main() {
  testWidgets(
    'box plot exposes server statistics on mouse hover and selection',
    (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Center(
              child: SizedBox(width: 400, child: NutrientBoxPlot(stats: stats)),
            ),
          ),
        ),
      );
      final mouse = await tester.createGesture(kind: PointerDeviceKind.mouse);
      await mouse.addPointer(location: Offset.zero);
      await mouse.moveTo(tester.getCenter(find.byType(NutrientBoxPlot)));
      await tester.pumpAndSettle();
      await tester.pump(const Duration(seconds: 1));
      expect(find.text(distributionDetails(stats)), findsOneWidget);
      await mouse.removePointer();
      await tester.tap(find.byType(NutrientBoxPlot));
      await tester.pumpAndSettle();
      expect(find.text('Composition statistics'), findsOneWidget);
    },
  );

  testWidgets('narrow analytics supports filters, search, and error recovery', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    var fail = true;
    final paths = <String>[];
    final api = NutriApi(
      client: MockClient((request) async {
        paths.add(request.url.toString());
        if (request.url.path.endsWith('/food-sources')) {
          return http.Response('[]', 200);
        }
        if (fail) return http.Response('{"detail":"Test offline"}', 503);
        return http.Response(
          jsonEncode({
            'food_count': 1,
            'nutrients': [stats],
            'foods': [
              {'name': 'Test food', 'source_code': 'TEST', 'nutrients': []},
            ],
            'method': 'v1',
            'method_description': 'Test method',
          }),
          200,
        );
      }),
    );
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: CompositionAnalyticsPage(api: api),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.textContaining('Test offline'), findsOneWidget);
    fail = false;
    await tester.tap(find.text('Try again'));
    await tester.pumpAndSettle();
    expect(find.text('Distribution by nutrient'), findsOneWidget);
    expect(tester.takeException(), isNull);
    expect(find.text('Open plate builder bubbles'), findsOneWidget);
    expect(paths.any((p) => p.contains('source_kind=real')), isTrue);
    expect(tester.takeException(), isNull);
  });
}
