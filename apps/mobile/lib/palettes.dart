import 'package:flutter/material.dart';

// Color reference facts only; see THIRD_PARTY_NOTICES.md for pinned provenance.
class AppPalette {
  final String id, name;
  final Color background, surface, accent, text;
  const AppPalette(
    this.id,
    this.name,
    this.background,
    this.surface,
    this.accent,
    this.text,
  );
  bool get dark => background.computeLuminance() < .3;
  Color get onAccent =>
      accent.computeLuminance() > .179 ? Colors.black : Colors.white;
  String get description => switch (id) {
    'mobile' => 'Cream / orange / teal',
    'nutritwin' => 'Warm paper / forest green',
    'serika_dark' => 'Charcoal / golden yellow',
    'serika' => 'Cool paper / mustard yellow',
    'nord' => 'Arctic blue / frosted cyan',
    'dracula' => 'Midnight purple / violet',
    _ => 'Muted plum / rose and seafoam',
  };
  double get radius => switch (id) {
    'serika_dark' || 'serika' => 6,
    'nord' => 10,
    'dracula' => 14,
    _ => 12,
  };
  // Supporting tones are original UI adaptations of the reference palettes.
  Color get secondary => switch (id) {
    'rose_pine' => const Color(0xFFEBBCBA),
    'dracula' => const Color(0xFFFF79C6),
    'nord' => const Color(0xFFA3BE8C),
    _ => accent,
  };
  Color get navigation => dark
      ? Color.lerp(surface, secondary, .10)!
      : id == 'serika'
      ? const Color(0xFF323437)
      : accent;
  Color get onNavigation =>
      dark || id == 'serika' ? const Color(0xFFF8F8F2) : onAccent;
  Color get container => Color.lerp(surface, secondary, dark ? .16 : .09)!;
  Color get border => Color.lerp(surface, text, .30)!;
  ThemeData get theme {
    final scheme =
        ColorScheme.fromSeed(
          seedColor: accent,
          brightness: dark ? Brightness.dark : Brightness.light,
        ).copyWith(
          primary: accent,
          onPrimary: onAccent,
          primaryContainer: container,
          onPrimaryContainer: text,
          secondary: secondary,
          onSecondary: secondary.computeLuminance() > .179
              ? Colors.black
              : Colors.white,
          secondaryContainer: container,
          onSecondaryContainer: text,
          tertiary: secondary,
          tertiaryContainer: container,
          onTertiaryContainer: text,
          surface: surface,
          onSurface: text,
          onSurfaceVariant: text.withValues(alpha: .8),
          surfaceContainerLowest: background,
          surfaceContainerLow: surface,
          surfaceContainer: container,
          surfaceContainerHigh: container,
          surfaceContainerHighest: Color.lerp(surface, secondary, .22),
          surfaceTint: Colors.transparent,
          outline: border,
          outlineVariant: border.withValues(alpha: .55),
        );
    final shape = RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(radius),
    );
    return ThemeData(
      useMaterial3: true,
      visualDensity: VisualDensity.standard,
      textTheme:
          ThemeData(brightness: dark ? Brightness.dark : Brightness.light)
              .textTheme
              .copyWith(
                headlineMedium: TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.w700,
                  letterSpacing: -.7,
                  color: text,
                ),
                headlineSmall: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.w700,
                  letterSpacing: -.5,
                  color: text,
                ),
                titleLarge: TextStyle(
                  fontSize: 19,
                  fontWeight: FontWeight.w600,
                  color: text,
                ),
                titleMedium: TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.w600,
                  color: text,
                ),
                bodyMedium: TextStyle(fontSize: 14, height: 1.45, color: text),
                labelLarge: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: text,
                ),
              ),
      tooltipTheme: TooltipThemeData(
        waitDuration: const Duration(milliseconds: 180),
        padding: const EdgeInsets.all(14),
        textStyle: TextStyle(fontSize: 12, height: 1.6, color: background),
        decoration: BoxDecoration(
          color: text,
          borderRadius: BorderRadius.circular(8),
        ),
      ),
      dataTableTheme: DataTableThemeData(
        headingRowColor: WidgetStatePropertyAll(container),
        headingTextStyle: TextStyle(fontWeight: FontWeight.w600, color: text),
        dividerThickness: .5,
      ),
      scaffoldBackgroundColor: background,
      colorScheme: scheme,
      appBarTheme: AppBarTheme(
        backgroundColor: id == 'mobile' ? surface : navigation,
        foregroundColor: id == 'mobile' ? text : onNavigation,
      ),
      inputDecorationTheme: InputDecorationTheme(
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 14,
          vertical: 16,
        ),
        filled: true,
        fillColor: Color.lerp(background, surface, .5),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(radius),
          borderSide: BorderSide(color: border),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(radius),
          borderSide: BorderSide(color: border),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(radius),
          borderSide: BorderSide(color: dark ? accent : text, width: 2),
        ),
      ),
      cardTheme: CardThemeData(
        color: surface,
        elevation: 0,
        shape: shape.copyWith(
          side: BorderSide(color: border.withValues(alpha: .55)),
        ),
      ),
      dialogTheme: DialogThemeData(backgroundColor: surface, shape: shape),
      popupMenuTheme: PopupMenuThemeData(color: surface, shape: shape),
      chipTheme: ChipThemeData(
        backgroundColor: surface,
        selectedColor: container,
        side: BorderSide(color: border),
        shape: shape,
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(shape: shape),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(foregroundColor: text, shape: shape),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: text,
          side: BorderSide(color: border),
          shape: shape,
        ),
      ),
      dividerTheme: DividerThemeData(color: border.withValues(alpha: .55)),
    );
  }
}

