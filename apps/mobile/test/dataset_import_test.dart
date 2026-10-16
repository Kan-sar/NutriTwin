import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:nutritwin_mobile/api.dart';
import 'package:nutritwin_mobile/dataset_import.dart';

void main() {
  testWidgets(
    'import requires preview and editing invalidates the confirmation',
    (tester) async {
      tester.view.physicalSize = const Size(1000, 1400);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      final requests = <Map<String, dynamic>>[];
      final api = NutriApi(
        client: MockClient((r) async {
          final input = jsonDecode(r.body) as Map<String, dynamic>;
          requests.add(input);
          if (input['document'] == 'broken') {
            return http.Response(
              jsonEncode({'detail': 'source.code: required'}),
              422,
            );
          }
          return http.Response(
            jsonEncode({
              'source': 'Test source',
              'foods': 1,
              'new_foods': 1,
              'missing_values': 1,
              'sample_names': ['Test food'],
              'checksum': 'preview-hash',
            }),
            200,
          );
        }),
      );
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(body: DatasetImportDialog(api: api)),
        ),
      );
      expect(find.widgetWithText(FilledButton, 'Import dataset'), findsNothing);
      await tester.enterText(find.byType(TextField), 'first document');
      await tester.tap(find.text('Preview dataset'));
      await tester.pumpAndSettle();
      expect(requests.single['commit'], isNull);
      expect(find.text('Preview — nothing saved yet'), findsOneWidget);
      await tester.enterText(find.byType(TextField), 'broken');
      await tester.pumpAndSettle();
      expect(find.widgetWithText(FilledButton, 'Import dataset'), findsNothing);
      await tester.tap(find.text('Preview dataset'));
      await tester.pumpAndSettle();
      expect(find.text('source.code: required'), findsOneWidget);
      expect(find.widgetWithText(FilledButton, 'Import dataset'), findsNothing);
      await tester.enterText(find.byType(TextField), 'corrected document');
      await tester.tap(find.text('Preview dataset'));
      await tester.pumpAndSettle();
      await tester.tap(find.widgetWithText(FilledButton, 'Import dataset'));
      await tester.pumpAndSettle();
      expect(requests.last['commit'], true);
      expect(requests.last['preview_checksum'], 'preview-hash');
      expect(requests.last['document'], 'corrected document');
      expect(find.text('Import complete'), findsOneWidget);
      expect(tester.takeException(), isNull);
      api.dispose();
    },
  );
}
