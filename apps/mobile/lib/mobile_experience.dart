import 'package:flutter/material.dart';

const mobileOrange = Color(0xFFF47735);
const mobileTeal = Color(0xFF176A68);

class MobileBottomBar extends StatelessWidget {
  final int page;
  final ValueChanged<int> onOpen;
  final VoidCallback onAdd;
  const MobileBottomBar({
    super.key,
    required this.page,
    required this.onOpen,
    required this.onAdd,
  });
  @override
  Widget build(BuildContext context) => Material(
    color: Theme.of(context).colorScheme.surface,
    elevation: 8,
    borderRadius: const BorderRadius.vertical(top: Radius.circular(22)),
    child: SafeArea(
      top: false,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 8),
        child: Row(
          children: [
            item(
              context,
              'Discover',
              Icons.bar_chart_rounded,
              0,
              [0, 6, 7].contains(page),
            ),
            item(context, 'Diary', Icons.receipt_long, 1, page == 1),
            Expanded(
              child: Center(
                heightFactor: 1,
                child: IconButton.filled(
                  style: IconButton.styleFrom(
                    backgroundColor: mobileOrange,
                    foregroundColor: Colors.white,
                    minimumSize: const Size(56, 56),
                  ),
                  tooltip: 'Add to diary',
                  onPressed: onAdd,
                  icon: const Icon(Icons.add, size: 36),
                ),
              ),
            ),
            item(context, 'Foods', Icons.apple, 5, page == 5),
            item(
              context,
              'More',
              Icons.more_horiz,
              8,
              [2, 3, 4, 8].contains(page),
            ),
          ],
        ),
      ),
    ),
  );
  Widget item(
    BuildContext context,
    String name,
    IconData icon,
    int target,
    bool selected,
  ) => Expanded(
    child: Semantics(
      selected: selected,
      child: InkWell(
        onTap: () => onOpen(target),
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 8),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                icon,
                size: 27,
                color: selected
                    ? Theme.of(context).colorScheme.primary
                    : Colors.grey.shade600,
              ),
              const SizedBox(height: 4),
              Text(
                name,
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: selected ? FontWeight.bold : FontWeight.normal,
                  color: selected
                      ? Theme.of(context).colorScheme.primary
                      : Theme.of(context).colorScheme.onSurface,
                ),
              ),
            ],
          ),
        ),
      ),
    ),
  );
}

