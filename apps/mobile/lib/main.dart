import 'composition_analytics.dart';
import 'mobile_experience.dart';

import 'package:flutter/foundation.dart';

import 'dart:convert';

import 'package:flutter/material.dart';

import 'api.dart';
import 'dishes.dart';
import 'dashboard_widgets.dart';
import 'prices.dart';
import 'weekly_chart.dart';
import 'nutrient_explorer.dart';
import 'nutrient_stats_selector.dart';
import 'palettes.dart';
import 'intake_alerts.dart';
import 'palette_storage_stub.dart'
    if (dart.library.js_interop) 'palette_storage_web.dart'
    as palette_storage;

void main() => runApp(const NutriTwinApp());
const forest = Color(0xFF244F3D);
const paper = Color(0xFFF7F8F2);
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

class NutriTwinApp extends StatefulWidget {
  final NutriApi? api;
  const NutriTwinApp({super.key, this.api});
  @override
  State<NutriTwinApp> createState() => _NutriTwinAppState();
}

class _NutriTwinAppState extends State<NutriTwinApp> {
  late final NutriApi api = widget.api ?? NutriApi();
  AppPalette palette = paletteById(
    palette_storage.readPalette() ??
        (!kIsWeb && defaultTargetPlatform == TargetPlatform.android
            ? 'mobile'
            : null),
  );
  @override
  Widget build(BuildContext context) => MaterialApp(
    title: 'NutriTwin',
    debugShowCheckedModeBanner: false,
    theme: palette.theme,
    home: TwinHome(
      api: api,
      palette: palette,
      onPaletteChanged: (id) {
        setState(() => palette = paletteById(id));
        return palette_storage.writePalette(id);
      },
    ),
  );
}

class TwinHome extends StatefulWidget {
  final NutriApi api;
  final AppPalette palette;
  final bool Function(String) onPaletteChanged;
  const TwinHome({
    super.key,
    required this.api,
    required this.palette,
    required this.onPaletteChanged,
  });
  @override
  State<TwinHome> createState() => _TwinHomeState();
}

class _TwinHomeState extends State<TwinHome> {
  final email = TextEditingController(), password = TextEditingController();
  final birth = TextEditingController(), allergens = TextEditingController();
  final search = TextEditingController(),
      mealName = TextEditingController(text: 'My meal');
  String? journalDay;
  bool manualJournal = false;
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
  Map<String, dynamic>? dishEditMeal;
  int? editRevision;
  String dietary = 'unrestricted', sex = '', role = 'student';
  bool busy = false, register = false, consent = false, demo = true;
  int page = 0;
  bool get compact => MediaQuery.sizeOf(context).width < 960;
  void openMobilePage(int next) => setState(() {
    page = next;
    if (next == 1) {
      journalDay ??= day(DateTime.now());
    }
  });
  Future<void> serverSettings() async {
    final value = await showDialog<String>(
      context: context,
      builder: (_) => ServerDialog(initial: api.baseUrl),
    );
    if (value != null && mounted) {
      setState(() {
        api.clear();
        api.baseUrl = value;
      });
    }
  }

