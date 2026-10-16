import 'package:flutter/material.dart';

/// Arranges related controls together on desktop and in reading order on phones.
class WorkspaceColumns extends StatelessWidget {
  final Widget primary, secondary;
  final double breakpoint;
  final int primaryFlex, secondaryFlex;
  const WorkspaceColumns({
    super.key,
    required this.primary,
    required this.secondary,
    this.breakpoint = 880,
    this.primaryFlex = 3,
    this.secondaryFlex = 2,
  });

  @override
  Widget build(BuildContext context) => LayoutBuilder(
    builder: (context, constraints) => constraints.maxWidth >= breakpoint
        ? Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(flex: primaryFlex, child: primary),
              const SizedBox(width: 24),
              Expanded(flex: secondaryFlex, child: secondary),
            ],
          )
        : Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [primary, const SizedBox(height: 20), secondary],
          ),
  );
}

class WorkspacePanel extends StatelessWidget {
  final Widget child;
  const WorkspacePanel({super.key, required this.child});
  @override
  Widget build(BuildContext context) => Card(
    margin: EdgeInsets.zero,
    child: SizedBox(
      width: double.infinity,
      child: Padding(padding: const EdgeInsets.all(20), child: child),
    ),
  );
}

class JournalSummaryCards extends StatelessWidget {
  final int mealsToday, loggedDays, alerts;
  const JournalSummaryCards({
    super.key,
    required this.mealsToday,
    required this.loggedDays,
    required this.alerts,
  });

  @override
  Widget build(BuildContext context) => LayoutBuilder(
    builder: (context, box) {
      final width = box.maxWidth >= 650
          ? (box.maxWidth - 24) / 3
          : box.maxWidth;
      return Wrap(
        spacing: 12,
        runSpacing: 12,
        children: [
          for (final item in [
            (
              Icons.restaurant_outlined,
              'Meals today',
              '$mealsToday',
              'Saved in your journal',
            ),
            (
              Icons.calendar_month_outlined,
              'Days recorded',
              '$loggedDays / 30',
              'Meal records, not a completeness score',
            ),
            (
              Icons.info_outline,
              'Intake-gap alerts',
              '$alerts',
              'Against the selected reference targets',
            ),
          ])
            SizedBox(
              width: width,
              child: WorkspacePanel(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(
                          item.$1,
                          size: 20,
                          color: Theme.of(context).colorScheme.primary,
                        ),
                        const SizedBox(width: 8),
                        Expanded(child: Text(item.$2)),
                      ],
                    ),
                    const SizedBox(height: 10),
                    Text(
                      item.$3,
                      style: Theme.of(context).textTheme.headlineMedium,
                    ),
                    const SizedBox(height: 4),
                    Text(item.$4, style: Theme.of(context).textTheme.bodySmall),
                  ],
                ),
              ),
            ),
        ],
      );
    },
  );
}

class PlateSteps extends StatelessWidget {
  final int active;
  const PlateSteps({super.key, required this.active});
  @override
  Widget build(BuildContext context) => Wrap(
    spacing: 8,
    runSpacing: 8,
    children: [
      for (final (i, title) in [
        'Choose a food',
        'Adjust your portion',
        'Log to your profile',
      ].indexed)
        Chip(
          avatar: Icon(
            i < active ? Icons.check_circle_outline : Icons.circle_outlined,
            size: 18,
            color: Theme.of(context).colorScheme.primary,
          ),
          label: Text('${i + 1}. $title'),
          backgroundColor: i == active
              ? Theme.of(context).colorScheme.primaryContainer
              : null,
        ),
    ],
  );
}
