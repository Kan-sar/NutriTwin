import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:nutritwin_mobile/dashboard_widgets.dart';
import 'package:nutritwin_mobile/intake_alerts.dart';
import 'package:nutritwin_mobile/dishes.dart';
import 'package:nutritwin_mobile/palettes.dart';

void main() {
  testWidgets(
    'workspace reflows without losing selection or unknown composition',
    (tester) async {
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      final data = {
        'nutrients': {
          'iron': {'amount': null, 'canonical_unit': 'mg', 'complete': false},
        },
        'ingredients': [
          {
            'name': 'A long ingredient name with preparation state and source attribution',
            'quantity_g': '125',
            'nutrients': {
              'iron': {'amount': null},
            },
          },
        ],
      };
      for (final size in [const Size(1280, 1000), const Size(390, 844)]) {
        tester.view.physicalSize = size;
        for (final palette in appPalettes) {
          await tester.pumpWidget(
            MaterialApp(
              theme: palette.theme,
              home: Scaffold(
                body: SingleChildScrollView(
                  child: Column(
                    children: [
                      const JournalSummaryCards(
                        mealsToday: 1,
                        loggedDays: 30,
                        alerts: 4,
                      ),
                      WorkspaceColumns(
                        primary: Text('Choose your food'),
                        secondary: Text('Your plate'),
                      ),
                      CompositionView(data: data),
                    ],
                  ),
                ),
              ),
            ),
          );
          await tester.pumpAndSettle();
          expect(find.text('Unknown mg'), findsOneWidget);
          expect(find.textContaining('No known share'), findsOneWidget);
          final left = tester.getTopLeft(find.text('Choose your food'));
          final right = tester.getTopLeft(find.text('Your plate'));
          if (size.width > 880) {
            expect(left.dy, right.dy);
            expect(right.dx, greaterThan(left.dx));
          } else {
            expect(right.dy, greaterThan(left.dy));
          }
          expect(
            tester.takeException(),
            isNull,
            reason: '${palette.name} at $size',
          );
        }
      }
    },
  );

  testWidgets(
    'risk details explain the supplied score and uncertainty on a phone',
    (tester) async {
      tester.view.physicalSize = const Size(390, 844);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: IntakeRiskDetails(
              provisional: true,
              nutrient: {
                'nutrient_code': 'iron',
                'risk': {
                  'score': '78.5208',
                  'band': 'persistent',
                  'data_complete': false,
                  'contributions': [
                    {'factor': 'gap_7d', 'points': '26.25'},
                  ],
                },
              },
            ),
          ),
        ),
      );
      expect(find.text('78.52 / 100 · persistent'), findsOneWidget);
      expect(find.text('Intake gap over 7 days'), findsOneWidget);
      expect(find.text('26.25 pts'), findsOneWidget);
      expect(
        find.textContaining('Missing values are not treated as zero'),
        findsOneWidget,
      );
      expect(tester.takeException(), isNull);
    },
  );
}
