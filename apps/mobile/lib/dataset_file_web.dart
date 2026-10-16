import 'dart:async';
import 'dart:js_interop';

@JS('document.createElement')
external _Input _createElement(JSString tag);

extension type _Input(JSObject _) implements JSObject {
  external set type(String value);
  external set accept(String value);
  external _Files? get files;
  external void addEventListener(String name, JSFunction callback);
  external void click();
}

extension type _Files(JSObject _) implements JSObject {
  external int get length;
  external _File? item(int index);
}

extension type _File(JSObject _) implements JSObject {
  external int get size;
  external JSPromise<JSString> text();
}

Future<String?> pickDatasetFile() {
  final result = Completer<String?>();
  final input = _createElement('input'.toJS);
  input.type = 'file';
  input.accept = '.json,application/json';
  input.addEventListener(
    'cancel',
    ((JSAny? event) {
      if (!result.isCompleted) result.complete(null);
    }).toJS,
  );
  input.addEventListener(
    'change',
    ((JSAny? event) {
      final file = input.files?.item(0);
      if (file == null) {
        result.complete(null);
        return;
      }
      if (file.size > 2000000) {
        result.completeError(
          const FormatException('Choose a JSON file smaller than 2 MB.'),
        );
        return;
      }
      file.text().toDart.then(
        (value) => result.complete(value.toDart),
        onError: (Object error) => result.completeError(error),
      );
    }).toJS,
  );
  input.click();
  return result.future;
}