class MobileDiscoverTabs extends StatelessWidget {
  final int page;
  final ValueChanged<int> onOpen;
  const MobileDiscoverTabs({
    super.key,
    required this.page,
    required this.onOpen,
  });
  @override
  Widget build(BuildContext context) => Row(
    children: [
      for (final tab in {0: 'Dashboard', 7: 'Charts', 6: 'Report'}.entries)
        Expanded(
          child: InkWell(
            onTap: () => onOpen(tab.key),
            child: Container(
              padding: const EdgeInsets.symmetric(vertical: 13),
              decoration: BoxDecoration(
                border: Border(
                  bottom: BorderSide(
                    color: page == tab.key ? mobileOrange : Colors.transparent,
                    width: 3,
                  ),
                ),
              ),
              child: Text(
                tab.value,
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: Theme.of(context).colorScheme.primary,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ),
        ),
    ],
  );
}

class MobileDashboard extends StatelessWidget {
  final Map<String, dynamic>? summary;
  final List<dynamic> meals;
  final ValueChanged<int> onOpen;
  final VoidCallback onAdd;
  const MobileDashboard({
    super.key,
    required this.summary,
    required this.meals,
    required this.onOpen,
    required this.onAdd,
  });
  @override
  Widget build(BuildContext context) {
    final nutrients = (summary?['nutrients'] as List?) ?? [];
    final today =
        summary?['as_of_date'] ??
        DateTime.now().toIso8601String().substring(0, 10);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        section('Daily Summary', onTap: () => onOpen(6)),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(18),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(
                  '$today · CONSUMED INTAKE',
                  style: Theme.of(context).textTheme.labelMedium,
                ),
                const SizedBox(height: 16),
                if (summary == null) ...[
                  const Text(
                    'Your nutrition starts here',
                    style: TextStyle(fontSize: 23, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Set up your profile and consent to see your daily nutrient summary.',
                  ),
                  TextButton(
                    onPressed: () => onOpen(3),
                    child: const Text('SET UP PROFILE'),
                  ),
                ] else ...[
                  for (final code in [
                    'energy',
                    'protein',
                    'carbohydrate',
                    'fat',
                  ])
                    nutrientRow(context, nutrients, code),
                  TextButton(
                    onPressed: () => onOpen(6),
                    child: const Text('VIEW FULL REPORT'),
                  ),
                ],
              ],
            ),
          ),
        ),
        const SizedBox(height: 12),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(18),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Row(
                  children: [
                    Icon(Icons.menu_book_outlined, color: mobileTeal),
                    SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        'Your food diary',
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 14),
                Text(
                  '${meals.where((m) => m['local_date'] == today).length} meals logged today',
                  style: const TextStyle(fontSize: 18),
                ),
                const SizedBox(height: 6),
                const Text(
                  'Every entry helps build a clearer picture of your nutrition.',
                ),
                const SizedBox(height: 14),
                FilledButton.icon(
                  onPressed: onAdd,
                  icon: const Icon(Icons.add),
                  label: const Text('Log food'),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 12),
        section('Nutrient Targets', onTap: () => onOpen(7)),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(18),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(
                  summary?['target_provisional'] == true
                      ? 'DEMO TARGETS · Synthetic reference values, not ICMR-NIN recommendations.'
                      : 'Targets and values come from your NutriTwin server.',
                ),
                const SizedBox(height: 16),
                if (nutrients.isEmpty) const Text('No nutrient data yet.'),
                for (final n in nutrients.take(8)) ...[
                  Text(
                    '${n['nutrient_code'].toString().replaceAll('_', ' ')} · ${n['consumed']?['daily']?['coverage_percent'] ?? 'Unknown'}%',
                    style: const TextStyle(fontWeight: FontWeight.w600),
                  ),
                  const SizedBox(height: 6),
                  if (double.tryParse(
                        '${n['consumed']?['daily']?['coverage_percent']}',
                      )
                      case final double percent)
                    LinearProgressIndicator(
                      value: (percent / 100).clamp(0, 1),
                      minHeight: 7,
                      color: mobileTeal,
                      backgroundColor: const Color(0xFFE8EBEA),
                      semanticsLabel: '${n['nutrient_code']} target coverage',
                      semanticsValue: '$percent percent',
                    )
                  else
                    const Text('Coverage unavailable'),
                  const SizedBox(height: 16),
                ],
              ],
            ),
          ),
        ),
        const SizedBox(height: 12),
        const Text(
          'Academic prototype. Missing nutrients remain unknown. Intake estimates are not diagnoses or measured absorption.',
          style: TextStyle(fontSize: 12),
        ),
      ],
    );
  }

  Widget section(String title, {required VoidCallback onTap}) => Row(
    children: [
      Expanded(
        child: Text(
          title,
          style: const TextStyle(fontSize: 21, fontWeight: FontWeight.w700),
        ),
      ),
      IconButton(
        onPressed: onTap,
        tooltip: 'Open $title',
        icon: const Icon(Icons.chevron_right),
      ),
    ],
  );
  Widget nutrientRow(
    BuildContext context,
    List<dynamic> nutrients,
    String code,
  ) {
    final aliases = switch (code) {
      'energy' => ['energy', 'energy_kcal'],
      'carbohydrate' => ['carbohydrate', 'carbohydrates', 'carbohydrate_g'],
      _ => [code, '${code}_g', 'total_$code'],
    };
    final n = nutrients
        .where((n) => aliases.contains(n['nutrient_code']))
        .firstOrNull;
    final value = n?['consumed']?['daily']?['total_amount'];
    final colors = {
      'energy': mobileOrange,
      'protein': const Color(0xFF66C88C),
      'carbohydrate': const Color(0xFF42BCC8),
      'fat': const Color(0xFFB477C6),
    };
    final label = {
      'energy': 'Energy',
      'protein': 'Protein',
      'carbohydrate': 'Carbs',
      'fat': 'Fat',
    }[code]!;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 9),
      child: Row(
        children: [
          Icon(Icons.circle, size: 11, color: colors[code]),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              label,
              style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w600),
            ),
          ),
          Flexible(
            child: Text(
              value == null ? 'Unavailable' : '$value ${n['unit']}',
              textAlign: TextAlign.right,
              style: const TextStyle(fontSize: 16),
            ),
          ),
        ],
      ),
    );
  }
}

