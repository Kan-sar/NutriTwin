import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:nutritwin_mobile/nutrient_stats_selector.dart';

void main() {
  testWidgets(
    'only the selected nutrient is rendered and refreshed values are used',
    (tester) async {
      var nutrients = <dynamic>[
        {'nutrient_code': 'iron', 'value': '3 mg'},
        {'nutrient_code': 'vitamin_c', 'value': 'Unknown'},
      ];
      Widget view() => MaterialApp(
        home: Scaffold(
          body: NutrientStatsSelector(
            nutrients: nutrients,
            statsBuilder: (n) =>
                Text('Stats: ${n['nutrient_code']} ${n['value']}'),
          ),
        ),
      );
      await tester.pumpWidget(view());
      expect(find.text('Stats: iron 3 mg'), findsOneWidget);
      await tester.tap(find.byType(DropdownButtonFormField<String>));
      await tester.pumpAndSettle();
      await tester.tap(find.text('iron').last);
      await tester.pumpAndSettle();
      expect(find.text('Stats: iron 3 mg'), findsOneWidget);
      expect(find.textContaining('Stats: vitamin_c'), findsNothing);
      await tester.tap(find.byType(DropdownButtonFormField<String>));
      await tester.pumpAndSettle();
      await tester.tap(find.text('vitamin c').last);
      await tester.pumpAndSettle();
      expect(find.text('Stats: vitamin_c Unknown'), findsOneWidget);
      expect(find.textContaining('Stats: iron'), findsNothing);
      nutrients = [
        {'nutrient_code': 'vitamin_c', 'value': '20 mg'},
      ];
      await tester.pumpWidget(view());
      await tester.pumpAndSettle();
      expect(find.text('Stats: vitamin_c 20 mg'), findsOneWidget);
      nutrients = [];
      await tester.pumpWidget(view());
      await tester.pumpAndSettle();
      expect(find.text('No nutrient data is available yet.'), findsOneWidget);
      expect(find.textContaining('Stats:'), findsNothing);
      expect(tester.takeException(), isNull);
    },
  );
}
