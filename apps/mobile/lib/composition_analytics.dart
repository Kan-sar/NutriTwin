import 'dart:math' as math;

import 'package:flutter/material.dart';

import 'api.dart';
import 'dashboard_widgets.dart';

String _name(dynamic code) => '$code'.replaceAll('_', ' ');
double? _number(dynamic value) => double.tryParse('$value');
String _format(dynamic value) =>
    _number(value)?.toStringAsFixed(2) ?? 'Unknown';

/// Server-supplied descriptive statistics; the client only draws geometry.
class CompositionAnalyticsPage extends StatefulWidget {
  final NutriApi api;
  final VoidCallback? onOpenPlateBuilder;
  const CompositionAnalyticsPage({
    super.key,
    required this.api,
    this.onOpenPlateBuilder,
  });
  @override
  State<CompositionAnalyticsPage> createState() =>
      _CompositionAnalyticsPageState();
}

class _CompositionAnalyticsPageState extends State<CompositionAnalyticsPage> {
  Map<String, dynamic>? data;
  List<dynamic> sources = [];
  String source = 'real';
  String? error;
  bool loading = true;
  int generation = 0;
  @override
  void initState() {
    super.initState();
    load();
  }

  Future<void> load() async {
    final request = ++generation;
    setState(() {
      loading = true;
      error = null;
    });
    try {
      final results = await Future.wait([
        widget.api.request(
          'GET',
          '/analytics/composition?source_kind=${source == 'demo' ? 'demo' : 'real'}${source == 'real' || source == 'demo' ? '' : '&source_code=${Uri.encodeQueryComponent(source)}'}',
        ),
        widget.api.request('GET', '/food-sources'),
      ]);
      if (!mounted || generation != request) return;
      setState(() {
        data = Map<String, dynamic>.from(results[0]);
        sources = results[1];
        loading = false;
      });
    } catch (e) {
      if (!mounted || generation != request) return;
      setState(() {
        error = '$e';
        loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final nutrients = (data?['nutrients'] as List?) ?? [];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Nutrient analytics', style: theme.textTheme.headlineMedium),
        const SizedBox(height: 6),
        const Text(
          'Explore composition across the food catalogue. Every comparison uses 100 g of food.',
        ),
        const SizedBox(height: 24),
        WorkspacePanel(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Wrap(
                spacing: 16,
                runSpacing: 12,
                crossAxisAlignment: WrapCrossAlignment.center,
                children: [
                  SizedBox(
                    width: math.min(300, MediaQuery.sizeOf(context).width - 88),
                    child: DropdownButtonFormField<String>(
                      initialValue: source,
                      isExpanded: true,
                      decoration: const InputDecoration(
                        labelText: 'Dataset',
                        prefixIcon: Icon(Icons.storage_outlined),
                      ),
                      items: [
                        const DropdownMenuItem(
                          value: 'real',
                          child: Text('All source-backed foods'),
                        ),
                        const DropdownMenuItem(
                          value: 'demo',
                          child: Text('DEMO · synthetic foods'),
                        ),
                        for (final s in sources.where(
                          (s) => s['synthetic'] != true,
                        ))
                          DropdownMenuItem(
                            value: '${s['code']}',
                            child: Text(
                              '${s['code']}',
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                      ],
                      onChanged: loading
                          ? null
                          : (value) {
                              if (value == null) return;
                              setState(() => source = value);
                              load();
                            },
                    ),
                  ),
                  OutlinedButton.icon(
                    onPressed: loading ? null : load,
                    icon: const Icon(Icons.refresh, size: 18),
                    label: const Text('Refresh data'),
                  ),
                  Chip(
                    avatar: Icon(
                      source == 'demo'
                          ? Icons.science_outlined
                          : Icons.dataset_outlined,
                      size: 16,
                    ),
                    label: Text(
                      source == 'demo'
                          ? 'Synthetic demonstration'
                          : 'Catalogue composition',
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              const Text(
                'Food records are equally weighted. These plots describe the installed dataset, not your intake or a recommended diet.',
                style: TextStyle(fontSize: 12),
              ),
            ],
          ),
        ),
        const SizedBox(height: 20),
        if (loading)
          const Padding(
            padding: EdgeInsets.all(32),
            child: Center(
              child: CircularProgressIndicator(
                semanticsLabel: 'Loading composition analytics',
              ),
            ),
          )
        else if (error != null)
          WorkspacePanel(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Unable to load analytics: $error'),
                const SizedBox(height: 12),
                FilledButton(onPressed: load, child: const Text('Try again')),
              ],
            ),
          )
        else if (data?['food_count'] == 0)
          const WorkspacePanel(
            child: Text(
              'No foods in this dataset. Choose another dataset or import food data from the journal.',
            ),
          )
        else ...[
          Wrap(
            spacing: 24,
            runSpacing: 12,
            children: [
              _metric(context, '${data?['food_count']}', 'Food records'),
              _metric(context, '${nutrients.length}', 'Nutrients'),
              _metric(context, '100 g', 'Comparison basis'),
              _metric(
                context,
                '${nutrients.fold<int>(0, (n, row) => n + (row['missing'] as int))}',
                'Unknown food × nutrient values',
              ),
            ],
          ),
          const SizedBox(height: 24),
          OutlinedButton.icon(
            onPressed: widget.onOpenPlateBuilder,
            icon: const Icon(Icons.bubble_chart_outlined),
            label: const Text('Open plate builder bubbles'),
          ),
          const SizedBox(height: 20),
          ...[
            Text('Distribution by nutrient', style: theme.textTheme.titleLarge),
            const SizedBox(height: 6),
            const Text(
              'Box = middle 50% · line = median · whiskers = within 1.5 IQR · dots = outliers. Hover or select a plot for statistics.',
            ),
            const SizedBox(height: 16),
            LayoutBuilder(
              builder: (context, constraints) {
                final width = constraints.maxWidth >= 760
                    ? (constraints.maxWidth - 16) / 2
                    : constraints.maxWidth;
                return Wrap(
                  spacing: 16,
                  runSpacing: 16,
                  children: [
                    for (final n in nutrients)
                      SizedBox(
                        width: width,
                        child: NutrientBoxPlot(
                          stats: Map<String, dynamic>.from(n),
                        ),
                      ),
                  ],
                );
              },
            ),
            const SizedBox(height: 16),
            Text(
              '${data?['method_description']} Each plot has its own scale, from zero to that nutrient’s maximum. Outliers are observations, not errors. Method: ${data?['method']}.',
              style: theme.textTheme.bodySmall,
            ),
          ],
        ],
      ],
    );
  }

  Widget _metric(BuildContext context, String value, String label) => Container(
    width: 190,
    padding: const EdgeInsets.only(left: 14),
    decoration: BoxDecoration(
      border: Border(
        left: BorderSide(
          color: Theme.of(context).colorScheme.primary,
          width: 3,
        ),
      ),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(value, style: Theme.of(context).textTheme.headlineSmall),
        Text(label, style: Theme.of(context).textTheme.bodySmall),
      ],
    ),
  );
}

String distributionDetails(Map<String, dynamic> n) =>
    '${_name(n['nutrient_code'])} · ${n['unit']} per 100 g\n'
    'Reported: ${n['count']}   Unknown: ${n['missing']}\n'
    'Minimum: ${_format(n['minimum'])}   Maximum: ${_format(n['maximum'])}\n'
    'Q1: ${_format(n['q1'])}   Median: ${_format(n['median'])}   Q3: ${_format(n['q3'])}\n'
    'Mean: ${_format(n['mean'])}\n'
    'Whiskers: ${_format(n['lower_whisker'])} – ${_format(n['upper_whisker'])}\n'
    'Outlier observations: ${(n['outliers'] as List).length}';

class AnalyticsInspection extends StatelessWidget {
  final String details;
  final Widget child;
  const AnalyticsInspection({
    super.key,
    required this.details,
    required this.child,
  });
  @override
  Widget build(BuildContext context) => Tooltip(
    message: details,
    excludeFromSemantics: true,
    child: InkWell(
      borderRadius: BorderRadius.circular(8),
      onTap: () => showDialog<void>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Composition statistics'),
          content: SingleChildScrollView(child: SelectableText(details)),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Close'),
            ),
          ],
        ),
      ),
      child: Semantics(
        label: details,
        button: true,
        excludeSemantics: true,
        child: child,
      ),
    ),
  );
}

