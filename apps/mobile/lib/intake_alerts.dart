import 'package:flutter/material.dart';

/// Displays existing model output; never calculates or diagnoses a deficiency.
class IntakeAlerts extends StatelessWidget {
  final List<dynamic> nutrients;
  final bool provisional;
  final void Function(dynamic nutrient) onInspect;
  const IntakeAlerts({
    super.key,
    required this.nutrients,
    required this.provisional,
    required this.onInspect,
  });

  @override
  Widget build(BuildContext context) {
    final flagged = nutrients
        .where(
          (n) =>
              n['risk'] != null &&
              ['watch', 'elevated', 'persistent'].contains(n['risk']['band']),
        )
        .toList();
    if (flagged.isEmpty) return const SizedBox.shrink();
    final colors = Theme.of(context).colorScheme;
    return Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Intake-gap alerts${provisional ? ' · DEMO targets' : ''}',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 8),
            const Text(
              'Based on recorded intake over 7 and 30 days. These indications are not deficiency diagnoses.',
            ),
            for (final n in flagged)
              ListTile(
                contentPadding: EdgeInsets.zero,
                leading: Icon(Icons.info_outline, color: colors.primary),
                title: Text(
                  '${(n['nutrient_code'] as String).replaceAll('_', ' ')} · ${n['risk']['band']}',
                ),
                subtitle: Text(
                  n['risk']['data_complete'] == true
                      ? 'Below the selected reference. View factors.'
                      : 'Incomplete records: missing meals or nutrient values increase uncertainty.',
                ),
                trailing: const Icon(Icons.chevron_right),
                onTap: () => onInspect(n),
              ),
            const Text(
              'Select an alert to inspect the score and its contributing factors.',
            ),
          ],
        ),
      ),
    );
  }
}

class IntakeRiskDetails extends StatelessWidget {
  final dynamic nutrient;
  final bool provisional;
  const IntakeRiskDetails({
    super.key,
    required this.nutrient,
    required this.provisional,
  });

  static const factorNames = {
    'gap_7d': 'Intake gap over 7 days',
    'gap_30d': 'Intake gap over 30 days',
    'duration': 'Duration of the recorded gap',
    'declining_trend': 'Declining intake trend',
    'missing_log_uncertainty': 'Missing meal records',
    'upper_limit_exposure': 'Upper-limit contribution',
  };

  String value(dynamic v) =>
      num.tryParse('$v')?.toStringAsFixed(2) ?? 'Unknown';

  @override
  Widget build(BuildContext context) {
    final risk = nutrient['risk'];
    return AlertDialog(
      title: Text(
        'Intake-gap indication: ${(nutrient['nutrient_code'] as String).replaceAll('_', ' ')}',
      ),
      content: SizedBox(
        width: 520,
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                '${value(risk['score'])} / 100 · ${risk['band']}',
                style: Theme.of(context).textTheme.headlineSmall,
              ),
              const SizedBox(height: 12),
              Text(
                provisional
                    ? 'DEMO targets. This score describes recorded intake gaps; it does not diagnose deficiency.'
                    : 'This score describes recorded intake gaps; it does not diagnose deficiency.',
              ),
              const SizedBox(height: 20),
              const Text(
                'What contributes to this score',
                style: TextStyle(fontWeight: FontWeight.w600),
              ),
              const SizedBox(height: 8),
              for (final factor in risk['contributions'] ?? [])
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 10),
                  child: Row(
                    children: [
                      Expanded(
                        child: Text(
                          factorNames[factor['factor']] ??
                              '${factor['factor']}'.replaceAll('_', ' '),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Text('${value(factor['points'])} pts'),
                    ],
                  ),
                ),
              const Divider(),
              Text(
                risk['data_complete'] == true
                    ? 'The model has values for the recorded 30-day window. Unrecorded meals can still affect interpretation.'
                    : 'Incomplete records or composition increase uncertainty. Missing values are not treated as zero intake.',
              ),
            ],
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Close'),
        ),
      ],
    );
  }
}
