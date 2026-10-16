import 'package:flutter/material.dart';

/// Shows one nutrient's existing stats without changing the API values.
class NutrientStatsSelector extends StatefulWidget {
  final List<dynamic> nutrients;
  final Widget Function(dynamic nutrient) statsBuilder;
  const NutrientStatsSelector({
    super.key,
    required this.nutrients,
    required this.statsBuilder,
  });

  @override
  State<NutrientStatsSelector> createState() => _NutrientStatsSelectorState();
}

class _NutrientStatsSelectorState extends State<NutrientStatsSelector> {
  String? selectedCode;

  @override
  Widget build(BuildContext context) {
    final selected =
        widget.nutrients
            .where((n) => n['nutrient_code'] == selectedCode)
            .firstOrNull ??
        widget.nutrients.firstOrNull;
    final code = selected?['nutrient_code'] as String?;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Nutrient stats',
          style: Theme.of(context).textTheme.headlineSmall,
        ),
        const SizedBox(height: 8),
        const Text(
          'Choose a nutrient to see its intake, target coverage and history.',
        ),
        const SizedBox(height: 16),
        DropdownButtonFormField<String>(
          key: ValueKey(code),
          initialValue: code,
          isExpanded: true,
          decoration: const InputDecoration(labelText: 'Nutrient'),
          hint: const Text('Choose a nutrient'),
          items: [
            for (final nutrient in widget.nutrients)
              DropdownMenuItem(
                value: nutrient['nutrient_code'] as String,
                child: Text(
                  (nutrient['nutrient_code'] as String).replaceAll('_', ' '),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
          ],
          onChanged: widget.nutrients.isEmpty
              ? null
              : (value) => setState(() => selectedCode = value),
        ),
        const SizedBox(height: 16),
        if (selected != null)
          widget.statsBuilder(selected)
        else
          Text(
            widget.nutrients.isEmpty
                ? 'No nutrient data is available yet.'
                : 'Your selected nutrient’s stats will appear here.',
          ),
      ],
    );
  }
}
