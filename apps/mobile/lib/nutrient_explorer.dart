import 'dart:math' as math;

import 'package:flutter/material.dart';

const nutrientPalette = [
  Color(0xFF99CEC4),
  Color(0xFFF0BE83),
  Color(0xFFC8B5DA),
  Color(0xFFEAA7AA),
  Color(0xFFBFD49A),
  Color(0xFF9DC4DE),
];
String nutrientName(dynamic code) => '$code'.replaceAll('_', ' ');
double? numeric(dynamic value) => double.tryParse('$value');

/// Displays API-provided coverage; it does not calculate nutrient intake.
class NutrientExplorer extends StatefulWidget {
  final List<dynamic> nutrients;
  final ValueChanged<String?> onSelected;
  const NutrientExplorer({
    super.key,
    required this.nutrients,
    required this.onSelected,
  });
  @override
  State<NutrientExplorer> createState() => _NutrientExplorerState();
}

class _NutrientExplorerState extends State<NutrientExplorer> {
  String? selected;
  String window = 'daily';
  bool targets = false;
  void select(String? code) {
    setState(() => selected = code);
    widget.onSelected(code);
  }

  @override
  Widget build(BuildContext context) => Card(
    child: Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Your nutrient landscape',
            style: Theme.of(context).textTheme.headlineSmall,
          ),
          const SizedBox(height: 8),
          const Text(
            'Explore your logged intake. Select a nutrient to bring its history into focus.',
          ),
          const SizedBox(height: 20),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              for (final entry in {
                'daily': 'Today',
                'rolling_7_day': '7 days',
                'rolling_30_day': '30 days',
              }.entries)
                ChoiceChip(
                  label: Text(entry.value),
                  selected: window == entry.key,
                  onSelected: (_) => setState(() => window = entry.key),
                ),
              FilterChip(
                label: const Text('Target bars'),
                selected: targets,
                onSelected: (v) => setState(() => targets = v),
              ),
            ],
          ),
          const SizedBox(height: 24),
          if (widget.nutrients.isEmpty)
            const Text('No nutrient data yet. Add a meal to begin exploring.'),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.surfaceContainerHighest,
              borderRadius: BorderRadius.circular(28),
            ),
            child: targets
                ? Column(
                    children: [
                      for (int i = 0; i < widget.nutrients.length; i++)
                        targetRow(widget.nutrients[i], i),
                    ],
                  )
                : Wrap(
                    alignment: WrapAlignment.center,
                    crossAxisAlignment: WrapCrossAlignment.center,
                    spacing: 14,
                    runSpacing: 14,
                    children: [
                      for (int i = 0; i < widget.nutrients.length; i++)
                        bubble(widget.nutrients[i], i),
                    ],
                  ),
          ),
          const SizedBox(height: 16),
          Text(
            'Consumed intake / reference target · not estimated effective intake.\nBubble size is a visual guide capped at 100%; labels show full coverage. Unknown values are unfilled. Incomplete totals may be lower bounds.',
            style: TextStyle(
              fontSize: 12,
              color: Theme.of(context).colorScheme.onSurface,
            ),
          ),
          const SizedBox(height: 16),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              ChoiceChip(
                label: const Text('All nutrients'),
                selected: selected == null,
                onSelected: (_) => select(null),
              ),
              for (final n in widget.nutrients)
                ChoiceChip(
                  label: Text(nutrientName(n['nutrient_code'])),
                  selected: selected == n['nutrient_code'],
                  onSelected: (_) => select(
                    selected == n['nutrient_code'] ? null : n['nutrient_code'],
                  ),
                ),
            ],
          ),
        ],
      ),
    ),
  );

  double? coverage(dynamic n) =>
      numeric(n['consumed']?[window]?['coverage_percent']);
  String amount(dynamic n) =>
      coverage(n) == null ? 'Unknown' : '${coverage(n)!.toStringAsFixed(1)}%';
  Widget bubble(dynamic n, int index) {
    final percent = coverage(n);
    final diameter =
        (140 + 44 * math.sqrt((percent ?? 0).clamp(0, 100) / 100)) *
        MediaQuery.textScalerOf(context).scale(14) /
        14;
    final active = selected == null || selected == n['nutrient_code'];
    final description =
        '${nutrientName(n['nutrient_code'])}: ${amount(n)} target coverage';
    return Tooltip(
      message: '$description. Select to inspect history.',
      child: Semantics(
        label: description,
        selected: selected == n['nutrient_code'],
        child: AnimatedOpacity(
          duration: const Duration(milliseconds: 180),
          opacity: active ? 1 : .42,
          child: SizedBox(
            width: diameter,
            height: diameter,
            child: OutlinedButton(
              style: OutlinedButton.styleFrom(
                padding: const EdgeInsets.all(12),
                shape: const CircleBorder(),
                foregroundColor: const Color(0xFF203E34),
                backgroundColor: percent == null
                    ? Colors.white
                    : nutrientPalette[index % nutrientPalette.length],
                side: BorderSide(
                  color: selected == n['nutrient_code']
                      ? const Color(0xFF244F3D)
                      : Colors.transparent,
                  width: 3,
                ),
              ),
              onPressed: () => select(
                selected == n['nutrient_code'] ? null : n['nutrient_code'],
              ),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    nutrientName(n['nutrient_code']),
                    textAlign: TextAlign.center,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontWeight: FontWeight.w600),
                  ),
                  const SizedBox(height: 5),
                  Text(amount(n)),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget targetRow(dynamic n, int index) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 10),
    child: InkWell(
      onTap: () => select(n['nutrient_code']),
      child: Column(
        children: [
          Row(
            children: [
              Expanded(child: Text(nutrientName(n['nutrient_code']))),
              Text(amount(n)),
            ],
          ),
          const SizedBox(height: 8),
          if (coverage(n) != null)
            LinearProgressIndicator(
              value: (coverage(n)! / 100).clamp(0, 1),
              minHeight: 10,
              borderRadius: BorderRadius.circular(8),
              color: nutrientPalette[index % nutrientPalette.length],
              backgroundColor: Colors.white,
              semanticsLabel:
                  '${nutrientName(n['nutrient_code'])} target coverage',
              semanticsValue: amount(n),
            )
          else
            const Align(
              alignment: Alignment.centerLeft,
              child: Text(
                'No coverage available',
                style: TextStyle(fontSize: 12),
              ),
            ),
        ],
      ),
    ),
  );
}

class FoodNutrientExplorer extends StatefulWidget {
  final List<dynamic> foods;
  final ValueChanged<dynamic>? onAdd;
  final ValueChanged<dynamic> onInspect;
  const FoodNutrientExplorer({
    super.key,
    required this.foods,
    required this.onAdd,
    required this.onInspect,
  });
  @override
  State<FoodNutrientExplorer> createState() => _FoodNutrientExplorerState();
}

class _FoodNutrientExplorerState extends State<FoodNutrientExplorer> {
  String? focus;
  @override
  Widget build(BuildContext context) {
    final codes = <String>{
      for (final f in widget.foods)
        for (final n in f['nutrients']) '${n['nutrient_code']}',
    }.toList()..sort();
    final selected = codes.contains(focus) ? focus : codes.firstOrNull;
    dynamic nutrient(dynamic f) => (f['nutrients'] as List)
        .where((n) => n['nutrient_code'] == selected)
        .firstOrNull;
    double? amount(dynamic f) => numeric(nutrient(f)?['amount_per_100g']);
    final ranked = List<dynamic>.from(widget.foods)
      ..sort((a, b) => (amount(b) ?? -1).compareTo(amount(a) ?? -1));
    final maximum = ranked.fold<double>(
      1,
      (m, f) => math.max(m, amount(f) ?? 0),
    );
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Food nutrient explorer',
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const Text(
          'Compare foods per 100 g. Select a food name for composition, or Add food to start a draft.',
        ),
        const SizedBox(height: 12),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            for (final code in codes)
              ChoiceChip(
                label: Text(nutrientName(code)),
                selected: selected == code,
                onSelected: (_) => setState(() => focus = code),
              ),
          ],
        ),
        for (final food in ranked)
          ListTile(
            contentPadding: EdgeInsets.zero,
            title: Text(food['name']),
            onTap: () => widget.onInspect(food),
            subtitle: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '${food['source_code']} · ${amount(food) == null ? 'Unknown' : '${amount(food)!.toStringAsFixed(2)} ${nutrient(food)?['unit'] ?? ''}'} per 100 g',
                ),
                if (amount(food) != null)
                  Padding(
                    padding: const EdgeInsets.only(top: 6),
                    // The adjacent text carries the quantity. A progress role on
                    // this decorative bar can hide the row's actions on Web.
                    child: ExcludeSemantics(
                      child: LinearProgressIndicator(
                        value: (amount(food)! / maximum).clamp(0, 1),
                        minHeight: 6,
                      ),
                    ),
                  ),
              ],
            ),
            trailing: Semantics(
              container: true,
              child: Tooltip(
                message: 'Add ${food['name']} to draft',
                child: TextButton.icon(
                  onPressed: widget.onAdd == null
                      ? null
                      : () => widget.onAdd!(food),
                  icon: const Icon(Icons.add_circle_outline),
                  label: const Text('Add food'),
                ),
              ),
            ),
          ),
      ],
    );
  }
}
