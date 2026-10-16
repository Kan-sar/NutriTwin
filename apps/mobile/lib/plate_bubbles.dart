import 'dart:math' as math;

import 'package:flutter/material.dart';

/// Workbook-inspired nutrient circles on a plate, using server-provided shares.
class PlateBubbles extends StatefulWidget {
  final Map<String, dynamic> data;
  const PlateBubbles({super.key, required this.data});
  @override
  State<PlateBubbles> createState() => _PlateBubblesState();
}

class _PlateBubblesState extends State<PlateBubbles> {
  int ingredient = 0;
  String? focus;
  static const colors = [
    Color(0xff4279a8),
    Color(0xffbd6745),
    Color(0xff4d8662),
    Color(0xff8a66af),
    Color(0xffb64d79),
    Color(0xff568b94),
    Color(0xff7c733b),
    Color(0xffad5260),
    Color(0xff54729c),
    Color(0xff607b4b),
    Color(0xff905e94),
    Color(0xff8c6950),
  ];
  String number(dynamic value) =>
      double.tryParse('$value')?.toStringAsFixed(2) ?? 'Unknown';
  @override
  Widget build(BuildContext context) {
    final rows = (widget.data['ingredients'] as List?) ?? [];
    if (rows.isEmpty) return const Text('Add ingredients to build your plate.');
    if (ingredient >= rows.length) ingredient = 0;
    final row = rows[ingredient];
    final ns = Map<String, dynamic>.from(row['nutrients'] ?? {});
    final codes = ns.keys.toList()..sort();
    String detail(String code) {
      final n = ns[code];
      return '${row['name']} · ${number(row['quantity_g'])} g\n${code.replaceAll('_', ' ')}: ${number(n['amount'])} ${n['canonical_unit']}\n'
          'Share of known meal total: ${n['known_share_percent'] == null ? 'Unavailable' : '${number(n['known_share_percent'])}%'}\n'
          'Meal total: ${number(widget.data['nutrients']?[code]?['amount'])} ${n['canonical_unit']}\n'
          '${widget.data['nutrients']?[code]?['complete'] == true ? 'Complete composition for this nutrient' : 'Incomplete composition; shares cover known contributions only'}\nSource: ${row['source'] ?? 'Unavailable'}';
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Plate builder · nutrient bubbles',
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const SizedBox(height: 8),
        const Text(
          'Choose an ingredient to explore its nutrient bubbles. Hover for amounts and select a nutrient to focus the plate.',
        ),
        const SizedBox(height: 16),
        DropdownButtonFormField<int>(
          key: ValueKey('${rows.map((r) => r['food_id']).join()}:$ingredient'),
          initialValue: ingredient,
          isExpanded: true,
          decoration: const InputDecoration(
            labelText: 'Ingredient on the plate',
          ),
          items: [
            for (var i = 0; i < rows.length; i++)
              DropdownMenuItem(
                value: i,
                child: Text(
                  '${rows[i]['name']} · ${number(rows[i]['quantity_g'])} g',
                  overflow: TextOverflow.ellipsis,
                ),
              ),
          ],
          onChanged: (v) => setState(() {
            ingredient = v!;
            focus = null;
          }),
        ),
        const SizedBox(height: 16),
        LayoutBuilder(
          builder: (context, box) {
            final size = math.min(box.maxWidth, 400.0);
            final scale = size / 400;
            return Center(
              child: Container(
                width: size,
                height: size,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: Theme.of(context).colorScheme.surface,
                  border: Border.all(
                    color: Theme.of(context).colorScheme.outlineVariant,
                    width: 12 * scale,
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withValues(alpha: .08),
                      blurRadius: 16,
                      offset: const Offset(0, 4),
                    ),
                  ],
                ),
                child: Stack(
                  alignment: Alignment.center,
                  children: [
                    for (var i = 0; i < codes.length; i++)
                      Builder(
                        builder: (context) {
                          final code = codes[i], n = ns[code];
                          final share = double.tryParse(
                            '${n['known_share_percent']}',
                          );
                          final diameter = share == null || share == 0
                              ? 16.0
                              : math.max(
                                  10.0,
                                  70 * math.sqrt(share.clamp(0, 100) / 100),
                                );
                          // Fixed non-overlapping plate positions; size is a visual encoding only.
                          final col = i % 3, line = i ~/ 3;
                          final y =
                              (line -
                                  (math.max(1, (codes.length / 3).ceil()) - 1) /
                                      2) *
                              78;
                          return Positioned(
                            left:
                                (size - 24 * scale) / 2 +
                                (col - 1) * 86 * scale -
                                37 * scale,
                            top:
                                (size - 24 * scale) / 2 +
                                y * scale -
                                37 * scale,
                            child: Tooltip(
                              message: detail(code),
                              child: SizedBox(
                                width: 74 * scale,
                                height: 74 * scale,
                                child: InkWell(
                                  customBorder: const CircleBorder(),
                                  onTap: () => setState(
                                    () => focus = focus == code ? null : code,
                                  ),
                                  child: Semantics(
                                    button: true,
                                    label: detail(code),
                                    child: Center(
                                      child: AnimatedOpacity(
                                        duration: const Duration(
                                          milliseconds: 150,
                                        ),
                                        opacity: focus == null || focus == code
                                            ? 1
                                            : .2,
                                        child: Container(
                                          width: diameter * scale,
                                          height: diameter * scale,
                                          decoration: BoxDecoration(
                                            shape: BoxShape.circle,
                                            color: share == null || share == 0
                                                ? Colors.transparent
                                                : colors[i % colors.length],
                                            border: Border.all(
                                              color: colors[i % colors.length],
                                              width: 2,
                                            ),
                                          ),
                                          child: diameter >= 44
                                              ? Center(
                                                  child: Text(
                                                    code == 'carbohydrate'
                                                        ? 'carbs'
                                                        : code.replaceAll(
                                                            'vitamin_',
                                                            'vit ',
                                                          ),
                                                    textAlign: TextAlign.center,
                                                    style: TextStyle(
                                                      color: Colors.white,
                                                      fontSize: 9 * scale,
                                                      fontWeight:
                                                          FontWeight.w700,
                                                    ),
                                                  ),
                                                )
                                              : null,
                                        ),
                                      ),
                                    ),
                                  ),
                                ),
                              ),
                            ),
                          );
                        },
                      ),
                  ],
                ),
              ),
            );
          },
        ),
        const SizedBox(height: 16),
        const Text(
          'Area represents this ingredient’s share of each nutrient’s known meal total, not RDA coverage. Tiny values have a minimum marker; outlined circles mean zero or unavailable share. Colors identify nutrients.',
          style: TextStyle(fontSize: 12),
        ),
        const SizedBox(height: 12),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            for (var i = 0; i < codes.length; i++)
              FilterChip(
                avatar: CircleAvatar(
                  backgroundColor: colors[i % colors.length],
                  radius: 6,
                ),
                label: Text(codes[i].replaceAll('_', ' ')),
                selected: focus == codes[i],
                onSelected: (_) =>
                    setState(() => focus = focus == codes[i] ? null : codes[i]),
              ),
          ],
        ),
        if (focus != null && ns.containsKey(focus))
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 16),
            child: SelectableText(detail(focus!)),
          ),
      ],
    );
  }
}
