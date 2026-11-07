// unawaited: fire-and-forget aszinkron írás.
import 'dart:async';
// File osztály a napló fájlhoz.
import 'dart:io';

// debugPrint + PlatformDispatcher hibakezelés.
import 'package:flutter/foundation.dart';
// App documents könyvtár elérési útja.
import 'package:path_provider/path_provider.dart';

/// Gyűrűpufferes diagnosztikai napló (USB nélkül is menthető).
class DiagnosticLog {
  // Csak static használat.
  DiagnosticLog._();

  // Maximum ennyi sort tartunk memóriában / fájlban.
  static const _maxLines = 400;
  // Memória-puffer a soroknak.
  static final _buffer = <String>[];
  // A diskre írt naplófájl.
  static File? _file;
  // true, ha az init sikeres volt.
  static bool _ready = false;

  // Fájl megnyitása / meglévő napló betöltése.
  static Future<void> init() async {
    // Dupla init elkerülése.
    if (_ready) return;
    // Hibakezelés kezdete (try).
    try {
      // App privát documents mappa.
      final dir = await getApplicationDocumentsDirectory();
      // fixed fájlnév a naplónak.
      _file = File('${dir.path}/diagnostic.log');
      // Ha van régi napló, beolvassuk.
      if (await _file!.exists()) {
        // Változó / mező: egyszer állítható érték.
        final existing = await _file!.readAsLines();
        // Csak az utolsó _maxLines sort tartjuk.
        _buffer.addAll(
          // Kódsor: részlet a fenti logikából.
          existing.length > _maxLines
              // Kódsor: részlet a fenti logikából.
              ? existing.sublist(existing.length - _maxLines)
              // Widget / hívás paraméterlista folytatása.
              : existing,
        // Utasítás vége.
        );
      // Blokk / osztály vége.
      }
      // Értékadás / mezőkitöltés.
      _ready = true; // Innentől mehet a log().
      // Indítási elválasztó sor.
      await _write('=== App start ${DateTime.now().toIso8601String()} ===');
    // Blokk / szerkezet zárójele.
    } catch (e, st) {
      // Naplóhiba ne döntse el az appot.
      debugPrint('[DiagnosticLog] init failed: $e\n$st');
    // Blokk / osztály vége.
    }
  // Blokk / osztály vége.
  }

  // Külső export / UI számára a fájl útja.
  static String? get filePath => _file?.path;

  // Az utolsó N sor a pufferből.
  static List<String> recentLines({int count = 40}) {
    // Feltételes elágazás.
    if (_buffer.isEmpty) return const []; // Üres lista konstans.
    // Változó / mező: egyszer állítható érték.
    final n = count.clamp(1, _buffer.length); // Érvényes tartomány.
    // Visszatérési érték a hívónak.
    return _buffer.sublist(_buffer.length - n); // Utolsó n elem.
  // Blokk / osztály vége.
  }

  // Egy naplóbejegyzés írása + konzolra nyomtatás.
  static void log(String tag, String message) {
    // Időbélyeg + címke + üzenet.
    final line =
        // Utasítás vége.
        '${DateTime.now().toIso8601String()} [$tag] $message';
    // Fejlesztői konzol kiírás.
    debugPrint(line); // Fejlesztői konzol.
    // Fut a háttérben, nem várjuk meg.
    unawaited(_write(line)); // Disk írás háttérben.
  // Blokk / osztály vége.
  }

  // Puffer frissítés + fájlba mentés.
  static Future<void> _write(String line) async {
    // Kódsor: részlet a fenti logikából.
    _buffer.add(line); // Új sor a végére.
    // Ha túl hosszú, levágjuk az elejét.
    if (_buffer.length > _maxLines) {
      // Utasítás vége.
      _buffer.removeRange(0, _buffer.length - _maxLines);
    // Blokk / osztály vége.
    }
    // Változó / mező: egyszer állítható érték.
    final file = _file; // Lokális másolat null-checkhez.
    // Feltételes elágazás.
    if (file == null) return; // Init előtt nincs fájl.
    // Hibakezelés kezdete (try).
    try {
      // Teljes puffer újraírása (egyszerű, kis méret).
      await file.writeAsString('${_buffer.join('\n')}\n');
    // Blokk / szerkezet zárójele.
    } catch (e) {
      // Fejlesztői konzol kiírás.
      debugPrint('[DiagnosticLog] write failed: $e');
    // Blokk / osztály vége.
    }
  // Blokk / osztály vége.
  }

  // Globális Flutter / platform hibák átirányítása a naplóba.
  static void installGlobalHandlers() {
    // Előző handler megőrzése (lánc).
    final prevFlutter = FlutterError.onError;
    // Új Flutter framework hibakezelő.
    FlutterError.onError = (details) {
      // Widget / hívás paraméterlista folytatása.
      log(
        // Widget / hívás paraméterlista folytatása.
        'FlutterError',
        // Widget / hívás paraméterlista folytatása.
        '${details.exceptionAsString()}\n${details.stack}',
      // Utasítás vége.
      );
      // Kódsor: részlet a fenti logikából.
      prevFlutter?.call(details); // Továbbadás, ha volt.
    // Blokk / szerkezet zárójele.
    };

    // Nem-Flutter (Dart) zone hibák.
    PlatformDispatcher.instance.onError = (error, stack) {
      // Utasítás vége.
      log('PlatformError', '$error\n$stack');
      // Visszatérési érték a hívónak.
      return false; // false = ne nyeljük el teljesen.
    // Blokk / szerkezet zárójele.
    };
  // Blokk / osztály vége.
  }
// Blokk / osztály vége.
}