class NutrientBoxPlot extends StatelessWidget {
  final Map<String, dynamic> stats;
  const NutrientBoxPlot({super.key, required this.stats});
  @override
  Widget build(BuildContext context) => Card(
    margin: EdgeInsets.zero,
    child: AnalyticsInspection(
      details: distributionDetails(stats),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    _name(stats['nutrient_code']),
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
                Text(
                  '${stats['unit']} / 100 g',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
            const SizedBox(height: 6),
            Text(
              'Median ${_format(stats['median'])} · ${stats['count']} reported · ${stats['missing']} unknown',
              style: Theme.of(context).textTheme.bodySmall,
            ),
            const SizedBox(height: 12),
            if (stats['median'] == null)
              const SizedBox(
                height: 54,
                child: Center(child: Text('No reported values')),
              )
            else
              SizedBox(
                height: 54,
                width: double.infinity,
                child: CustomPaint(
                  painter: _BoxPainter(
                    stats,
                    Theme.of(context).colorScheme.primary,
                    Theme.of(context).colorScheme.onSurface,
                  ),
                ),
              ),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('0', style: TextStyle(fontSize: 10)),
                Text(
                  _format(stats['maximum']),
                  style: const TextStyle(fontSize: 10),
                ),
              ],
            ),
          ],
        ),
      ),
    ),
  );
}