class MobileDiary extends StatelessWidget {
  final List<dynamic> meals;
  final String selectedDay;
  final ValueChanged<String> onDate;
  final ValueChanged<dynamic> onEdit;
  final VoidCallback onAdd, onManage;
  const MobileDiary({
    super.key,
    required this.meals,
    required this.selectedDay,
    required this.onDate,
    required this.onEdit,
    required this.onAdd,
    required this.onManage,
  });
  @override
  Widget build(BuildContext context) {
    final date = DateTime.parse(selectedDay);
    final today = DateTime.now();
    String day(DateTime d) => d.toIso8601String().substring(0, 10);
    final entries = meals.where((m) => m['local_date'] == selectedDay).toList();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          children: [
            IconButton(
              tooltip: 'Previous day',
              onPressed: () =>
                  onDate(day(date.subtract(const Duration(days: 1)))),
              icon: const Icon(Icons.chevron_left),
            ),
            Expanded(
              child: TextButton.icon(
                onPressed: () async {
                  final picked = await showDatePicker(
                    context: context,
                    initialDate: date,
                    firstDate: DateTime(1900),
                    lastDate: today,
                  );
                  if (picked != null) onDate(day(picked));
                },
                icon: const Icon(Icons.calendar_today, size: 16),
                label: Text(selectedDay == day(today) ? 'Today' : selectedDay),
              ),
            ),
            IconButton(
              tooltip: 'Next day',
              onPressed: selectedDay.compareTo(day(today)) >= 0
                  ? null
                  : () => onDate(day(date.add(const Duration(days: 1)))),
              icon: const Icon(Icons.chevron_right),
            ),
          ],
        ),
        const SizedBox(height: 12),
        Text('${entries.length} saved meals', textAlign: TextAlign.center),
        const SizedBox(height: 20),
        for (final group in ['Breakfast', 'Lunch', 'Dinner', 'Snacks']) ...[
          Container(
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.surface,
              border: Border(
                bottom: BorderSide(color: Theme.of(context).dividerColor),
              ),
            ),
            child: ListTile(
              dense: true,
              title: Text(
                group,
                style: const TextStyle(
                  fontWeight: FontWeight.w700,
                  fontSize: 16,
                ),
              ),
              trailing: IconButton(
                tooltip: 'Add food to diary',
                onPressed: onAdd,
                icon: const Icon(Icons.add, color: mobileTeal),
              ),
            ),
          ),
          for (final m in entries.where((m) => mealGroup(m) == group))
            ListTile(
              onTap: () => onEdit(m),
              title: Text(m['name']),
              subtitle: Text(
                '${(m['ingredients'] as List).length} ingredients',
              ),
              trailing: const Icon(Icons.chevron_right),
            ),
          if (!entries.any((m) => mealGroup(m) == group))
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 18, horizontal: 16),
              child: Text('No entries', style: TextStyle(color: Colors.grey)),
            ),
        ],
        const SizedBox(height: 16),
        OutlinedButton.icon(
          onPressed: onManage,
          icon: const Icon(Icons.edit_note),
          label: const Text('Manage diary / build a meal'),
        ),
        const SizedBox(height: 10),
        const Text(
          'Meal groups use entry names, then local meal time. Tap an entry to edit.',
          style: TextStyle(fontSize: 12),
        ),
      ],
    );
  }

  static String mealGroup(dynamic meal) {
    final name = '${meal['name']}'.toLowerCase();
    for (final group in ['Breakfast', 'Lunch', 'Dinner', 'Snacks']) {
      if (name.contains(group.toLowerCase().replaceAll('snacks', 'snack'))) {
        return group;
      }
    }
    final hour = DateTime.tryParse('${meal['eaten_at']}')?.toLocal().hour;
    if (hour == null) return 'Snacks';
    return hour < 11
        ? 'Breakfast'
        : hour < 16
        ? 'Lunch'
        : hour < 22
        ? 'Dinner'
        : 'Snacks';
  }
}

