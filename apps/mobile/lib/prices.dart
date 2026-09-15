import 'package:flutter/material.dart';

import 'api.dart';

class FoodPrices extends StatefulWidget {
  final NutriApi api;
  const FoodPrices({super.key, required this.api});
  @override
  State<FoodPrices> createState() => _FoodPricesState();
}

class _FoodPricesState extends State<FoodPrices> {
  final query = TextEditingController();
  final price = TextEditingController();
  final preparation = TextEditingController(text: '15');
  final servings = TextEditingController(text: '2');
  final observed = TextEditingController(
    text: DateTime.now().toIso8601String().substring(0, 10),
  );
  List<dynamic> results = [], saved = [];
  String? selected, message;
  bool busy = false;
  @override
  void dispose() {
    for (final controller in [query, price, preparation, servings, observed]) {
      controller.dispose();
    }
    super.dispose();
  }

  Future<void> run(Future<void> Function() action) async {
    setState(() {
      busy = true;
      message = null;
    });
    try {
      await action();
    } on ApiError catch (e) {
      message = e.message;
    } on FormatException {
      message =
          'Enter a valid price, date, preparation time, and serving count.';
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Widget field(String label, TextEditingController controller) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 8),
    child: TextField(
      enabled: !busy,
      controller: controller,
      decoration: InputDecoration(labelText: label),
    ),
  );
  @override
  Widget build(BuildContext context) => ExpansionTile(
    title: const Text('My food prices'),
    subtitle: const Text('Manual INR prices, private to your account'),
    children: [
      if (busy) const LinearProgressIndicator(),
      if (message != null) Semantics(liveRegion: true, child: Text(message!)),
      field('Find a food to price', query),
      OutlinedButton(
        onPressed: busy
            ? null
            : () => run(() async {
                results = await widget.api.request(
                  'GET',
                  '/foods?query=${Uri.encodeQueryComponent(query.text.trim())}',
                );
                selected = null;
              }),
        child: const Text('Find foods'),
      ),
      for (final food in results)
        ListTile(
          title: Text(food['name']),
          subtitle: Text(food['source_code']),
          selected: selected == food['id'],
          leading: Icon(
            selected == food['id'] ? Icons.check_circle : Icons.circle_outlined,
          ),
          onTap: busy ? null : () => setState(() => selected = food['id']),
        ),
      field('INR per 100 g', price),
      field('Preparation minutes per 100 g', preparation),
      field('Maximum 100 g servings (1–10)', servings),
      field('Price observation date (YYYY-MM-DD)', observed),
      FilledButton(
        onPressed: busy || selected == null
            ? null
            : () => run(() async {
                final rupees = double.parse(price.text);
                if (!rupees.isFinite || rupees < 0) {
                  throw const FormatException();
                }
                await widget.api.request(
                  'PUT',
                  '/food-offers/$selected',
                  body: {
                    'cost_minor_per_100g': (rupees * 100).round(),
                    'currency': 'INR',
                    'preparation_minutes': int.parse(preparation.text),
                    'maximum_servings': int.parse(servings.text),
                    'observed_on': observed.text.trim(),
                  },
                );
                saved = await widget.api.request('GET', '/food-offers');
                message = 'Price saved.';
              }),
        child: const Text('Save price'),
      ),
      TextButton(
        onPressed: busy
            ? null
            : () => run(() async {
                saved = await widget.api.request('GET', '/food-offers');
              }),
        child: const Text('Load my saved prices'),
      ),
      for (final offer in saved)
        ListTile(
          title: Text(
            'INR ${(offer['cost_minor_per_100g'] / 100).toStringAsFixed(2)} / 100 g',
          ),
          subtitle: Text(
            '${offer['observed_on']} • ${offer['stale_pricing'] ? 'Stale — refresh before planning' : 'Within the 14-day price window'}',
          ),
        ),
      const Padding(
        padding: EdgeInsets.all(12),
        child: Text(
          'Prices do not establish food safety or scientific target validity.',
        ),
      ),
    ],
  );
}
