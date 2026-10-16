import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:nutritwin_mobile/intake_alerts.dart';

void main() {
  testWidgets(
    'alerts use API bands, show uncertainty and expose the selected trace',
    (tester) async {
      dynamic inspected;
      final iron = {
        'nutrient_code': 'iron',
        'risk': {'band': 'persistent', 'data_complete': false},
      };
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: IntakeAlerts(
              nutrients: [
                iron,
                {'nutrient_code': 'energy', 'risk': null},
                {
                  'nutrient_code': 'protein',
                  'risk': {'band': 'low'},
                },
              ],
              provisional: true,
              onInspect: (n) => inspected = n,
            ),
          ),
        ),
      );
      expect(find.text('Intake-gap alerts · DEMO targets'), findsOneWidget);
      expect(find.textContaining('Incomplete records'), findsOneWidget);
      expect(find.textContaining('protein ·'), findsNothing);
      await tester.tap(find.text('iron · persistent'));
      expect(inspected, same(iron));
    },
  );
  testWidgets('missing or low risk never becomes a gap alert', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: IntakeAlerts(
          nutrients: [
            {'nutrient_code': 'iron', 'risk': null},
            {
              'nutrient_code': 'protein',
              'risk': {'band': 'low'},
            },
          ],
          provisional: true,
          onInspect: (_) {},
        ),
      ),
    );
    expect(find.byType(Card), findsNothing);
  });
}