class MobileMore extends StatelessWidget {
  final String email;
  final bool admin;
  final ValueChanged<int> onOpen;
  final VoidCallback onPalette, onLogout;
  const MobileMore({
    super.key,
    required this.email,
    required this.admin,
    required this.onOpen,
    required this.onPalette,
    required this.onLogout,
  });
  @override
  Widget build(BuildContext context) => Column(
    children: [
      ListTile(
        leading: const CircleAvatar(child: Icon(Icons.person_outline)),
        title: const Text('Your account'),
        subtitle: Text(email),
      ),
      const SizedBox(height: 16),
      Card(
        child: Column(
          children: [
            ListTile(
              leading: const Icon(Icons.person_outline),
              title: const Text('Profile & consent'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => onOpen(3),
            ),
            ListTile(
              leading: const Icon(Icons.restaurant_menu),
              title: const Text('Meal planning'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => onOpen(2),
            ),
            ListTile(
              leading: const Icon(Icons.palette_outlined),
              title: const Text('Display & color palette'),
              trailing: const Icon(Icons.chevron_right),
              onTap: onPalette,
            ),
            if (admin)
              ListTile(
                leading: const Icon(Icons.fact_check_outlined),
                title: const Text('Evidence review'),
                trailing: const Icon(Icons.chevron_right),
                onTap: () => onOpen(4),
              ),
          ],
        ),
      ),
      const SizedBox(height: 20),
      TextButton.icon(
        onPressed: onLogout,
        icon: const Icon(Icons.logout),
        label: const Text('Sign out'),
      ),
    ],
  );
}

class ServerDialog extends StatefulWidget {
  final String initial;
  const ServerDialog({super.key, required this.initial});
  @override
  State<ServerDialog> createState() => _ServerDialogState();
}

class _ServerDialogState extends State<ServerDialog> {
  late final controller = TextEditingController(text: widget.initial);
  String? error;
  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: const Text('Server connection'),
    content: SingleChildScrollView(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Text(
            'Enter your NutriTwin server address. For a phone, use your computer’s Wi-Fi IP and API port. Use HTTPS for a hosted server. This setting lasts until the app closes.',
          ),
          const SizedBox(height: 16),
          TextField(
            controller: controller,
            keyboardType: TextInputType.url,
            autocorrect: false,
            decoration: InputDecoration(
              labelText: 'Server URL',
              hintText: 'http://192.168.1.10:8000',
              errorText: error,
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
      FilledButton(
        onPressed: () {
          final value = controller.text.trim().replaceFirst(RegExp(r'/+$'), '');
          final uri = Uri.tryParse(value);
          if (uri == null ||
              !['http', 'https'].contains(uri.scheme) ||
              uri.host.isEmpty ||
              uri.userInfo.isNotEmpty ||
              uri.hasQuery ||
              uri.hasFragment ||
              (uri.path.isNotEmpty && uri.path != '/')) {
            setState(
              () => error =
                  'Use an http(s) origin without a path or credentials.',
            );
            return;
          }
          Navigator.pop(context, value);
        },
        child: const Text('Save'),
      ),
    ],
  );
}
