import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:nutritwin_mobile/main.dart';

void main() {
  testWidgets('sign in is accessible and does not prefill credentials', (
    tester,
  ) async {
    await tester.pumpWidget(const NutriTwinApp());
    expect(find.text('NutriTwin'), findsOneWidget);
    expect(find.widgetWithText(FilledButton, 'Sign in'), findsOneWidget);
    final fields = tester
        .widgetList<TextField>(find.byType(TextField))
        .toList();
    expect(fields.map((f) => f.controller!.text), everyElement(isEmpty));
    expect(fields.last.obscureText, isTrue);
    await tester.tap(find.text('Create a Student or Adult account'));
    await tester.pumpAndSettle();
    expect(find.text('Account type'), findsOneWidget);
    expect(find.widgetWithText(FilledButton, 'Create account'), findsOneWidget);
    expect(find.text('admin'), findsNothing);
  });
}
