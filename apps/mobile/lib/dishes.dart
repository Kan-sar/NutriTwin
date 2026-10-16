import 'plate_bubbles.dart';

import 'dart:math';

import 'package:flutter/material.dart';

import 'api.dart';
import 'dataset_import.dart';
import 'dashboard_widgets.dart';

String recipeRequestKey() {
  final r = Random.secure();
  final b = List<int>.generate(16, (_) => r.nextInt(256));
  b[6] = (b[6] & 15) | 64;
  b[8] = (b[8] & 63) | 128;
  final s = b.map((x) => x.toRadixString(16).padLeft(2, '0')).join();
  return '${s.substring(0, 8)}-${s.substring(8, 12)}-${s.substring(12, 16)}-${s.substring(16, 20)}-${s.substring(20)}';
}

String amountText(dynamic value) {
  if (value == null) return 'Unknown';
  final number = num.tryParse('$value');
  return number == null
      ? '$value'
      : number.toStringAsFixed(2).replaceFirst(RegExp(r'\.?0+$'), '');
}

class DishWorkspace extends StatefulWidget {
  final NutriApi api;
  final Future<void> Function() onChanged;
  final bool admin;
  final Map<String, dynamic>? initialMeal;
  const DishWorkspace({
    super.key,
    required this.api,
    required this.onChanged,
    this.admin = false,
    this.initialMeal,
  });
  @override
  State<DishWorkspace> createState() => _DishWorkspaceState();
}

class _DishWorkspaceState extends State<DishWorkspace> {
  final search = TextEditingController();
  final quantity = TextEditingController(text: '100');
  final name = TextEditingController();
  final batch = TextEditingController();
  final servings = TextEditingController(text: '1');
  final notes = TextEditingController();
  List<dynamic> results = [], recent = [];
  Map<String, dynamic>? selected, view, editing, logged;
  List<Map<String, dynamic>> ingredients = [];
  bool busy = false, creating = false, changed = false, searched = false;
  String? error, message;
  String portion = 'g', meal = 'Lunch';
  DateTime when = DateTime.now();
  String requestKey = recipeRequestKey();
  Map<String, dynamic>? pendingLog;
  int rowEpoch = 0;
  String? baseWeight;
  String? replacesRecipe;

  @override
  void initState() {
    super.initState();
    if (widget.initialMeal != null) {
      perform(() => editMeal(widget.initialMeal!));
    } else {
      perform(browse);
    }
  }

