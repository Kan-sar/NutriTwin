import 'dart:js_interop';

@JS('window.localStorage.getItem')
external JSString? _getItem(JSString key);
@JS('window.localStorage.setItem')
external void _setItem(JSString key, JSString value);

String? readPalette() {
  try {
    return _getItem('nutritwin.palette'.toJS)?.toDart;
  } catch (_) {
    return null;
  }
}

bool writePalette(String id) {
  try {
    _setItem('nutritwin.palette'.toJS, id.toJS);
    return true;
  } catch (_) {
    return false;
  }
}