const appPalettes = [
  AppPalette(
    'nutritwin',
    'NutriTwin',
    Color(0xFFF7F8F2),
    Color(0xFFFFFFFF),
    Color(0xFF244F3D),
    Color(0xFF203E34),
  ),
  AppPalette(
    'serika_dark',
    'Serika Dark',
    Color(0xFF323437),
    Color(0xFF2C2E31),
    Color(0xFFE2B714),
    Color(0xFFD1D0C5),
  ),
  AppPalette(
    'serika',
    'Serika',
    Color(0xFFE1E1E3),
    Color(0xFFD1D3D8),
    Color(0xFFE2B714),
    Color(0xFF323437),
  ),
  AppPalette(
    'nord',
    'Nord',
    Color(0xFF242933),
    Color(0xFF2E3440),
    Color(0xFF88C0D0),
    Color(0xFFD8DEE9),
  ),
  AppPalette(
    'dracula',
    'Dracula',
    Color(0xFF282A36),
    Color(0xFF20222C),
    Color(0xFFBD93F9),
    Color(0xFFF8F8F2),
  ),
  AppPalette(
    'rose_pine',
    'Rosé Pine',
    Color(0xFF1F1D27),
    Color(0xFF282533),
    Color(0xFF9CCFD8),
    Color(0xFFE0DEF4),
  ),
  AppPalette(
    'mobile',
    'Mobile',
    Color(0xFFFFFCF6),
    Color(0xFFFFFFFF),
    Color(0xFFC94B17),
    Color(0xFF252735),
  ),
];

AppPalette paletteById(String? id) =>
    appPalettes.where((p) => p.id == id).firstOrNull ?? appPalettes.first;

Future<String?> choosePalette(BuildContext context, String current) =>
    showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Choose a color palette'),
        content: SizedBox(
          width: 430,
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'NutriTwin plus five palettes from Monkeytype. Your choice is saved in this browser when storage is available.',
                ),
                const SizedBox(height: 16),
                for (final palette in appPalettes)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: Semantics(
                      selected: current == palette.id,
                      child: Material(
                        color: palette.background,
                        borderRadius: BorderRadius.circular(12),
                        child: ListTile(
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                          title: Text(
                            palette.name,
                            style: TextStyle(color: palette.text),
                          ),
                          subtitle: Text(
                            palette.description,
                            style: TextStyle(color: palette.text),
                          ),
                          leading: CircleAvatar(
                            backgroundColor: palette.accent,
                            child: Icon(
                              Icons.palette_outlined,
                              color: palette.onAccent,
                            ),
                          ),
                          trailing: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              for (final color in [
                                palette.accent,
                                palette.secondary,
                                palette.surface,
                              ])
                                Container(
                                  width: 12,
                                  height: 28,
                                  margin: const EdgeInsets.only(left: 3),
                                  color: color,
                                ),
                              if (current == palette.id)
                                Icon(Icons.check, color: palette.text),
                            ],
                          ),
                          onTap: () => Navigator.pop(context, palette.id),
                        ),
                      ),
                    ),
                  ),
              ],
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
        ],
      ),
    );