  @override
  void dispose() {
    for (final c in [search, quantity, name, batch, servings, notes]) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> perform(Future<void> Function() f) async {
    if (busy) return;
    setState(() {
      busy = true;
      error = null;
    });
    try {
      await f();
    } on ApiError catch (e) {
      if (mounted) error = e.message;
    } on FormatException catch (e) {
      if (mounted) error = e.message;
    } catch (_) {
      if (mounted) {
        error = 'Could not complete this action. Your entry is still here.';
      }
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> browse() async {
    results = await widget.api.request('GET', '/recipes');
    recent = await widget.api.request('GET', '/meals');
  }

  Future<void> find() async {
    var term = search.text.trim();
    final match = RegExp(
      r'^(\d+(?:\.\d+)?)\s*g\s+(.+)$',
      caseSensitive: false,
    ).firstMatch(term);
    if (match != null && !creating) {
      quantity.text = match[1]!;
      portion = 'g';
      term = match[2]!;
    }
    final q = Uri.encodeQueryComponent(term);
    final dishes = creating
        ? []
        : await widget.api.request('GET', '/recipes?query=$q');
    final foods = await widget.api.request(
      'GET',
      '/foods?query=$q&source_kind=real&limit=25',
    );
    results = [
      ...dishes,
      ...foods.map((f) => {...f, 'kind': 'food', 'source': f['source_code']}),
    ];
    searched = true;
  }

  List<Map<String, dynamic>> payloadIngredients() => ingredients
      .map(
        (i) => <String, dynamic>{
          'food_id': i['food_id'],
          'quantity_g': i['quantity_g'],
        },
      )
      .toList();
  Map<String, dynamic> previewBody({bool reset = false}) {
    if (ingredients.isEmpty && selected == null) {
      throw const FormatException('Add at least one ingredient.');
    }
    final q = num.tryParse(quantity.text);
    if (!creating && (q == null || q <= 0)) {
      throw const FormatException('Enter a positive quantity.');
    }
    return {
      if (selected?['kind'] == 'recipe') 'recipe_id': selected!['id'],
      if (selected?['kind'] == 'food') 'food_id': selected!['id'],
      'quantity': creating ? '100' : quantity.text,
      'portion': portion,
      if (!reset && (changed || creating || selected == null))
        'ingredients': payloadIngredients(),
      if (!reset &&
          changed &&
          !creating &&
          selected != null &&
          baseWeight != null)
        'scale_from_g': baseWeight,
    };
  }

  Future<void> refreshPreview({bool reset = false}) async {
    final data = await widget.api.request(
      'POST',
      '/composition/preview',
      body: previewBody(reset: reset),
    );
    view = Map<String, dynamic>.from(data);
    baseWeight = data['portion_weight_g'];
    rowEpoch++;
    ingredients = (data['ingredients'] as List)
        .map((i) => Map<String, dynamic>.from(i))
        .toList();
    if (reset) changed = false;
  }

  Future<void> choose(Map<String, dynamic> item) async {
    if (creating) {
      ingredients.add({
        'food_id': item['id'],
        'name': item['name'],
        'quantity_g': '100',
      });
      changed = true;
      await refreshPreview();
      return;
    }
    selected = item;
    editing = null;
    logged = null;
    pendingLog = null;
    requestKey = recipeRequestKey();
    ingredients = [];
    changed = false;
    portion = 'g';
    view = null;
    name.text = item['name'];
    await refreshPreview();
  }

  Future<void> editMeal(Map<String, dynamic> item) async {
    final data = await widget.api.request(
      'GET',
      '/meals/${item['id']}/composition',
    );
    editing = Map<String, dynamic>.from(data['meal']);
    creating = false;
    selected = null;
    portion = 'g';
    changed = true;
    when = DateTime.parse(item['eaten_at']).toLocal();
    name.text = item['name'];
    view = Map<String, dynamic>.from(data);
    ingredients = (data['ingredients'] as List)
        .map((i) => Map<String, dynamic>.from(i))
        .toList();
    quantity.text = '100';
    pendingLog = null;
    requestKey = recipeRequestKey();
  }

  void beginRecipe() {
    setState(() {
      creating = true;
      editing = null;
      selected = null;
      logged = null;
      view = null;
      ingredients = [];
      results = [];
      search.clear();
      name.clear();
      batch.clear();
      notes.clear();
      servings.text = '1';
      portion = 'g';
      changed = true;
      message = null;
      error = null;
      pendingLog = null;
      replacesRecipe = null;
    });
  }

  Future<void> saveRecipe() async {
    if (name.text.trim().isEmpty) {
      throw const FormatException('Give your recipe a name.');
    }
    if ((num.tryParse(batch.text) ?? 0) <= 0 ||
        (num.tryParse(servings.text) ?? 0) <= 0) {
      throw const FormatException(
        'Enter the finished batch weight and number of servings.',
      );
    }
    final recipe = await widget.api.request(
      'POST',
      '/recipes',
      body: {
        'name': name.text.trim(),
        'yield_g': batch.text,
        'servings': servings.text,
        'notes': notes.text,
        'ingredients': payloadIngredients(),
        if (replacesRecipe != null) 'replaces_id': replacesRecipe,
      },
    );
    creating = false;
    changed = false;
    ingredients = [];
    selected = {
      ...recipe,
      'kind': 'recipe',
      'personal': true,
      'portions': {'g': '1', ...recipe['portions']},
    };
    quantity.text = '1';
    portion = 'serving';
    name.text = recipe['name'];
    message = 'Recipe saved privately. Choose a portion to log it.';
    await refreshPreview();
    await browse();
  }

  Future<void> log() async {
    if (pendingLog == null) {
      if (name.text.trim().isEmpty) {
        throw const FormatException('Enter a name for this entry.');
      }
      await refreshPreview();
      pendingLog = {
        ...previewBody(),
        'request_key': requestKey,
        'name': editing == null
            ? '${name.text.trim()} · $meal'
            : name.text.trim(),
        'eaten_at': when.toUtc().toIso8601String(),
        'local_date':
            '${when.year}-${when.month.toString().padLeft(2, '0')}-${when.day.toString().padLeft(2, '0')}',
        if (editing != null) 'meal_id': editing!['id'],
        if (editing != null) 'expected_revision': editing!['revision'],
      };
    }
    dynamic saved;
    try {
      saved = await widget.api.request('POST', '/food-log', body: pendingLog);
    } on ApiError catch (e) {
      if (e.status >= 400 && e.status < 500) {
        pendingLog = null;
        requestKey = recipeRequestKey();
      }
      rethrow;
    }
    logged = Map<String, dynamic>.from(saved);
    pendingLog = null;
    editing = null;
    requestKey = recipeRequestKey();
    message = 'Logged. Your journal and profile history have been updated.';
    await widget.onChanged();
    await browse();
  }

  Future<void> undo() async {
    final item = logged!;
    await widget.api.request(
      'DELETE',
      '/meals/${item['id']}?expected_revision=${item['revision']}',
    );
    logged = null;
    message = 'Entry removed from your journal and totals.';
    await widget.onChanged();
    await browse();
  }

  Future<void> dateTime() async {
    final day = await showDatePicker(
      context: context,
      initialDate: when,
      firstDate: DateTime(1900),
      lastDate: DateTime.now().add(const Duration(days: 365)),
    );
    if (day == null || !mounted) return;
    final time = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.fromDateTime(when),
    );
    if (time == null) return;
    when = DateTime(day.year, day.month, day.day, time.hour, time.minute);
  }

  Widget input(String label, TextEditingController c, {String? help}) =>
      Padding(
        padding: const EdgeInsets.symmetric(vertical: 8),
        child: TextField(
          controller: c,
          enabled: !busy && pendingLog == null,
          decoration: InputDecoration(labelText: label, helperText: help),
        ),
      );
  Widget action(
    String label,
    Future<void> Function() f, {
    bool enabled = true,
  }) => FilledButton(
    onPressed: busy || !enabled ? null : () => perform(f),
    child: Text(label),
  );

  @override
  Widget build(BuildContext context) {
    final portions = Map<String, dynamic>.from(
      selected?['portions'] ?? {'g': '1'},
    );
    portions.putIfAbsent('g', () => '1');
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          creating
              ? 'Create your recipe'
              : editing != null
              ? 'Edit logged meal'
              : 'What’s on your plate?',
          style: Theme.of(context).textTheme.headlineMedium,
        ),
        const SizedBox(height: 8),
        Text(
          creating
              ? 'Add ingredients for the whole batch. Your recipe stays private.'
              : 'Search a dish, choose your portion, and log it. Adjust ingredients whenever you need.',
        ),
        const SizedBox(height: 16),
        Wrap(
          spacing: 12,
          runSpacing: 8,
          children: [
            if (!creating)
              OutlinedButton.icon(
                onPressed: busy || pendingLog != null ? null : beginRecipe,
                icon: const Icon(Icons.add),
                label: const Text('Create recipe'),
              ),
            if (creating)
              OutlinedButton(
                onPressed: busy
                    ? null
                    : () => perform(() async {
                        creating = false;
                        ingredients = [];
                        view = null;
                        selected = null;
                        await browse();
                      }),
                child: const Text('Back to dishes'),
              ),
            if (widget.admin)
              OutlinedButton.icon(
                onPressed: busy
                    ? null
                    : () async {
                        await showDialog(
                          context: context,
                          builder: (_) => DatasetImportDialog(api: widget.api),
                        );
                        if (mounted) perform(browse);
                      },
                icon: const Icon(Icons.file_upload_outlined),
                label: const Text('Import dataset'),
              ),
          ],
        ),
        if (busy) const LinearProgressIndicator(),
        if (error != null)
          Padding(
            padding: const EdgeInsets.all(12),
            child: Semantics(
              liveRegion: true,
              child: Text(
                error!,
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              ),
            ),
          ),
        if (message != null)
          Padding(
            padding: const EdgeInsets.all(12),
            child: Semantics(liveRegion: true, child: Text(message!)),
          ),
        if (logged != null)
          OutlinedButton(
            onPressed: busy ? null : () => perform(undo),
            child: const Text('Undo log'),
          ),
        if (pendingLog != null) ...[
          const Text(
            'The save response was not confirmed. Retry this same action safely before editing.',
          ),
          action('Retry log', log),
        ],
        if (creating) ...[
          input('Recipe name', name),
          input(
            'Finished batch weight (g)',
            batch,
            help: 'Weigh the finished batch, including retained water.',
          ),
          input('Servings in this batch', servings),
          input('Recipe notes', notes),
          const Text(
            'Choose each ingredient in the state you weighed it. No extra cooking-loss adjustment is guessed.',
          ),
        ],
        const SizedBox(height: 16),
        if (!creating) ...[
          PlateSteps(
            active: logged != null
                ? 2
                : selected != null
                ? 1
                : 0,
          ),
          const SizedBox(height: 18),
        ],
        WorkspaceColumns(
          primaryFlex: 2,
          secondaryFlex: 3,
          primary: WorkspacePanel(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  creating ? 'Find ingredients' : 'Choose your food',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: search,
                  enabled: !busy && pendingLog == null,
                  onSubmitted: (_) => perform(find),
                  decoration: InputDecoration(
                    labelText: creating
                        ? 'Find an ingredient'
                        : 'Search food or dish',
                    hintText: creating
                        ? 'Try cooked rice, lentils or oil'
                        : 'Try dosa, biryani or 200 g idli',
                    suffixIcon: IconButton(
                      tooltip: 'Search dishes and foods',
                      onPressed: busy ? null : () => perform(find),
                      icon: const Icon(Icons.search),
                    ),
                  ),
                ),
                if (results.isEmpty && searched)
                  const Padding(
                    padding: EdgeInsets.all(16),
                    child: Text(
                      'No matches. Try another name or create your own recipe.',
                    ),
                  ),
                if (selected == null && !creating && !searched) ...[
                  const SizedBox(height: 16),
                  Text(
                    'Recent meals',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  if (recent.isEmpty)
                    const Text('Your logged meals will appear here.'),
                  for (final r in recent.take(5))
                    ListTile(
                      title: Text(r['name']),
                      subtitle: Text(r['local_date']),
                      trailing: const Icon(Icons.history),
                      onTap: busy
                          ? null
                          : () => perform(
                              () => editMeal(Map<String, dynamic>.from(r)),
                            ),
                    ),
                  Text(
                    'Dishes & favorites',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ],
                ConstrainedBox(
                  constraints: const BoxConstraints(maxHeight: 290),
                  child: ListView(
                    shrinkWrap: true,
                    children: [
                      for (final r in results)
                        ListTile(
                          leading: Icon(
                            r['kind'] == 'recipe'
                                ? Icons.rice_bowl_outlined
                                : Icons.eco_outlined,
                          ),
                          title: Text(r['name']),
                          subtitle: Text('${r['source']}'),
                          trailing: r['kind'] == 'recipe'
                              ? IconButton(
                                  tooltip: r['favorite'] == true
                                      ? 'Remove favorite'
                                      : 'Favorite recipe',
                                  icon: Icon(
                                    r['favorite'] == true
                                        ? Icons.star
                                        : Icons.star_border,
                                  ),
                                  onPressed: busy
                                      ? null
                                      : () => perform(() async {
                                          await widget.api.request(
                                            'PUT',
                                            '/recipes/${r['id']}/favorite?enabled=${r['favorite'] != true}',
                                          );
                                          await find();
                                        }),
                                )
                              : const Icon(Icons.add),
                          onTap: busy || pendingLog != null
                              ? null
                              : () => perform(
                                  () => choose(Map<String, dynamic>.from(r)),
                                ),
                        ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          secondary: WorkspacePanel(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  creating ? 'Recipe composition' : 'Your plate',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                if (selected == null && ingredients.isEmpty) ...[
                  const SizedBox(height: 24),
                  Center(
                    child: Icon(
                      Icons.restaurant_outlined,
                      size: 56,
                      color: Theme.of(context).colorScheme.primary,
                    ),
                  ),
                  const SizedBox(height: 20),
                  const Text(
                    'Start with a dish or ingredient',
                    style: TextStyle(fontWeight: FontWeight.w600),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Choose a result to load its ingredients. Set your portion, adjust the amounts, then log it to your profile.',
                  ),
                  const SizedBox(height: 12),
                  const Text('Nothing is saved until you choose Log food.'),
                ],
                if (selected != null || ingredients.isNotEmpty) ...[
                  const SizedBox(height: 20),
                  if (!creating) ...[
                    input('Entry name', name),
                    if (selected != null)
                      Wrap(
                        spacing: 12,
                        runSpacing: 8,
                        crossAxisAlignment: WrapCrossAlignment.center,
                        children: [
                          SizedBox(
                            width: 150,
                            child: input('Quantity', quantity),
                          ),
                          SizedBox(
                            width: 220,
                            child: DropdownButtonFormField<String>(
                              key: ValueKey('${selected!['id']}:$portion'),
                              initialValue: portion,
                              isExpanded: true,
                              decoration: const InputDecoration(
                                labelText: 'Portion unit',
                              ),
                              items: portions.keys
                                  .map(
                                    (p) => DropdownMenuItem(
                                      value: p,
                                      child: Text(p),
                                    ),
                                  )
                                  .toList(),
                              onChanged: busy || pendingLog != null
                                  ? null
                                  : (v) => setState(() => portion = v!),
                            ),
                          ),
                          action('Update portion', () async {
                            if (changed) {
                              final currentWeight = num.tryParse('$baseWeight');
                              if (currentWeight == null || currentWeight <= 0) {
                                throw const FormatException(
                                  'Reset the recipe before rescaling.',
                                );
                              }
                              final body = {
                                ...previewBody(),
                                'scale_from_g': '$currentWeight',
                              };
                              final data = await widget.api.request(
                                'POST',
                                '/composition/preview',
                                body: body,
                              );
                              view = Map<String, dynamic>.from(data);
                              baseWeight = data['portion_weight_g'];
                              rowEpoch++;
                              ingredients = (data['ingredients'] as List)
                                  .map((i) => Map<String, dynamic>.from(i))
                                  .toList();
                            } else {
                              await refreshPreview();
                            }
                          }),
                        ],
                      ),
                    if (selected != null)
                      Text(
                        '${selected!['source']} · ingredient amounts below are for this entry.',
                      ),
                    if (selected?['personal'] == true)
                      Wrap(
                        spacing: 12,
                        children: [
                          OutlinedButton(
                            onPressed: busy
                                ? null
                                : () => perform(() async {
                                    final r = await widget.api.request(
                                      'GET',
                                      '/recipes/${selected!['id']}',
                                    );
                                    replacesRecipe = r['id'];
                                    creating = true;
                                    selected = null;
                                    changed = true;
                                    name.text = r['name'];
                                    batch.text = r['yield_g'];
                                    notes.text = r['notes'] ?? '';
                                    final size = num.parse(
                                      '${r['portions']['serving']}',
                                    );
                                    servings.text =
                                        (num.parse(r['yield_g']) / size)
                                            .toStringAsFixed(3);
                                    ingredients = (r['ingredients'] as List)
                                        .map(
                                          (i) => Map<String, dynamic>.from(i),
                                        )
                                        .toList();
                                    portion = 'g';
                                    await refreshPreview();
                                  }),
                            child: const Text('Edit my recipe'),
                          ),
                          OutlinedButton(
                            onPressed: busy
                                ? null
                                : () => perform(() async {
                                    await widget.api.request(
                                      'DELETE',
                                      '/recipes/${selected!['id']}',
                                    );
                                    selected = null;
                                    ingredients = [];
                                    view = null;
                                    message = 'Recipe retired. Previously logged meals are preserved.';
                                    await browse();
                                  }),
                            child: const Text('Retire recipe'),
                          ),
                        ],
                      ),
                  ],
                  ExpansionTile(
                    initiallyExpanded: creating || editing != null,
                    title: Text(
                      'Ingredients and amounts (${ingredients.length})',
                    ),
                    subtitle: const Text(
                      'Adjust grams, remove ingredients, or add a replacement',
                    ),
                    children: [
                      for (int i = 0; i < ingredients.length; i++)
                        Padding(
                          padding: const EdgeInsets.symmetric(vertical: 8),
                          child: Row(
                            children: [
                              Expanded(
                                child: Text(
                                  ingredients[i]['name'] ??
                                      ingredients[i]['food_id'],
                                ),
                              ),
                              const SizedBox(width: 12),
                              SizedBox(
                                width: 108,
                                child: TextFormField(
                                  key: ValueKey(
                                    '$rowEpoch:$i:${ingredients[i]['food_id']}',
                                  ),
                                  initialValue:
                                      '${ingredients[i]['quantity_g']}',
                                  enabled: !busy && pendingLog == null,
                                  keyboardType:
                                      const TextInputType.numberWithOptions(
                                        decimal: true,
                                      ),
                                  decoration: InputDecoration(
                                    labelText: 'Grams',
                                    semanticCounterText: ingredients[i]['name'],
                                  ),
                                  onChanged: (v) => setState(() {
                                    ingredients[i]['quantity_g'] = v;
                                    changed = true;
                                    view = null;
                                  }),
                                  onFieldSubmitted: (_) =>
                                      perform(refreshPreview),
                                ),
                              ),
                              IconButton(
                                tooltip: 'Remove ${ingredients[i]['name']}',
                                onPressed: busy || pendingLog != null
                                    ? null
                                    : () => setState(() {
                                        ingredients.removeAt(i);
                                        changed = true;
                                        view = null;
                                      }),
                                icon: const Icon(Icons.remove_circle_outline),
                              ),
                            ],
                          ),
                        ),
                      Wrap(
                        spacing: 12,
                        runSpacing: 8,
                        children: [
                          action(
                            'Recalculate',
                            refreshPreview,
                            enabled:
                                ingredients.isNotEmpty && pendingLog == null,
                          ),
                          if (selected?['kind'] == 'recipe')
                            OutlinedButton(
                              onPressed: busy || pendingLog != null
                                  ? null
                                  : () => perform(
                                      () => refreshPreview(reset: true),
                                    ),
                              child: const Text('Reset to recipe'),
                            ),
                          if (!creating)
                            OutlinedButton(
                              onPressed: busy || pendingLog != null
                                  ? null
                                  : () async {
                                      final food =
                                          await showDialog<
                                            Map<String, dynamic>
                                          >(
                                            context: context,
                                            builder: (_) => IngredientPicker(
                                              api: widget.api,
                                            ),
                                          );
                                      if (food != null && mounted) {
                                        perform(() async {
                                          ingredients.add({
                                            'food_id': food['id'],
                                            'name': food['name'],
                                            'quantity_g': '100',
                                          });
                                          changed = true;
                                          await refreshPreview();
                                        });
                                      }
                                    },
                              child: const Text('Add / replace ingredient'),
                            ),
                        ],
                      ),
                    ],
                  ),
                  if (view != null) CompositionView(data: view!, compact: true),
                  if (view == null)
                    const Text(
                      'Amounts changed. Recalculate to update composition.',
                    ),
                  const SizedBox(height: 16),
                  if (creating)
                    action(
                      'Save private recipe',
                      saveRecipe,
                      enabled: ingredients.isNotEmpty,
                    )
                  else ...[
                    Wrap(
                      spacing: 12,
                      runSpacing: 12,
                      children: [
                        SizedBox(
                          width: 200,
                          child: DropdownButtonFormField<String>(
                            initialValue: meal,
                            decoration: const InputDecoration(
                              labelText: 'Meal',
                            ),
                            items: ['Breakfast', 'Lunch', 'Dinner', 'Snack']
                                .map(
                                  (s) => DropdownMenuItem(
                                    value: s,
                                    child: Text(s),
                                  ),
                                )
                                .toList(),
                            onChanged: busy || pendingLog != null
                                ? null
                                : (v) => setState(() => meal = v!),
                          ),
                        ),
                        OutlinedButton.icon(
                          onPressed: busy || pendingLog != null
                              ? null
                              : () => perform(dateTime),
                          icon: const Icon(Icons.calendar_today),
                          label: Text(
                            '${when.day}/${when.month}/${when.year} ${when.hour}:${when.minute.toString().padLeft(2, '0')}',
                          ),
                        ),
                        action(
                          editing == null ? 'Log food' : 'Save meal changes',
                          log,
                          enabled: ingredients.isNotEmpty && pendingLog == null,
                        ),
                        OutlinedButton(
                          onPressed: busy || pendingLog != null
                              ? null
                              : () => setState(() {
                                  creating = true;
                                  selected = null;
                                  editing = null;
                                  batch.clear();
                                  portions.clear();
                                  portion = 'g';
                                  servings.text = '1';
                                  message = 'Set the batch weight and servings to save this variation privately.';
                                }),
                          child: const Text('Save as my recipe'),
                        ),
                      ],
                    ),
                  ],
                ],
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class IngredientPicker extends StatefulWidget {
  final NutriApi api;
  const IngredientPicker({super.key, required this.api});
  @override
  State<IngredientPicker> createState() => _IngredientPickerState();
}

class _IngredientPickerState extends State<IngredientPicker> {
  final query = TextEditingController();
  List<dynamic> foods = [];
  String? error;
  bool busy = false;
  @override
  void dispose() {
    query.dispose();
    super.dispose();
  }

  Future<void> find() async {
    setState(() {
      busy = true;
      error = null;
    });
    try {
      final r = await widget.api.request(
        'GET',
        '/foods?source_kind=real&query=${Uri.encodeQueryComponent(query.text)}',
      );
      if (mounted) setState(() => foods = r);
    } catch (e) {
      if (mounted) setState(() => error = '$e');
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: const Text('Choose an ingredient'),
    content: SizedBox(
      width: 520,
      height: 400,
      child: Column(
        children: [
          TextField(
            controller: query,
            onSubmitted: (_) => find(),
            decoration: InputDecoration(
              labelText: 'Search ingredients',
              suffixIcon: IconButton(
                onPressed: busy ? null : find,
                tooltip: 'Find ingredient',
                icon: const Icon(Icons.search),
              ),
            ),
          ),
          if (error != null) Text(error!),
          if (busy) const LinearProgressIndicator(),
          Expanded(
            child: ListView(
              children: [
                for (final f in foods)
                  ListTile(
                    title: Text(f['name']),
                    subtitle: Text(f['source_code']),
                    onTap: () =>
                        Navigator.pop(context, Map<String, dynamic>.from(f)),
                  ),
              ],
            ),
          ),
        ],
      ),
    ),
    actions: [
      TextButton(
        onPressed: () => Navigator.pop(context),
        child: const Text('Cancel'),
      ),
    ],
  );
}

class MealCompositionPage extends StatefulWidget {
  final NutriApi api;
  final List<dynamic> meals;
  final void Function(Map<String, dynamic>) onEdit;
  const MealCompositionPage({
    super.key,
    required this.api,
    required this.meals,
    required this.onEdit,
  });
  @override
  State<MealCompositionPage> createState() => _MealCompositionPageState();
}

class _MealCompositionPageState extends State<MealCompositionPage> {
  String? id, error;
  Map<String, dynamic>? data;
  bool busy = false;

  @override
  void initState() {
    super.initState();
    if (widget.meals.isNotEmpty) select(widget.meals.first['id']);
  }

  Future<void> select(String value) async {
    setState(() {
      id = value;
      busy = true;
      error = null;
      data = null;
    });
    try {
      final d = await widget.api.request('GET', '/meals/$value/composition');
      if (mounted) setState(() => data = Map<String, dynamic>.from(d));
    } catch (e) {
      if (mounted) setState(() => error = '$e');
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(
        'Meal composition',
        style: Theme.of(context).textTheme.headlineMedium,
      ),
      const SizedBox(height: 8),
      const Text(
        'Explore your plate. Select a nutrient to see what each ingredient contributes.',
      ),
      const SizedBox(height: 20),
      if (widget.meals.isEmpty)
        const Text('Log a dish or meal to explore its composition here.')
      else
        DropdownButtonFormField<String>(
          initialValue: id,
          isExpanded: true,
          decoration: const InputDecoration(labelText: 'Choose a logged meal'),
          items: widget.meals
              .map(
                (m) => DropdownMenuItem<String>(
                  value: m['id'],
                  child: Text(
                    '${m['name']} · ${m['local_date']}',
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              )
              .toList(),
          onChanged: busy ? null : (v) => select(v!),
        ),
      if (busy) const LinearProgressIndicator(),
      if (error != null) Text(error!),
      if (data != null) ...[
        const SizedBox(height: 20),
        CompositionView(data: data!),
        OutlinedButton.icon(
          onPressed: () =>
              widget.onEdit(Map<String, dynamic>.from(data!['meal'])),
          icon: const Icon(Icons.edit),
          label: const Text('Edit this meal'),
        ),
        if (data!['trace']?['definition']?['source'] != null)
          Text('Recipe source: ${data!['trace']['definition']['source']}'),
      ],
    ],
  );
}

class CompositionView extends StatefulWidget {
  final Map<String, dynamic> data;
  final bool compact;
  const CompositionView({super.key, required this.data, this.compact = false});
  @override
  State<CompositionView> createState() => _CompositionViewState();
}

class _CompositionViewState extends State<CompositionView> {
  String nutrient = 'protein';
  bool bubbles = false;
  int? selected;
  @override
  Widget build(BuildContext context) {
    final ns = Map<String, dynamic>.from(widget.data['nutrients'] ?? {});
    if (ns.isEmpty) return const Text('No nutrient composition available.');
    final code = ns.containsKey(nutrient) ? nutrient : ns.keys.first;
    final total = ns[code];
    final rows = widget.data['ingredients'] as List;
    final positive = rows
        .map(
          (r) =>
              num.tryParse('${r['nutrients']?[code]?['amount']}')?.toDouble() ??
              0.0,
        )
        .toList();
    final sum = positive.fold<double>(0, (a, b) => a + b);
    final colors = [
      Theme.of(context).colorScheme.primary,
      const Color(0xffca8355),
      const Color(0xff589ba8),
      const Color(0xff9b83bd),
      const Color(0xff9aa756),
      const Color(0xffbf7599),
    ];
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                ChoiceChip(
                  label: const Text('Ingredient breakdown'),
                  selected: !bubbles,
                  onSelected: (_) => setState(() => bubbles = false),
                ),
                ChoiceChip(
                  label: const Text('Nutrient bubbles'),
                  selected: bubbles,
                  onSelected: (_) => setState(() => bubbles = true),
                ),
              ],
            ),
            const SizedBox(height: 20),
            // Keep both view states when switching without stacking both charts.
            Offstage(
              offstage: !bubbles,
              child: PlateBubbles(data: widget.data),
            ),
            Offstage(
              offstage: bubbles,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'On this plate',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 12),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      for (final c in [
                        'energy',
                        'protein',
                        'carbohydrate',
                        'fat',
                      ])
                        if (ns[c] != null)
                          ActionChip(
                            label: Text(
                              '${c.replaceAll('_', ' ')}  ${amountText(ns[c]['amount'])} ${ns[c]['canonical_unit']}',
                            ),
                            onPressed: () => setState(() => nutrient = c),
                          ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  DropdownButtonFormField<String>(
                    key: ValueKey(code),
                    initialValue: code,
                    isExpanded: true,
                    decoration: const InputDecoration(
                      labelText: 'Nutrient focus',
                    ),
                    items: ns.keys
                        .map(
                          (c) => DropdownMenuItem(
                            value: c,
                            child: Text(c.replaceAll('_', ' ')),
                          ),
                        )
                        .toList(),
                    onChanged: (v) => setState(() {
                      nutrient = v!;
                      selected = null;
                    }),
                  ),
                  const SizedBox(height: 16),
                  if (widget.compact)
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        if (total['complete'] != true)
                          const Text(
                            'Some ingredient values are unknown. Shown totals and shares cover known contributions only.',
                          ),
                        for (int i = 0; i < rows.length; i++)
                          ListTile(
                            selected: selected == i,
                            contentPadding: EdgeInsets.zero,
                            leading: Container(
                              width: 14,
                              height: 14,
                              decoration: BoxDecoration(
                                color: colors[i % colors.length],
                                shape: BoxShape.circle,
                              ),
                            ),
                            title: Text(rows[i]['name']),
                            subtitle: Text(
                              '${amountText(rows[i]['quantity_g'])} g · ${amountText(rows[i]['nutrients']?[code]?['amount'])} ${total['canonical_unit']}\n${sum > 0 && rows[i]['nutrients']?[code]?['amount'] != null ? '${(positive[i] / sum * 100).toStringAsFixed(1)}% of known total' : 'No known share'}',
                            ),

                            onTap: () => setState(
                              () => selected = selected == i ? null : i,
                            ),
                          ),
                      ],
                    )
                  else
                    WorkspaceColumns(
                      breakpoint: 680,
                      primaryFlex: 2,
                      secondaryFlex: 3,
                      primary: Center(
                        child: SizedBox(
                          width: 250,
                          height: 250,
                          child: Stack(
                            alignment: Alignment.center,
                            children: [
                              ExcludeSemantics(
                                child: CustomPaint(
                                  size: const Size(250, 250),
                                  painter: _PlatePainter(
                                    positive,
                                    colors,
                                    selected,
                                  ),
                                ),
                              ),
                              SizedBox(
                                width: 145,
                                child: Column(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    Text(code.replaceAll('_', ' ')),
                                    Text(
                                      '${amountText(total['amount'])} ${total['canonical_unit']}',
                                      style: Theme.of(context)
                                          .textTheme
                                          .headlineSmall,
                                      textAlign: TextAlign.center,
                                    ),
                                    Text(
                                      total['complete'] == true
                                          ? 'Known total'
                                          : 'Incomplete total',
                                      textAlign: TextAlign.center,
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                      secondary: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Ingredient contributions',
                            style: Theme.of(context).textTheme.titleMedium,
                          ),
                          const SizedBox(height: 4),
                          const Text(
                            'Select an ingredient to highlight it on the plate.',
                          ),
                          if (total['complete'] != true)
                            const Text(
                              'Some ingredient values are unknown. Shown totals and shares cover known contributions only.',
                            ),
                          for (int i = 0; i < rows.length; i++)
                            ListTile(
                              selected: selected == i,
                              contentPadding: EdgeInsets.zero,
                              leading: Container(
                                width: 14,
                                height: 14,
                                decoration: BoxDecoration(
                                  color: colors[i % colors.length],
                                  shape: BoxShape.circle,
                                ),
                              ),
                              title: Text(rows[i]['name']),
                              subtitle: Text(
                                '${amountText(rows[i]['quantity_g'])} g · ${amountText(rows[i]['nutrients']?[code]?['amount'])} ${total['canonical_unit']}\n${sum > 0 && rows[i]['nutrients']?[code]?['amount'] != null ? '${(positive[i] / sum * 100).toStringAsFixed(1)}% of known total' : 'No known share'}',
                              ),

                              onTap: () => setState(
                                () => selected = selected == i ? null : i,
                              ),
                            ),
                        ],
                      ),
                    ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            if (!widget.compact)
              Text(
                widget.data['allergen_notice'] ??
                    'Ingredient composition is an estimate.',
              ),
          ],
        ),
      ),
    );
  }
}

class _PlatePainter extends CustomPainter {
  final List<double> values;
  final List<Color> colors;
  final int? selected;
  _PlatePainter(this.values, this.colors, this.selected);
  @override
  void paint(Canvas canvas, Size size) {
    final rect = Rect.fromLTWH(20, 20, size.width - 40, size.height - 40);
    final total = values.fold<double>(0, (a, b) => a + b);
    canvas.drawArc(
      rect,
      0,
      2 * pi,
      false,
      Paint()
        ..color = colors.first.withValues(alpha: 0.12)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 25,
    );
    if (total <= 0) return;
    var start = -pi / 2;
    for (int i = 0; i < values.length; i++) {
      final sweep = values[i] / total * 2 * pi;
      canvas.drawArc(
        rect,
        start,
        sweep,
        false,
        Paint()
          ..color = colors[i % colors.length].withValues(
            alpha: selected == null || selected == i ? 1 : 0.3,
          )
          ..style = PaintingStyle.stroke
          ..strokeWidth = selected == i ? 34 : 25,
      );
      start += sweep;
    }
  }

  @override
  bool shouldRepaint(covariant _PlatePainter old) => true;
}
