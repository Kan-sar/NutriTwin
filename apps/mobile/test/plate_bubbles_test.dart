import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:nutritwin_mobile/plate_bubbles.dart';

void main() {
  testWidgets(
    'plate bubbles show ingredient amounts on hover and focused details on tap',
    (tester) async {
      final n = {
        'amount': '2',
        'canonical_unit': 'mg',
        'known_share_percent': '25',
      };
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: SingleChildScrollView(
              child: PlateBubbles(
                data: {
                  'ingredients': [
                    {
                      'food_id': 'a',
                      'name': 'Lentils',
                      'quantity_g': '50',
                      'source': 'TEST',
                      'nutrients': {'iron': n},
                    },
                  ],
                  'nutrients': {
                    'iron': {
                      'amount': '8',
                      'canonical_unit': 'mg',
                      'complete': false,
                    },
                  },
                },
              ),
            ),
          ),
        ),
      );
      final bubble = find.byType(Tooltip);
      final mouse = await tester.createGesture(kind: PointerDeviceKind.mouse);
      await mouse.addPointer(location: Offset.zero);
      await mouse.moveTo(tester.getCenter(bubble));
      await tester.pumpAndSettle();
      await tester.pump(const Duration(seconds: 1));
      expect(
        find.textContaining('Share of known meal total: 25.00%'),
        findsOneWidget,
      );
      await mouse.removePointer();
      await tester.tap(bubble);
      await tester.pumpAndSettle();
      expect(find.byType(SelectableText), findsOneWidget);
      expect(
        tester.widget<SelectableText>(find.byType(SelectableText)).data,
        contains('Incomplete composition'),
      );
      expect(tester.takeException(), isNull);
    },
  );
}