class _BoxPainter extends CustomPainter {
  final Map<String, dynamic> stats;
  final Color accent, ink;
  _BoxPainter(this.stats, this.accent, this.ink);
  @override
  void paint(Canvas canvas, Size size) {
    final max = _number(stats['maximum']) ?? 0;
    double x(dynamic value) =>
        5 + (max == 0 ? 0 : (_number(value) ?? 0) / max) * (size.width - 10);
    final line = Paint()
      ..color = ink.withValues(alpha: .7)
      ..strokeWidth = 1.5;
    canvas.drawLine(
      Offset(5, 48),
      Offset(size.width - 5, 48),
      Paint()..color = ink.withValues(alpha: .2),
    );
    canvas.drawLine(
      Offset(x(stats['lower_whisker']), 24),
      Offset(x(stats['upper_whisker']), 24),
      line,
    );
    for (final key in ['lower_whisker', 'upper_whisker']) {
      canvas.drawLine(
        Offset(x(stats[key]), 15),
        Offset(x(stats[key]), 33),
        line,
      );
    }
    final rect = Rect.fromLTRB(
      x(stats['q1']),
      10,
      math.max(x(stats['q3']), x(stats['q1']) + 1),
      38,
    );
    canvas.drawRect(rect, Paint()..color = accent.withValues(alpha: .25));
    canvas.drawRect(
      rect,
      Paint()
        ..color = accent
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.5,
    );
    canvas.drawLine(
      Offset(x(stats['median']), 8),
      Offset(x(stats['median']), 40),
      Paint()
        ..color = ink
        ..strokeWidth = 2.5,
    );
    for (final value in stats['outliers']) {
      canvas.drawCircle(Offset(x(value), 24), 2.5, Paint()..color = accent);
    }
  }

  @override
  bool shouldRepaint(covariant _BoxPainter old) =>
      old.stats != stats || old.accent != accent || old.ink != ink;
}
