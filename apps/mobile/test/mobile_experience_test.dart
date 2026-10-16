import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:nutritwin_mobile/mobile_experience.dart';
import 'package:nutritwin_mobile/palettes.dart';

void main() {
  void phone(WidgetTester tester) {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
  }

  testWidgets('phone navigation opens every destination and add action', (
    tester,
  ) async {
    phone(tester);
    int? destination;
    var added = false;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          bottomNavigationBar: MobileBottomBar(
            page: 0,
            onOpen: (p) => destination = p,
            onAdd: () => added = true,
          ),
        ),
      ),
    );
    for (final entry in {
      'Discover': 0,
      'Diary': 1,
      'Foods': 5,
      'More': 8,
    }.entries) {
      await tester.tap(find.text(entry.key));
      expect(destination, entry.value);
    }
    await tester.tap(find.byTooltip('Add to diary'));
    expect(added, isTrue);
    expect(tester.takeException(), isNull);
  });

  testWidgets('diary filters dates, edits the selected entry and changes day', (
    tester,
  ) async {
    phone(tester);
    dynamic edited;
    String? date;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SingleChildScrollView(
            child: MobileDiary(
              meals: [
                {
                  'id': '1',
                  'name': 'Breakfast oats',
                  'local_date': '2026-10-15',
                  'ingredients': [],
                  'eaten_at': '2026-10-15T08:00:00',
                },
                {
                  'id': '2',
                  'name': 'Yesterday rice',
                  'local_date': '2026-10-14',
                  'ingredients': [],
                  'eaten_at': '2026-10-14T12:00:00',
                },
              ],
              selectedDay: '2026-10-15',
              onDate: (d) => date = d,
              onAdd: () {},
              onEdit: (m) => edited = m,
              onManage: () {},
            ),
          ),
        ),
      ),
    );
    expect(find.text('Breakfast oats'), findsOneWidget);
    expect(find.text('Yesterday rice'), findsNothing);
    await tester.tap(find.text('Breakfast oats'));
    expect(edited['id'], '1');
    await tester.tap(find.byTooltip('Previous day'));
    expect(date, '2026-10-14');
    expect(tester.takeException(), isNull);
  });

  testWidgets('server rejects credentials, paths and invalid schemes', (
    tester,
  ) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(body: ServerDialog(initial: 'http://10.0.2.2:8000')),
      ),
    );
    for (final url in [
      'file:///secret',
      'https://user:pass@example.com',
      'https://example.com/api/v1',
    ]) {
      await tester.enterText(find.byType(TextField), url);
      await tester.tap(find.text('Save'));
      await tester.pump();
      expect(
        find.text('Use an http(s) origin without a path or credentials.'),
        findsOneWidget,
      );
    }
  });

  testWidgets('dashboard shows missing values and a clear demo label', (
    tester,
  ) async {
    phone(tester);
    await tester.pumpWidget(
      MaterialApp(
        theme: paletteById('mobile').theme,
        home: Scaffold(
          appBar: AppBar(
            title: const Text('NutriTwin'),
            bottom: PreferredSize(
              preferredSize: const Size.fromHeight(48),
              child: MobileDiscoverTabs(page: 0, onOpen: (_) {}),
            ),
          ),
          bottomNavigationBar: MobileBottomBar(
            page: 0,
            onOpen: (_) {},
            onAdd: () {},
          ),
          body: SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: MobileDashboard(
              summary: {
                'as_of_date': '2026-10-16',
                'target_provisional': true,
                'nutrients': [],
              },
              meals: const [],
              onOpen: (_) {},
              onAdd: () {},
            ),
          ),
        ),
      ),
    );
    expect(find.text('Unavailable'), findsNWidgets(4));
    expect(find.textContaining('DEMO TARGETS'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
