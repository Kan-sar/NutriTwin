import 'dart:convert';

import 'package:flutter/material.dart';

import 'api.dart';
import 'prices.dart';
import 'weekly_chart.dart';

void main() => runApp(const NutriTwinApp());
const forest = Color(0xFF244F3D);
const paper = Color(0xFFF5F5ED);
const chartColors = [
  Color(0xFF4E79A7),
  Color(0xFFE15759),
  Color(0xFF59A14F),
  Color(0xFFF28E2B),
];
String day(DateTime date) => date.toIso8601String().substring(0, 10);
String shown(dynamic value) {
  if (value == null) return 'Unavailable';
  final parsed = double.tryParse('$value');
  return parsed == null ? '$value' : parsed.toStringAsFixed(2);
}

String label(String code) => code.replaceAll('_', ' ');
double? number(dynamic value) => double.tryParse('$value');

class NutriTwinApp extends StatelessWidget {
  final NutriApi? api;
  const NutriTwinApp({super.key, this.api});
  @override
  Widget build(BuildContext context) => MaterialApp(
    title: 'NutriTwin',
    debugShowCheckedModeBanner: false,
    theme: ThemeData(
      useMaterial3: true,
      scaffoldBackgroundColor: paper,
      colorScheme: ColorScheme.fromSeed(seedColor: forest, primary: forest),
      inputDecorationTheme: const InputDecorationTheme(
        border: OutlineInputBorder(),
      ),
      cardTheme: CardThemeData(
        color: Colors.white,
        elevation: 0,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      ),
    ),
    home: TwinHome(api: api ?? NutriApi()),
  );
}

class TwinHome extends StatefulWidget {
  final NutriApi api;
  const TwinHome({super.key, required this.api});
  @override
  State<TwinHome> createState() => _TwinHomeState();
}

class _TwinHomeState extends State<TwinHome> {
  final email = TextEditingController(), password = TextEditingController();
  final birth = TextEditingController(), allergens = TextEditingController();
  final search = TextEditingController(),
      mealName = TextEditingController(text: 'My meal');
  final mealDate = TextEditingController(text: day(DateTime.now()));
  final mealTime = TextEditingController(text: '12:00');
  final budget = TextEditingController(text: '50'),
      prep = TextEditingController(text: '30');
  final iron = TextEditingController(text: '3'),
      vitaminC = TextEditingController(text: '20');
  final gapWeight = TextEditingController(text: '7'),
      timeWeight = TextEditingController(text: '2');
  final varietyWeight = TextEditingController(text: '1');
  final proposal = TextEditingController(),
      reviewNote = TextEditingController();
  Map<String, dynamic>? user, profile, summary, constructed;
  List<dynamic> foods = [],
      meals = [],
      ranked = [],
      history = [],
      revisions = [];
  List<Map<String, dynamic>> draft = [];
  String? editId, error;
  int? editRevision;
  String dietary = 'unrestricted', sex = '', role = 'student';
  bool busy = false, register = false, consent = false, demo = true;
  int page = 0;
  int draftEpoch = 0;
  NutriApi get api => widget.api;
  final pages = [
    'Overview',
    'Food journal',
    'Meal planning',
    'Profile',
    'Evidence review',
  ];
  final icons = [
    Icons.dashboard_outlined,
    Icons.restaurant_outlined,
    Icons.auto_awesome_outlined,
    Icons.person_outline,
    Icons.fact_check_outlined,
  ];
  @override
  void dispose() {
    for (final c in [
      email,
      password,
      birth,
      allergens,
      search,
      mealName,
      mealDate,
      mealTime,
      budget,
      prep,
      iron,
      vitaminC,
      gapWeight,
      timeWeight,
      varietyWeight,
      proposal,
      reviewNote,
    ]) {
      c.dispose();
    }
    api.dispose();
    super.dispose();
  }

