import 'dart:math' as math;

import 'package:flutter/material.dart';

class WeeklyChart extends StatelessWidget {
  final List<dynamic> series;
  final String unit;
  const WeeklyChart({super.key, required this.series, required this.unit});
  double? value(dynamic v) => double.tryParse('$v');
  @override
  Widget build(BuildContext context) {
    final days = series.skip(math.max(0, series.length - 7)).toList();
    final maximum = days.fold<double>(
      1,
      (m, d) => math.max(
        m,
        math.max(
          value(d['consumed']) ?? 0,
          value(d['estimated_effective']) ?? 0,
        ),
      ),
    );
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Last 7 days · logged intake'),
          const SizedBox(height: 12),
          Row(
            children: [
              for (final d in days)
                Expanded(
                  child: Tooltip(
                    message:
                        '${d['date']}: consumed ${d['consumed'] ?? 'unknown'}, estimated effective ${d['estimated_effective'] ?? 'unknown'} $unit',
                    child: Semantics(
                      label:
                          '${d['date']}: consumed ${d['consumed'] ?? 'unknown'} $unit; estimated effective ${d['estimated_effective'] ?? 'unknown'} $unit',
                      child: Column(
                        children: [
                          SizedBox(
                            height: 80,
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              crossAxisAlignment: CrossAxisAlignment.end,
                              children: [
                                for (final kind in [
                                  'consumed',
                                  'estimated_effective',
                                ])
                                  Padding(
                                    padding: const EdgeInsets.symmetric(
                                      horizontal: 2,
                                    ),
                                    child: value(d[kind]) == null
                                        ? const Text('—')
                                        : Container(
                                            width: 10,
                                            height:
                                                80 *
                                                (value(d[kind])! / maximum)
                                                    .clamp(0, 1),
                                            color: kind == 'consumed'
                                                ? const Color(0xFF4E79A7)
                                                : const Color(0xFF76B7B2),
                                          ),
                                  ),
                              ],
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            '${d['date']}'.substring(5),
                            style: Theme.of(context).textTheme.labelSmall,
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
            ],
          ),
          const SizedBox(height: 12),
          const Wrap(
            spacing: 16,
            children: [
              Text('Blue: consumed'),
              Text('Teal: estimated effective'),
              Text('— unknown'),
            ],
          ),
        ],
      ),
    );
  }
}