  Future<void> mobileAdd() async {
    final next = await showModalBottomSheet<int>(
      context: context,
      showDragHandle: true,
      builder: (c) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const ListTile(
              title: Text(
                'Add to your diary',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
            ),
            ListTile(
              leading: const Icon(Icons.search),
              title: const Text('Food'),
              subtitle: const Text('Search foods and enter grams'),
              onTap: () => Navigator.pop(c, 1),
            ),
            ListTile(
              leading: const Icon(Icons.restaurant),
              title: const Text('Dish or recipe'),
              subtitle: const Text('Choose a dish and adjust portions'),
              onTap: () => Navigator.pop(c, 5),
            ),
          ],
        ),
      ),
    );
    if (next != null && mounted) {
      setState(() {
        page = next;
        if (next == 1) {
          manualJournal = true;
          journalDay ??= day(DateTime.now());
        }
      });
    }
  }

  String foodSourceKind = 'real';
  bool moreFoods = false;
  bool foodSearchCompleted = false;
  String? journalMessage;
  final draftAnchor = GlobalKey();
  String lastFoodQuery = '';
  String lastFoodSource = 'real';
  int draftEpoch = 0;
  NutriApi get api => widget.api;
  Future<void> changePalette() async {
    final id = await choosePalette(context, widget.palette.id);
    if (id == null || !mounted) return;
    final saved = widget.onPaletteChanged(id);
    if (!saved) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Palette applied for this session. Browser storage is unavailable.',
          ),
        ),
      );
    }
  }

  final pages = [
    'Overview',
    'Food journal',
    'Meal planning',
    'Profile',
    'Evidence review',
    'Dishes & recipes',
    'Meal composition',
    'Nutrient analytics',
  ];
  final icons = [
    Icons.dashboard_outlined,
    Icons.restaurant_outlined,
    Icons.auto_awesome_outlined,
    Icons.person_outline,
    Icons.fact_check_outlined,
    Icons.rice_bowl_outlined,
    Icons.pie_chart_outline,
    Icons.scatter_plot_outlined,
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
    String? hint,
    ValueChanged<String>? onSubmitted,
    Widget? suffixIcon,
  }) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 7),
    child: TextField(
      controller: controller,
      enabled: !busy,
      obscureText: secret,
      maxLines: lines,
      onSubmitted: onSubmitted,
      decoration: InputDecoration(
        labelText: name,
        hintText: hint,
        suffixIcon: suffixIcon,
      ),
    ),
  );
  Widget button(
    String title,
    Future<void> Function() callback, {
    bool enabled = true,
    bool primary = true,
  }) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 8),
    child: primary
        ? FilledButton(
            onPressed: busy || !enabled ? null : () => act(callback),
            child: Text(title),
          )
        : TextButton(
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
          style: Theme.of(context).textTheme.headlineMedium
              ?.copyWith(fontWeight: FontWeight.w700),
        ),
        const SizedBox(height: 8),
        Text(subtitle),
      ],
    ),
  );
  Widget notice(String text) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 12),
    child: Text(
      text,
      style: TextStyle(color: Theme.of(context).colorScheme.onSurface),
    ),
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

  Future<void> showFoodDetails(dynamic food) async {
    await showDialog<void>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(food['name']),
        content: SizedBox(
          width: 460,
          child: SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text('Source: ${food['source_code']}'),
                const SizedBox(height: 12),
                const Text(
                  'Composition per 100 g',
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
                const Text(
                  'Values describe the food as named. Missing values are unknown, not zero.',
                ),
                const SizedBox(height: 12),
                for (final nutrient in food['nutrients'])
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 6),
                    child: Row(
                      children: [
                        Expanded(child: Text(label(nutrient['nutrient_code']))),
                        const SizedBox(width: 12),
                        Text(
                          nutrient['amount_per_100g'] == null
                              ? 'Unknown'
                              : '${shown(nutrient['amount_per_100g'])} ${nutrient['unit']}',
                        ),
                      ],
                    ),
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
      ),
    );
  }

  Future<void> chooseMealDate() async {
    final now = DateTime.now();
    final parsed = DateTime.tryParse(mealDate.text);
    final earliest = DateTime(1900);
    final initial =
        parsed != null && !parsed.isAfter(now) && !parsed.isBefore(earliest)
        ? parsed
        : now;
    final selected = await showDatePicker(
      context: context,
      initialDate: initial,
      firstDate: earliest,
      lastDate: now,
    );
    if (selected != null && mounted) {
      setState(() => mealDate.text = day(selected));
    }
  }

  Future<void> chooseMealTime() async {
    final parts = mealTime.text.split(':');
    final hour = int.tryParse(parts.first);
    final minute = parts.length == 2 ? int.tryParse(parts.last) : null;
    final initial =
        hour != null &&
            minute != null &&
            hour >= 0 &&
            hour < 24 &&
            minute >= 0 &&
            minute < 60
        ? TimeOfDay(hour: hour, minute: minute)
        : TimeOfDay.now();
    final selected = await showTimePicker(
      context: context,
      initialTime: initial,
    );
    if (selected != null && mounted) {
      setState(
        () => mealTime.text =
            '${selected.hour.toString().padLeft(2, '0')}:${selected.minute.toString().padLeft(2, '0')}',
      );
    }
  }

  Widget loginView() => Center(
    child: ConstrainedBox(
      constraints: const BoxConstraints(maxWidth: 490),
      child: panel([
        Icon(
          Icons.spa_outlined,
          size: 52,
          color: Theme.of(context).colorScheme.onSurface,
        ),
        TextButton.icon(
          onPressed: changePalette,
          icon: const Icon(Icons.palette_outlined),
          label: const Text('Color palette'),
        ),
        const SizedBox(height: 20),
        heading(
          'NutriTwin',
          'A clearer picture of what you eat, one day at a time.',
        ),
        TextButton.icon(
          onPressed: busy ? null : serverSettings,
          icon: const Icon(Icons.dns_outlined),
          label: const Text('Server connection'),
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
    color: widget.palette.navigation,
    child: SizedBox(
      width: 236,
      child: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Padding(
              padding: EdgeInsets.fromLTRB(24, 24, 24, 10),
              child: Text(
                '◉  NutriTwin',
                style: TextStyle(
                  color: widget.palette.onNavigation,
                  fontSize: 25,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
            Expanded(
              child: ListView(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                children: [
                  for (final group in {
                    'YOUR DAY': [0, 5, 1],
                    'EXPLORE': [7, 6, 2],
                    'ACCOUNT': [3, if (user?['role'] == 'admin') 4],
                  }.entries) ...[
                    Padding(
                      padding: const EdgeInsets.fromLTRB(16, 18, 16, 8),
                      child: Text(
                        group.key,
                        style: TextStyle(
                          color: widget.palette.onNavigation,
                          fontSize: 10,
                          letterSpacing: 1.4,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                    for (final i in group.value)
                      Padding(
                        padding: const EdgeInsets.only(bottom: 4),
                        child: ListTile(
                          selected: page == i,
                          selectedTileColor: widget.palette.onNavigation
                              .withValues(alpha: .16),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(10),
                          ),
                          leading: Icon(
                            icons[i],
                            size: 21,
                            color: widget.palette.onNavigation,
                          ),
                          title: Text(
                            pages[i],
                            style: TextStyle(
                              color: widget.palette.onNavigation,
                              fontSize: 14,
                              fontWeight: page == i
                                  ? FontWeight.w700
                                  : FontWeight.w400,
                            ),
                          ),
                          onTap: () {
                            setState(() => page = i);
                            if (drawer) Navigator.pop(context);
                          },
                        ),
                      ),
                  ],
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(20),
              child: Text(
                '${user?['email']}\n${user?['role']}',
                style: TextStyle(color: widget.palette.onNavigation),
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
                        foods = [];
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
              child: Text(
                'Sign out',
                style: TextStyle(color: widget.palette.onNavigation),
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
            0 =>
              wide
                  ? overview()
                  : MobileDashboard(
                      summary: summary,
                      meals: meals,
                      onOpen: openMobilePage,
                      onAdd: mobileAdd,
                    ),
            1 =>
              !wide && !manualJournal
                  ? MobileDiary(
                      meals: meals,
                      selectedDay: journalDay ?? day(DateTime.now()),
                      onDate: (d) => setState(() => journalDay = d),
                      onAdd: mobileAdd,
                      onEdit: (m) => setState(() {
                        manualJournal = true;
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
                      onManage: () => setState(() => manualJournal = true),
                    )
                  : journal(),
            8 => MobileMore(
              email: user?['email'] ?? '',
              admin: user?['role'] == 'admin',
              onOpen: openMobilePage,
              onPalette: changePalette,
              onLogout: () => act(() async {
                try {
                  await api.logout();
                } finally {
                  user = null;
                  profile = null;
                  summary = null;
                  meals = [];
                  draft = [];
                  foods = [];
                  ranked = [];
                  history = [];
                  revisions = [];
                  constructed = null;
                  dishEditMeal = null;
                }
              }),
            ),
            2 => planning(),
            3 => profileView(),
            5 => DishWorkspace(
              key: ValueKey('${user?['id']}:${dishEditMeal?['id']}'),
              api: api,
              admin: user?['role'] == 'admin',
              initialMeal: dishEditMeal,
              onChanged: () async {
                await load();
                if (mounted) setState(() {});
              },
            ),
            6 => MealCompositionPage(
              api: api,
              meals: meals,
              onEdit: (m) => setState(() {
                dishEditMeal = m;
                page = 5;
              }),
            ),
            7 => CompositionAnalyticsPage(
              api: api,
              onOpenPlateBuilder: () => setState(() => page = 6),
            ),
            _ => evidence(),
          };
    return Scaffold(
      appBar: user != null && !wide
          ? AppBar(
              automaticallyImplyLeading: false,
              title: Text(
                page == 0 || page == 7 || page == 6
                    ? 'NutriTwin'
                    : page == 1
                    ? 'Diary'
                    : page == 5
                    ? 'Foods'
                    : page == 8
                    ? 'More'
                    : pages[page],
              ),
              bottom: [0, 7, 6].contains(page)
                  ? PreferredSize(
                      preferredSize: const Size.fromHeight(48),
                      child: MobileDiscoverTabs(
                        page: page,
                        onOpen: openMobilePage,
                      ),
                    )
                  : null,
              actions: [
                IconButton(
                  onPressed: changePalette,
                  tooltip: 'Color palette',
                  icon: const Icon(Icons.palette_outlined),
                ),
              ],
            )
          : null,
      bottomNavigationBar: user != null && !wide
          ? MobileBottomBar(
              page: page,
              onOpen: openMobilePage,
              onAdd: mobileAdd,
            )
          : null,
      body: SafeArea(
        child: Row(
          children: [
            if (user != null && wide) navigation(),
            Expanded(
              child: Column(
                children: [
                  if (user != null && wide)
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 28,
                        vertical: 14,
                      ),
                      decoration: BoxDecoration(
                        color: Theme.of(context).colorScheme.surface,
                        border: Border(
                          bottom: BorderSide(
                            color: Theme.of(context).colorScheme.outlineVariant,
                          ),
                        ),
                      ),
                      child: Row(
                        children: [
                          Icon(icons[page], size: 19),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Text(
                              'NutriTwin  /  ${pages[page]}',
                              style: Theme.of(context).textTheme.labelLarge,
                            ),
                          ),
                          const Icon(Icons.calendar_today_outlined, size: 16),
                          const SizedBox(width: 8),
                          Text(summary?['as_of_date'] ?? day(DateTime.now())),
                          const SizedBox(width: 20),
                          TextButton.icon(
                            onPressed: changePalette,
                            label: const Text('Color palette'),
                            icon: const Icon(Icons.palette_outlined, size: 20),
                          ),
                          const SizedBox(width: 12),
                        ],
                      ),
                    ),
                  if (busy)
                    const LinearProgressIndicator(
                      semanticsLabel: 'Loading NutriTwin',
                    ),
                  if (error != null)
                    Semantics(
                      liveRegion: true,
                      child: Material(
                        color: Theme.of(context).colorScheme.errorContainer,
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Row(
                            children: [
                              const Icon(Icons.error_outline),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Text(
                                  error!,
                                  style: TextStyle(
                                    color: Theme.of(context)
                                        .colorScheme
                                        .onErrorContainer,
                                  ),
                                ),
                              ),
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
                      key: ValueKey(
                        'workspace-$page-${page == 1 && manualJournal}',
                      ),
                      primary: false,
                      padding: EdgeInsets.all(wide ? 28 : 16),
                      child: Align(
                        alignment: Alignment.topCenter,
                        child: ConstrainedBox(
                          constraints: const BoxConstraints(maxWidth: 1440),
                          child: SizedBox(
                            width: double.infinity,
                            child: content,
                          ),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget overview() => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      heading(
        'Nutrition overview',
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
        const SizedBox(height: 12),
        Wrap(
          spacing: 10,
          runSpacing: 10,
          children: [
            FilledButton.icon(
              onPressed: busy
                  ? null
                  : () => setState(() {
                      dishEditMeal = null;
                      page = 5;
                    }),
              icon: const Icon(Icons.add),
              label: const Text('Log food'),
            ),
            TextButton.icon(
              onPressed: busy ? null : () => act(load),
              icon: const Icon(Icons.refresh),
              label: const Text('Refresh overview'),
            ),
          ],
        ),
        const SizedBox(height: 24),
        JournalSummaryCards(
          mealsToday: meals
              .where((m) => m['local_date'] == summary!['as_of_date'])
              .length,
          loggedDays: summary!['logged_days_30'] ?? 0,
          alerts: orderedNutrients()
              .where(
                (n) => [
                  'watch',
                  'elevated',
                  'persistent',
                ].contains(n['risk']?['band']),
              )
              .length,
        ),
        const SizedBox(height: 24),
        WorkspaceColumns(
          primary: WorkspacePanel(
            child: NutrientStatsSelector(
              nutrients: orderedNutrients(),
              statsBuilder: nutrientCard,
            ),
          ),
          secondary: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              IntakeAlerts(
                nutrients: orderedNutrients(),
                provisional: summary!['target_provisional'] == true,
                onInspect: (n) => showDialog<void>(
                  context: context,
                  builder: (_) => IntakeRiskDetails(
                    nutrient: n,
                    provisional: summary!['target_provisional'] == true,
                  ),
                ),
              ),
              const SizedBox(height: 12),
              const WorkspacePanel(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Reading your journal',
                      style: TextStyle(fontWeight: FontWeight.w600),
                    ),
                    SizedBox(height: 8),
                    Text(
                      'Missing values remain unknown. A logged day does not mean every meal or nutrient was recorded.',
                    ),
                    SizedBox(height: 8),
                    Text('No LLM used in nutrition calculations.'),
                  ],
                ),
              ),
            ],
          ),
        ),
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
          backgroundColor: Theme.of(context).colorScheme.surface,
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
      if (profile != null)
        panel([
          Text(
            'Your food history',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          Text(
            '${meals.length} saved meals · ${summary?['logged_days_30'] ?? 0} of 30 days logged',
          ),
          for (final m in meals.take(5))
            ListTile(title: Text(m['name']), subtitle: Text(m['local_date'])),
          button('View composition and nutrients', () async {
            page = 6;
          }),
        ]),
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
    mealDate.text = journalDay ?? day(DateTime.now());
    mealTime.text = '12:00';
  }

  Future<void> searchFoods() async {
    final query = search.text.trim();
    final source = foodSourceKind;
    final result = await api.request(
      'GET',
      '/foods?query=${Uri.encodeQueryComponent(query)}&source_kind=$source&limit=25',
    );
    lastFoodQuery = query;
    lastFoodSource = source;
    foods = result;
    moreFoods = foods.length == 25;
    foodSearchCompleted = true;
  }

  void reviewDraft() {
    setState(() => manualJournal = true);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      final target = draftAnchor.currentContext;
      if (target != null) {
        Scrollable.ensureVisible(
          target,
          duration: const Duration(milliseconds: 250),
        );
      }
    });
  }

  String? validateMealDraft() {
    if (mealName.text.trim().isEmpty) {
      return 'Give this meal a name before saving.';
    }
    final value = mealDate.text.trim();
    final date = DateTime.tryParse(value);
    if (!RegExp(r'^\d{4}-\d{2}-\d{2}$').hasMatch(value) ||
        date == null ||
        day(date) != value) {
      return 'Enter a valid meal date as YYYY-MM-DD.';
    }
    if (value.compareTo(day(DateTime.now())) > 0) {
      return 'Choose today or a past date for a meal you have eaten.';
    }
    if (!RegExp(r'^([01]\d|2[0-3]):[0-5]\d$').hasMatch(mealTime.text.trim())) {
      return 'Enter a valid local time as HH:mm, for example 12:30.';
    }
    for (final item in draft) {
      final grams = '${item['quantity_g']}'.trim();
      final amount = double.tryParse(grams);
      if (amount == null || !amount.isFinite || amount <= 0) {
        return 'Enter a gram amount greater than zero for ${item['name'] ?? 'each ingredient'}.';
      }
    }
    return null;
  }

  Future<void> chooseJournalDay() async {
    final selected = await showDatePicker(
      context: context,
      initialDate: DateTime.tryParse(journalDay ?? '') ?? DateTime.now(),
      firstDate: DateTime(1900),
      lastDate: DateTime(2100),
    );
    if (selected != null && mounted) {
      setState(() {
        journalDay = day(selected);
        if (editId == null) mealDate.text = journalDay!;
      });
    }
  }

  Future<void> moveMealDate(dynamic meal) async {
    final selected = await showDatePicker(
      context: context,
      initialDate: DateTime.parse(meal['local_date']),
      firstDate: DateTime(1900),
      lastDate: DateTime(2100),
    );
    if (selected == null || !mounted) return;
    final previousTime = DateTime.parse(meal['eaten_at']).toLocal();
    final at = DateTime(
      selected.year,
      selected.month,
      selected.day,
      previousTime.hour,
      previousTime.minute,
      previousTime.second,
    );
    await api.request(
      'PATCH',
      '/meals/${meal['id']}/date?expected_revision=${meal['revision']}',
      body: {
        'local_date': day(selected),
        'eaten_at': at.toUtc().toIso8601String(),
      },
    );
    journalDay = day(selected);
    journalMessage =
        '${meal['name']} moved to $journalDay. Both dates will be recalculated.';
    await load();
  }

  Future<void> clearJournal({required bool all}) async {
    final snapshot = meals
        .where((m) => all || m['local_date'] == journalDay)
        .toList();
    if (snapshot.isEmpty) return;
    final yes = await showDialog<bool>(
      context: context,
      builder: (c) => AlertDialog(
        title: Text(all ? 'Remove all journal entries?' : 'Clear $journalDay?'),
        content: Text(
          'Remove ${snapshot.length} saved meal entries${all ? ' across all dates' : ' on $journalDay'}? Your intake history and alerts will be recalculated. Your profile, recipes and datasets are kept. This cannot be undone in the app.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(c, false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(c, true),
            child: const Text('Remove entries'),
          ),
        ],
      ),
    );
    if (yes != true) return;
    await api.request(
      'POST',
      '/meals/batch-delete',
      body: {
        'entries': [
          for (final m in snapshot) {'id': m['id'], 'revision': m['revision']},
        ],
      },
    );
    if (snapshot.any((m) => m['id'] == editId)) resetDraft();
    journalMessage = '${snapshot.length} journal entries removed.';
    await load();
  }

  Widget journal() => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      heading(
        'Food journal',
        'Review saved meals by date, or build a meal from individual foods.',
      ),
      Wrap(
        spacing: 8,
        runSpacing: 8,
        children: [
          ChoiceChip(
            label: const Text('Saved entries'),
            selected: !manualJournal,
            onSelected: (_) => setState(() => manualJournal = false),
          ),
          ChoiceChip(
            label: const Text('Build a meal'),
            selected: manualJournal,
            onSelected: (_) => setState(() => manualJournal = true),
          ),
        ],
      ),
      const SizedBox(height: 16),
      if (!manualJournal)
        panel([
          Text('Browse by day', style: Theme.of(context).textTheme.titleLarge),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              OutlinedButton.icon(
                onPressed: busy ? null : chooseJournalDay,
                icon: const Icon(Icons.calendar_month_outlined),
                label: Text(journalDay ?? 'Choose a date'),
              ),
              TextButton(
                onPressed: busy
                    ? null
                    : () => setState(() => journalDay = day(DateTime.now())),
                child: const Text('Today'),
              ),
              TextButton(
                onPressed: busy
                    ? null
                    : () => setState(() => journalDay = null),
                child: const Text('All dates'),
              ),
              if (journalDay != null)
                OutlinedButton.icon(
                  onPressed:
                      busy || !meals.any((m) => m['local_date'] == journalDay)
                      ? null
                      : () => act(() => clearJournal(all: false)),
                  icon: const Icon(Icons.delete_sweep_outlined),
                  label: const Text('Clear selected day'),
                ),
              OutlinedButton.icon(
                onPressed: busy || meals.isEmpty
                    ? null
                    : () => act(() => clearJournal(all: true)),
                icon: const Icon(Icons.delete_forever_outlined),
                label: const Text('Remove all entries'),
              ),
            ],
          ),
          Text(
            journalDay == null
                ? '${meals.length} saved meals across all dates'
                : '${meals.where((m) => m['local_date'] == journalDay).length} saved meals on $journalDay',
          ),
        ]),
      Wrap(
        spacing: 10,
        runSpacing: 8,
        crossAxisAlignment: WrapCrossAlignment.center,
        children: [
          TextButton.icon(
            onPressed: busy
                ? null
                : () => act(() async {
                    meals = await api.request('GET', '/meals');
                  }),
            icon: const Icon(Icons.refresh),
            label: const Text('Refresh journal'),
          ),
        ],
      ),
      const SizedBox(height: 16),
      if (!consent)
        notice(
          'Complete your profile and consent in Profile to start logging meals.',
        ),
      if (journalMessage != null)
        Semantics(liveRegion: true, child: notice(journalMessage!)),
      if (draft.isNotEmpty && !manualJournal)
        OutlinedButton.icon(
          onPressed: reviewDraft,
          icon: const Icon(Icons.receipt_long_outlined),
          label: Text(
            'Review draft · ${draft.length} ${draft.length == 1 ? 'ingredient' : 'ingredients'}',
          ),
        ),
      Offstage(
        offstage: manualJournal,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              journalDay == null
                  ? 'Saved meals · all dates'
                  : 'Saved meals · $journalDay',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            if (journalDay != null &&
                !meals.any((m) => m['local_date'] == journalDay))
              notice(
                'No entries on this date. Choose another day or add a meal.',
              ),
            if (meals.isEmpty)
              notice(
                'No meals logged yet. Save your first meal to start your nutrition history.',
              ),
            for (final m in meals.where(
              (m) => journalDay == null || m['local_date'] == journalDay,
            ))
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
                                manualJournal = true;
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
                        tooltip: 'Change meal date',
                        onPressed: busy
                            ? null
                            : () => act(() => moveMealDate(m)),
                        icon: const Icon(Icons.event_outlined),
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
                                        onPressed: () =>
                                            Navigator.pop(c, false),
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
        ),
      ),
      Offstage(
        offstage: !manualJournal,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 24),
            Text(
              'Build a meal manually',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const Text(
              'Choose individual foods and review their amounts before saving.',
            ),
            const SizedBox(height: 12),
            panel([
              Text(
                '1. Find a food',
                style: Theme.of(context).textTheme.titleLarge,
              ),
              field(
                'Search foods',
                search,
                hint: 'Try lentils, rice or spinach',
                onSubmitted: (_) {
                  if (consent) act(searchFoods);
                },
              ),
              DropdownButtonFormField<String>(
                initialValue: foodSourceKind,
                decoration: const InputDecoration(labelText: 'Food dataset'),
                items: const [
                  DropdownMenuItem(
                    value: 'real',
                    child: Text('Real source data'),
                  ),
                  DropdownMenuItem(
                    value: 'demo',
                    child: Text('Synthetic demo foods'),
                  ),
                  DropdownMenuItem(value: 'all', child: Text('All datasets')),
                ],
                onChanged: busy
                    ? null
                    : (v) => setState(() {
                        foodSourceKind = v!;
                        foods = [];
                        moreFoods = false;
                        foodSearchCompleted = false;
                      }),
              ),
              notice(
                'USDA foods retain their raw, dry or prepared descriptions. Choose the state you actually weighed; Indian targets remain a separate reference.',
              ),
              button(
                'Dataset provenance',
                () async {
                  final sources = await api.request('GET', '/food-sources');
                  await showDetails('Installed food datasets', sources);
                },
                enabled: consent,
                primary: false,
              ),
              button('Search', searchFoods, enabled: consent),
              if (!foodSearchCompleted)
                const Text(
                  'Search by name, or leave the search empty to browse foods.',
                ),
              if (foodSearchCompleted && foods.isEmpty)
                const Text(
                  'No foods found. Try a shorter name or choose another dataset.',
                ),
              if (foods.isNotEmpty)
                Text(
                  '${foods.length} foods loaded · comparison covers these results',
                ),
              if (foods.isNotEmpty)
                FoodNutrientExplorer(
                  foods: foods,
                  onInspect: showFoodDetails,
                  onAdd: busy
                      ? null
                      : (f) => setState(() {
                          draft.add({
                            'food_id': f['id'],
                            'name': f['name'],
                            'quantity_g': '100',
                          });
                          journalMessage =
                              '${f['name']} added to your draft at 100 g. Review the amount before saving.';
                        }),
                ),
              if (moreFoods)
                button('Load more foods', () async {
                  final next = await api.request(
                    'GET',
                    '/foods?query=${Uri.encodeQueryComponent(lastFoodQuery)}&source_kind=$lastFoodSource&limit=25&offset=${foods.length}',
                  );
                  foods = [...foods, ...next];
                  moreFoods = next.length == 25;
                }, enabled: consent),
            ]),
            panel([
              Text(
                editId == null ? 'Meal draft' : 'Edit logged meal',
                key: draftAnchor,
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const Text(
                '2. Review amounts · Your draft is not logged until you save it.',
              ),
              if (draft.isEmpty)
                notice(
                  'Your draft is empty. Use Add food in the search results above.',
                ),
              if (editId != null)
                const Text(
                  'If this meal changed elsewhere, your draft stays here. Refresh the journal to compare it with the saved meal, then select Edit on the latest meal before applying your changes.',
                ),
              field('Meal name', mealName),
              field(
                'Meal date (YYYY-MM-DD)',
                mealDate,
                suffixIcon: IconButton(
                  tooltip: 'Choose meal date',
                  onPressed: busy ? null : chooseMealDate,
                  icon: const Icon(Icons.calendar_month_outlined),
                ),
              ),
              field(
                'Local meal time (HH:mm)',
                mealTime,
                suffixIcon: IconButton(
                  tooltip: 'Choose meal time',
                  onPressed: busy ? null : chooseMealTime,
                  icon: const Icon(Icons.schedule),
                ),
              ),
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
                    keyboardType: const TextInputType.numberWithOptions(
                      decimal: true,
                    ),
                    onChanged: (v) => draft[i]['quantity_g'] = v,
                  ),
                  trailing: IconButton(
                    tooltip: 'Remove ingredient',
                    onPressed: busy
                        ? null
                        : () => setState(() => draft.removeAt(i)),
                    icon: const Icon(Icons.close),
                  ),
                ),
              button(editId == null ? 'Save meal' : 'Save changes', () async {
                final validation = validateMealDraft();
                if (validation != null) {
                  error = validation;
                  return;
                }
                final savedName = mealName.text.trim();
                final eaten = DateTime.parse(
                  '${mealDate.text.trim()}T${mealTime.text.trim()}:00',
                );
                final payload = {
                  'name': mealName.text.trim(),
                  'local_date': mealDate.text.trim(),
                  'eaten_at': eaten.toUtc().toIso8601String(),
                  'ingredients': [
                    for (final item in draft)
                      {
                        'food_id': item['food_id'],
                        'quantity_g': item['quantity_g'],
                      },
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
                journalMessage =
                    '$savedName saved. Your nutrition overview will reflect this meal.';
                await load();
              }, enabled: draft.isNotEmpty && consent),
              button('Clear draft', () async {
                resetDraft();
                journalMessage =
                    'Draft cleared. Your saved meals are unchanged.';
              }),
            ]),
          ],
        ),
      ),
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
            manualJournal = true;
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