  Future<void> act(Future<void> Function() action) async {
    if (busy) return;
    setState(() {
      busy = true;
      error = null;
    });
    try {
      await action();
    } on ApiError catch (e) {
      error = e.message;
      if (e.status == 401) {
        user = null;
        summary = null;
      }
      if (e.status == 409 && e.message.contains('consent')) page = 3;
    } on FormatException {
      error = 'Check dates, times, numbers, and structured evidence values.';
    } catch (_) {
      error =
          'The request could not be completed. Refresh to check saved changes.';
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> load() async {
    try {
      profile = Map<String, dynamic>.from(
        await api.request('GET', '/profiles/me'),
      );
    } on ApiError catch (e) {
      if (e.status != 404) rethrow;
      profile = null;
      page = 3;
    }
    if (profile != null) {
      birth.text = profile!['birth_date'];
      sex = profile!['source_sex_category'] ?? '';
      dietary = profile!['dietary_pattern'];
      allergens.text = (profile!['allergens'] as List).join(', ');
      summary = Map<String, dynamic>.from(
        await api.request('GET', '/twin/summary'),
      );
      meals = await api.request('GET', '/meals');
      history = await api.request('GET', '/recommendations/history');
      consent = true;
    }
    final prefs = await api.request('GET', '/preferences');
    prep.text = '${prefs['maximum_preparation_minutes']}';
    gapWeight.text = '${prefs['weights']['gap_coverage'] ?? 0}';
    timeWeight.text = '${prefs['weights']['preparation_time'] ?? 0}';
    varietyWeight.text = '${prefs['weights']['variety'] ?? 0}';
    if (user?['role'] == 'admin') {
      revisions = await api.request('GET', '/admin/science/revisions');
    }
  }

  Widget field(
    String name,
    TextEditingController controller, {
    bool secret = false,
    int lines = 1,
  }) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 7),
    child: TextField(
      controller: controller,
      enabled: !busy,
      obscureText: secret,
      maxLines: lines,
      decoration: InputDecoration(labelText: name),
    ),
  );
  Widget button(
    String title,
    Future<void> Function() callback, {
    bool enabled = true,
  }) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 8),
    child: FilledButton(
      onPressed: busy || !enabled ? null : () => act(callback),
      child: Text(title),
    ),
  );
  Widget panel(List<Widget> children) => Card(
    child: Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: children,
      ),
    ),
  );
  Widget heading(String title, String subtitle) => Padding(
    padding: const EdgeInsets.only(bottom: 20),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: Theme.of(context).textTheme.headlineLarge
              ?.copyWith(fontWeight: FontWeight.w700),
        ),
        const SizedBox(height: 8),
        Text(subtitle),
      ],
    ),
  );
  Widget notice(String text) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 12),
    child: Text(text, style: const TextStyle(color: forest)),
  );
  Future<void> showDetails(String title, Object? details) async {
    if (!mounted) return;
    await showDialog<void>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(title),
        content: SingleChildScrollView(
          child: SelectableText(
            details is String
                ? details
                : const JsonEncoder.withIndent('  ').convert(details),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }

  Widget loginView() => Center(
    child: ConstrainedBox(
      constraints: const BoxConstraints(maxWidth: 490),
      child: panel([
        const Icon(Icons.spa_outlined, size: 52, color: forest),
        const SizedBox(height: 20),
        heading(
          'NutriTwin',
          'A clearer picture of what you eat, one day at a time.',
        ),
        field('Email', email),
        field('Password', password, secret: true),
        if (register)
          DropdownButtonFormField<String>(
            initialValue: role,
            decoration: const InputDecoration(labelText: 'Account type'),
            items: ['student', 'adult']
                .map((s) => DropdownMenuItem(value: s, child: Text(label(s))))
                .toList(),
            onChanged: busy ? null : (s) => setState(() => role = s!),
          ),
        if (register)
          const Text('Use at least 12 characters for your password.'),
        button(register ? 'Create account' : 'Sign in', () async {
          if (register) {
            await api.request(
              'POST',
              '/auth/register',
              body: {
                'email': email.text.trim(),
                'password': password.text,
                'role': role,
              },
            );
          }
          await api.login(email.text.trim(), password.text);
          password.clear();
          user = Map<String, dynamic>.from(
            await api.request('GET', '/users/me'),
          );
          await load();
        }),
        TextButton(
          onPressed: busy ? null : () => setState(() => register = !register),
          child: Text(
            register
                ? 'Already registered? Sign in'
                : 'Create a Student or Adult account',
          ),
        ),
        notice(
          'Academic prototype. Intake estimates are not diagnoses or measured absorption.',
        ),
      ]),
    ),
  );
  Widget navigation({bool drawer = false}) => Material(
    color: forest,
    child: SizedBox(
      width: 248,
      child: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Padding(
              padding: EdgeInsets.all(28),
              child: Text(
                '◉  NutriTwin',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 25,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
            for (int i = 0; i < (user?['role'] == 'admin' ? 5 : 4); i++)
              ListTile(
                selected: page == i,
                selectedTileColor: Colors.white12,
                leading: Icon(icons[i], color: Colors.white),
                title: Text(
                  pages[i],
                  style: const TextStyle(color: Colors.white),
                ),
                onTap: () {
                  setState(() => page = i);
                  if (drawer) Navigator.pop(context);
                },
              ),
            const Spacer(),
            Padding(
              padding: const EdgeInsets.all(20),
              child: Text(
                '${user?['email']}\n${user?['role']}',
                style: const TextStyle(color: Colors.white70),
              ),
            ),
            TextButton(
              onPressed: busy
                  ? null
                  : () => act(() async {
                      try {
                        await api.logout();
                      } finally {
                        user = null;
                        profile = null;
                        summary = null;
                        draft = [];
                        meals = [];
                        ranked = [];
                        history = [];
                        revisions = [];
                        constructed = null;
                      }
                    }),
              child: const Text(
                'Sign out',
                style: TextStyle(color: Colors.white),
              ),
            ),
            const SizedBox(height: 20),
          ],
        ),
      ),
    ),
  );
  @override
  Widget build(BuildContext context) {
    final wide = MediaQuery.sizeOf(context).width >= 960;
    final content = user == null
        ? loginView()
        : switch (page) {
            0 => overview(),
            1 => journal(),
            2 => planning(),
            3 => profileView(),
            _ => evidence(),
          };
    return Scaffold(
      appBar: user != null && !wide ? AppBar(title: Text(pages[page])) : null,
      drawer: user != null && !wide
          ? Drawer(child: navigation(drawer: true))
          : null,
      body: Row(
        children: [
          if (user != null && wide) navigation(),
          Expanded(
            child: Column(
              children: [
                if (busy)
                  const LinearProgressIndicator(
                    semanticsLabel: 'Loading NutriTwin',
                  ),
                if (error != null)
                  Semantics(
                    liveRegion: true,
                    child: Material(
                      color: const Color(0xFFFFE8E4),
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Row(
                          children: [
                            const Icon(Icons.error_outline),
                            const SizedBox(width: 12),
                            Expanded(child: Text(error!)),
                            IconButton(
                              tooltip: 'Dismiss error',
                              onPressed: () => setState(() => error = null),
                              icon: const Icon(Icons.close),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                Expanded(
                  child: SingleChildScrollView(
                    padding: EdgeInsets.all(wide ? 36 : 16),
                    child: content,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget overview() => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      heading(
        'See the bigger picture.',
        'Your nutrition journal • ${summary?['as_of_date'] ?? day(DateTime.now())}',
      ),
      if (summary == null)
        panel([
          const Text(
            'Complete your profile and consent to start your journal.',
          ),
          button('Set up profile', () async {
            page = 3;
          }),
        ])
      else ...[
        notice(
          summary!['target_provisional'] == true
              ? 'DEMO TARGETS • Synthetic reference values, not ICMR-NIN recommendations.'
              : 'Reviewed, versioned reference targets.',
        ),
        Wrap(
          spacing: 12,
          runSpacing: 12,
          children: [
            Chip(
              label: Text('${summary!['logged_days_30']} of 30 days logged'),
            ),
            const Chip(label: Text('Missing values remain unknown')),
            const Chip(label: Text('No LLM used')),
          ],
        ),
        button('Refresh overview', load),
        for (final n in orderedNutrients()) nutrientCard(n),
        notice(summary!['medical_disclaimer']),
      ],
    ],
  );
  List<dynamic> orderedNutrients() {
    final items = List<dynamic>.from(summary!['nutrients']);
    int priority(dynamic n) => n['consumed']['daily']['total_amount'] != null
        ? 0
        : n['target']['rda'] != null
        ? 1
        : 2;
    items.sort((a, b) {
      final difference = priority(a).compareTo(priority(b));
      return difference != 0
          ? difference
          : (a['nutrient_code'] as String).compareTo(b['nutrient_code']);
    });
    return items;
  }

  Widget nutrientCard(dynamic n) {
    final percent = number(n['consumed']['daily']['coverage_percent']);
    return panel([
      Text(
        label(n['nutrient_code']),
        style: Theme.of(context).textTheme.titleLarge,
      ),
      const SizedBox(height: 16),
      Wrap(
        spacing: 36,
        runSpacing: 16,
        children: [
          metric('Consumed', n['consumed']['daily']['total_amount'], n['unit']),
          metric(
            'Estimated effective',
            n['estimated_effective']['daily']['total_amount'],
            n['unit'],
          ),
          metric('Daily target', n['target']['rda'], n['unit']),
        ],
      ),
      const SizedBox(height: 20),
      if (percent != null)
        LinearProgressIndicator(
          value: (percent / 100).clamp(0, 1),
          minHeight: 8,
          color: chartColors[0],
          backgroundColor: paper,
          semanticsLabel: 'Consumed target coverage',
          semanticsValue: '$percent percent',
        ),
      const SizedBox(height: 12),
      Text(
        n['composition_complete_today'] == true
            ? 'Composition complete for logged foods.'
            : 'Incomplete log or food composition: totals may be lower bounds.',
      ),
      Wrap(
        spacing: 12,
        children: [
          for (final w in ['rolling_7_day', 'rolling_30_day'])
            Chip(
              label: Text(
                '${w == 'rolling_7_day' ? '7' : '30'} day coverage: ${shown(n['consumed'][w]['coverage_percent'])}${n['consumed'][w]['coverage_percent'] == null ? '' : '%'}',
              ),
            ),
        ],
      ),
      WeeklyChart(
        series: List<dynamic>.from(n['daily_series']),
        unit: n['unit'],
      ),
      ExpansionTile(
        title: const Text('Daily history and calculation explanation'),
        children: [
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: DataTable(
              columns: const [
                DataColumn(label: Text('Date')),
                DataColumn(label: Text('Consumed')),
                DataColumn(label: Text('Estimated effective')),
                DataColumn(label: Text('Target')),
                DataColumn(label: Text('Complete')),
              ],
              rows: [
                for (final d in n['daily_series'])
                  DataRow(
                    cells: [
                      for (final k in [
                        'date',
                        'consumed',
                        'estimated_effective',
                        'target',
                        'complete',
                      ])
                        DataCell(Text(shown(d[k]))),
                    ],
                  ),
              ],
            ),
          ),
          if (n['risk'] != null)
            ListTile(
              title: Text(n['risk']['wording']),
              subtitle: const Text(
                'Persistent intake-gap indication. Incomplete logs cannot establish deficiency.',
              ),
            ),
          button(
            'Inspect calculation trace',
            () => showDetails(
              'Calculation trace',
              n['estimated_effective']['calculation_trace'],
            ),
          ),
          if (n['risk'] != null)
            button(
              'Inspect score contributions',
              () => showDetails('Intake-gap indication', n['risk']),
            ),
        ],
      ),
    ]);
  }

  Widget metric(String title, dynamic value, String unit) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(title),
      Text(
        '${shown(value)} ${value == null ? '' : unit}',
        style: const TextStyle(fontSize: 23, fontWeight: FontWeight.w600),
      ),
    ],
  );
  Widget profileView() => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      heading(
        'Your profile',
        'Only the context needed for your nutrition journal.',
      ),
      panel([
        field('Birth date (YYYY-MM-DD)', birth),
        DropdownButtonFormField<String>(
          initialValue: sex,
          decoration: const InputDecoration(
            labelText: 'Reference-table sex category',
          ),
          items: ['', 'male', 'female']
              .map(
                (s) => DropdownMenuItem(
                  value: s,
                  child: Text(s.isEmpty ? 'Not provided' : s),
                ),
              )
              .toList(),
          onChanged: busy ? null : (s) => setState(() => sex = s!),
        ),
        const SizedBox(height: 16),
        DropdownButtonFormField<String>(
          initialValue: dietary,
          decoration: const InputDecoration(labelText: 'Dietary pattern'),
          items: [
            'unrestricted',
            'vegetarian',
            'vegan',
          ].map((s) => DropdownMenuItem(value: s, child: Text(s))).toList(),
          onChanged: busy ? null : (s) => setState(() => dietary = s!),
        ),
        field('Allergens, separated by commas', allergens),
        CheckboxListTile(
          value: consent,
          onChanged: busy ? null : (v) => setState(() => consent = v!),
          title: const Text(
            'I consent to storing my profile and food journal for the core application.',
          ),
          subtitle: const Text(
            'Academic, non-diagnostic prototype. No research sharing is included in this consent.',
          ),
        ),
        button('Save profile and consent', () async {
          await api.request(
            'POST',
            '/consents',
            body: {'document_version': 'core-consent-v1', 'granted': true},
          );
          await api.request(
            'PUT',
            '/profiles/me',
            body: {
              'birth_date': birth.text.trim(),
              'source_sex_category': sex.isEmpty ? null : sex,
              'activity_level': profile?['activity_level'],
              'dietary_pattern': dietary,
              'allergens': allergens.text.split(','),
            },
          );
          await load();
          page = 0;
        }, enabled: consent),
        button('Withdraw core consent', () async {
          await api.request(
            'POST',
            '/consents',
            body: {'document_version': 'core-consent-v1', 'granted': false},
          );
          consent = false;
          summary = null;
          meals = [];
          draft = [];
          ranked = [];
          history = [];
        }),
        notice(
          'Historical calculations retain their recorded profile and target versions. Changes apply from today.',
        ),
      ]),
    ],
  );
  void resetDraft() {
    draftEpoch++;
    editId = null;
    editRevision = null;
    draft = [];
    mealName.text = 'My meal';
    mealDate.text = day(DateTime.now());
    mealTime.text = '12:00';
  }

  Widget journal() => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      heading(
        'Food journal',
        'Search a source, choose an amount, and save what you ate.',
      ),
      button('Refresh journal', () async {
        meals = await api.request('GET', '/meals');
      }),
      panel([
        field('Search foods', search),
        button('Search', () async {
          foods = await api.request(
            'GET',
            '/foods?query=${Uri.encodeQueryComponent(search.text.trim())}',
          );
        }, enabled: consent),
        for (final f in foods)
          ListTile(
            contentPadding: EdgeInsets.zero,
            title: Text(f['name']),
            subtitle: Text(
              '${f['source_code']} • ${(f['nutrients'] as List).where((n) => n['amount_per_100g'] == null).length} missing nutrient values',
            ),
            trailing: IconButton(
              tooltip: 'Add ${f['name']} to draft',
              onPressed: busy
                  ? null
                  : () => setState(
                      () => draft.add({
                        'food_id': f['id'],
                        'name': f['name'],
                        'quantity_g': '100',
                      }),
                    ),
              icon: const Icon(Icons.add_circle_outline),
            ),
            onTap: () => showDetails('Food composition per 100 g', f),
          ),
      ]),
      panel([
        Text(
          editId == null ? 'Meal draft' : 'Edit logged meal',
          style: Theme.of(context).textTheme.titleLarge,
        ),
        if (editId != null)
          const Text(
            'If this meal changed elsewhere, your draft stays here. Refresh the journal to compare it with the saved meal, then select Edit on the latest meal before applying your changes.',
          ),
        field('Meal name', mealName),
        field('Meal date (YYYY-MM-DD)', mealDate),
        field('Local meal time (HH:mm)', mealTime),
        for (int i = 0; i < draft.length; i++)
          ListTile(
            contentPadding: EdgeInsets.zero,
            title: Text(draft[i]['name'] ?? 'Saved ingredient ${i + 1}'),
            subtitle: TextFormField(
              key: ValueKey(
                '${draftEpoch}_${editId}_${draft[i]['food_id']}_$i',
              ),
              initialValue: '${draft[i]['quantity_g']}',
              enabled: !busy,
              decoration: const InputDecoration(labelText: 'Grams'),
              onChanged: (v) => draft[i]['quantity_g'] = v,
            ),
            trailing: IconButton(
              tooltip: 'Remove ingredient',
              onPressed: busy ? null : () => setState(() => draft.removeAt(i)),
              icon: const Icon(Icons.close),
            ),
          ),
        button(editId == null ? 'Save meal' : 'Save changes', () async {
          final eaten = DateTime.parse(
            '${mealDate.text.trim()}T${mealTime.text.trim()}:00',
          );
          final payload = {
            'name': mealName.text.trim(),
            'local_date': mealDate.text.trim(),
            'eaten_at': eaten.toUtc().toIso8601String(),
            'ingredients': [
              for (final item in draft)
                {'food_id': item['food_id'], 'quantity_g': item['quantity_g']},
            ],
          };
          await api.request(
            editId == null ? 'POST' : 'PUT',
            editId == null
                ? '/meals'
                : '/meals/$editId?expected_revision=$editRevision',
            body: payload,
          );
          resetDraft();
          await load();
        }, enabled: draft.isNotEmpty && consent),
        button('Clear draft', () async {
          resetDraft();
        }),
      ]),
      for (final m in meals)
        panel([
          ListTile(
            contentPadding: EdgeInsets.zero,
            title: Text(m['name']),
            subtitle: Text(
              '${m['local_date']} • ${(m['ingredients'] as List).length} ingredients • revision ${m['revision']}',
            ),
            trailing: Wrap(
              children: [
                IconButton(
                  tooltip: 'Edit meal',
                  onPressed: busy
                      ? null
                      : () => setState(() {
                          draftEpoch++;
                          editId = m['id'];
                          editRevision = m['revision'];
                          mealName.text = m['name'];
                          mealDate.text = m['local_date'];
                          mealTime.text = DateTime.parse(m['eaten_at'])
                              .toLocal()
                              .toIso8601String()
                              .substring(11, 16);
                          draft = [
                            for (final i in m['ingredients'])
                              Map<String, dynamic>.from(i),
                          ];
                        }),
                  icon: const Icon(Icons.edit_outlined),
                ),
                IconButton(
                  tooltip: 'Delete meal',
                  onPressed: busy
                      ? null
                      : () => act(() async {
                          final yes = await showDialog<bool>(
                            context: context,
                            builder: (c) => AlertDialog(
                              title: const Text('Delete this meal?'),
                              content: const Text(
                                'Your daily and rolling calculations will be recalculated.',
                              ),
                              actions: [
                                TextButton(
                                  onPressed: () => Navigator.pop(c, false),
                                  child: const Text('Cancel'),
                                ),
                                FilledButton(
                                  onPressed: () => Navigator.pop(c, true),
                                  child: const Text('Delete'),
                                ),
                              ],
                            ),
                          );
                          if (yes == true) {
                            await api.request(
                              'DELETE',
                              '/meals/${m['id']}?expected_revision=${m['revision']}',
                            );
                            await load();
                          }
                        }),
                  icon: const Icon(Icons.delete_outline),
                ),
              ],
            ),
          ),
        ]),
    ],
  );
  Widget planning() => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      heading(
        'Make room for a better meal.',
        'Compare transparent choices and review a draft before logging.',
      ),
      panel([
        Text(
          'Planning preferences',
          style: Theme.of(context).textTheme.titleLarge,
        ),
        field('Maximum preparation minutes', prep),
        field('Gap coverage importance', gapWeight),
        field('Preparation time importance', timeWeight),
        field('Variety importance', varietyWeight),
        button('Save preferences', () async {
          await api.request(
            'PUT',
            '/preferences',
            body: {
              'weights': {
                'gap_coverage': gapWeight.text,
                'preparation_time': timeWeight.text,
                'variety': varietyWeight.text,
              },
              'maximum_preparation_minutes': int.parse(prep.text),
            },
          );
        }),
        button('Compare demo meals', () async {
          final result = await api.request('GET', '/recommendations');
          ranked = [
            ...result['recommendations'],
            ...result['rejected_candidates'],
          ];
          history = await api.request('GET', '/recommendations/history');
        }),
        for (final r in ranked)
          ExpansionTile(
            title: Text(r['candidate_name']),
            subtitle: Text(
              r['accepted'] == true
                  ? 'Score ${r['score']}'
                  : 'Rejected: ${(r['rejection_reasons'] as List).join(', ')}',
            ),
            children: [
              Padding(
                padding: const EdgeInsets.all(16),
                child: Text(r['explanation']),
              ),
              button(
                'Inspect ranking factors',
                () => showDetails('Ranking factors', r),
              ),
            ],
          ),
        notice(
          'The comparison templates and their composition are synthetic demonstrations.',
        ),
      ]),
      panel([
        Text('Construct a meal', style: Theme.of(context).textTheme.titleLarge),
        SwitchListTile(
          value: demo,
          onChanged: busy ? null : (v) => setState(() => demo = v),
          title: const Text('Use synthetic demo foods and prices'),
        ),
        notice(
          demo
              ? 'DEMO • These inputs demonstrate the solver; they are not dietary targets.'
              : 'Real-data planning requires reviewed authoritative targets, complete logged composition, and fresh manual INR prices.',
        ),
        field('Minimum iron (mg)', iron),
        field('Minimum vitamin C (mg)', vitaminC),
        field('Maximum budget (INR)', budget),
        button('Find a compliant meal', () async {
          constructed = Map<String, dynamic>.from(
            await api.request(
              'POST',
              '/recommendations/construct',
              body: {
                'demo_mode': demo,
                'derive_from_gaps': !demo,
                'nutrient_minimums': {
                  'iron': iron.text,
                  'vitamin_c': vitaminC.text,
                },
                'maximum_budget_minor': (double.parse(budget.text) * 100)
                    .round(),
                'maximum_preparation_minutes': int.parse(prep.text),
              },
            ),
          );
          history = await api.request('GET', '/recommendations/history');
        }),
        if (constructed != null) ...[
          Text(
            'Result: ${constructed!['status']}',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          notice(constructed!['notice']),
          Text(constructed!['trace']['explanation']),
          for (final s in constructed!['servings'])
            ListTile(
              title: Text(s['name']),
              subtitle: Text('${s['quantity_g']} g'),
            ),
          Text(
            'Total cost: INR ${((number(constructed!['total_cost_minor']) ?? 0) / 100).toStringAsFixed(2)}',
          ),
          button('Use as a journal draft', () async {
            resetDraft();
            mealName.text = demo ? 'DEMO constructed meal' : 'Constructed meal';
            draft = [
              for (final s in constructed!['servings'])
                {
                  'food_id': s['food_id'],
                  'name': s['name'],
                  'quantity_g': '${s['quantity_g']}',
                },
            ];
            page = 1;
          }, enabled: (constructed!['servings'] as List).isNotEmpty),
          button(
            'Inspect construction trace',
            () =>
                showDetails('Construction explanation', constructed!['trace']),
          ),
        ],
      ]),
      panel([
        FoodPrices(api: api),
        const SizedBox(height: 24),
        Text('Decision history', style: Theme.of(context).textTheme.titleLarge),
        if (history.isEmpty)
          const Text('Your saved planning decisions will appear here.'),
        for (final h in history)
          ListTile(
            title: Text(label(h['candidate_id'])),
            subtitle: Text(
              '${h['date']} • ${h['accepted'] ? 'accepted' : 'rejected'}',
            ),
            trailing: const Icon(Icons.chevron_right),
            onTap: busy
                ? null
                : () => act(() async {
                    final d = await api.request(
                      'GET',
                      '/recommendations/${h['id']}/explain',
                    );
                    await showDetails('Saved explanation', d);
                  }),
          ),
      ]),
    ],
  );
  Widget evidence() => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      heading(
        'Scientific evidence review',
        'Versioned submissions, separate approval, explicit activation.',
      ),
      notice(
        'Quantitative rules remain inactive until reviewed. Qualitative evidence never changes totals.',
      ),
      panel([
        field('Scientific proposal (JSON)', proposal, lines: 8),
        button('Submit proposal', () async {
          await api.request(
            'POST',
            '/admin/science/revisions',
            body: jsonDecode(proposal.text),
          );
          revisions = await api.request('GET', '/admin/science/revisions');
          proposal.clear();
        }),
        field('Review record (at least 20 characters)', reviewNote, lines: 3),
        button('Refresh evidence', () async {
          revisions = await api.request('GET', '/admin/science/revisions');
        }),
      ]),
      for (final r in revisions)
        panel([
          Text(
            '${r['kind']} • ${r['status']}',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          Text('Effective from ${r['effective_from']}'),
          button(
            'Inspect immutable proposal',
            () => showDetails('Scientific revision', r),
          ),
          for (final action in switch (r['status']) {
            'submitted' => ['approve', 'reject'],
            'approved' => ['activate'],
            'active' => ['retire'],
            _ => <String>[],
          })
            button(label(action), () async {
              await api.request(
                'POST',
                '/admin/science/revisions/${r['id']}/review',
                body: {'action': action, 'review_record': reviewNote.text},
              );
              revisions = await api.request('GET', '/admin/science/revisions');
            }),
        ]),
    ],
  );
}
