import 'package:flutter/material.dart';

import 'api.dart';
import 'dataset_file_stub.dart'
    if (dart.library.js_interop) 'dataset_file_web.dart'
    as files;

class DatasetImportDialog extends StatefulWidget {
  final NutriApi api;
  const DatasetImportDialog({super.key, required this.api});
  @override
  State<DatasetImportDialog> createState() => _DatasetImportDialogState();
}

class _DatasetImportDialogState extends State<DatasetImportDialog> {
  final document = TextEditingController();
  Map<String, dynamic>? preview;
  String? error;
  bool busy = false, complete = false;
  @override
  void dispose() {
    document.dispose();
    super.dispose();
  }

  Future<void> perform(Future<void> Function() action) async {
    setState(() {
      busy = true;
      error = null;
    });
    try {
      await action();
    } on ApiError catch (e) {
      if (mounted) setState(() => error = e.message);
    } on FormatException catch (e) {
      if (mounted) setState(() => error = e.message);
    } catch (_) {
      if (mounted) {
        setState(
          () => error = 'Could not import the dataset. Try previewing again.',
        );
      }
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: const Text('Import food or recipe dataset'),
    content: SizedBox(
      width: 620,
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Choose a NutriTwin foods JSON file (up to 2 MB / 500 foods). Preview validates it before anything is saved. Imported foods are non-authoritative; targets and scientific rules are not imported.',
            ),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: busy
                  ? null
                  : () => perform(() async {
                      final text = await files.pickDatasetFile();
                      if (text != null && mounted) {
                        setState(() {
                          document.text = text;
                          preview = null;
                          complete = false;
                        });
                      }
                    }),
              icon: const Icon(Icons.upload_file),
              label: const Text('Choose JSON file'),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: document,
              enabled: !busy,
              minLines: 4,
              maxLines: 8,
              decoration: const InputDecoration(
                labelText: 'Dataset JSON',
                helperText: 'You can also paste the JSON here.',
              ),
              onChanged: (_) => setState(() {
                preview = null;
                complete = false;
              }),
            ),
            ExpansionTile(
              title: const Text('Required format'),
              children: [
                const Padding(
                  padding: EdgeInsets.all(12),
                  child: SelectableText(
                    'schema_version: nutritwin-foods-v1\nsource: code (IMPORT- prefix), title, organization, url, license, version, effective_from (YYYY-MM-DD), redistribution_confirmed (true only with permission)\nfoods: food_code, name, dietary_tags, allergens, nutrients\neach nutrient: nutrient_code, unit, amount_per_100g (number or null)\nUse canonical units: energy kcal; protein/carbohydrate/fat/fiber g; iron/calcium/magnesium/potassium/sodium/zinc/vitamin_c mg.\nQuantities are per 100 g edible food. Preserve the raw/cooked state in the name. Missing nutrients stay unknown.',
                  ),
                ),
              ],
            ),
            if (error != null)
              Semantics(
                liveRegion: true,
                child: Text(
                  error!,
                  style: TextStyle(color: Theme.of(context).colorScheme.error),
                ),
              ),
            if (preview != null) ...[
              const SizedBox(height: 12),
              Text(
                complete ? 'Import complete' : 'Preview — nothing saved yet',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              Text(
                '${preview!['source']}\n${preview!['foods']} ${preview!['kind'] ?? 'foods'} · ${preview!['new_foods']} new · ${preview!['missing_values']} explicit missing values',
              ),
              Text((preview!['sample_names'] as List).join('\n')),
            ],
            if (busy) const LinearProgressIndicator(),
          ],
        ),
      ),
    ),
    actions: [
      TextButton(
        onPressed: busy ? null : () => Navigator.pop(context, complete),
        child: Text(complete ? 'Done' : 'Cancel'),
      ),
      if (!complete)
        OutlinedButton(
          onPressed: busy
              ? null
              : () => perform(() async {
                  if (document.text.trim().isEmpty) {
                    throw const FormatException(
                      'Choose a file or paste a dataset first.',
                    );
                  }
                  preview = null;
                  final value = await widget.api.request(
                    'POST',
                    '/admin/food-datasets/import',
                    body: {'document': document.text},
                  );
                  if (mounted) {
                    setState(() => preview = Map<String, dynamic>.from(value));
                  }
                }),
          child: const Text('Preview dataset'),
        ),
      if (preview != null && !complete)
        FilledButton(
          onPressed: busy
              ? null
              : () => perform(() async {
                  final value = await widget.api.request(
                    'POST',
                    '/admin/food-datasets/import',
                    body: {
                      'document': document.text,
                      'commit': true,
                      'preview_checksum': preview!['checksum'],
                    },
                  );
                  if (mounted) {
                    setState(() {
                      preview = Map<String, dynamic>.from(value);
                      complete = true;
                    });
                  }
                }),
          child: const Text('Import dataset'),
        ),
    ],
  );
}
