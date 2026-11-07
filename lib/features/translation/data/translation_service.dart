// Diagnosztikai napló.
import 'package:educational_chatbot/core/utils/diagnostic_log.dart';
// Mojibake javítás a fordított szövegen.
import 'package:educational_chatbot/core/utils/text_encoding_fix.dart';
// Online Google Translate HTTP kliens.
import 'package:translator/translator.dart';

/// Online-only Hu↔En fordítás (a telefonon, nem a szerveren).
class TranslationService {
  // Üres konstruktor.
  TranslationService();

  // A translator csomag Google Translate wrapperje.
  final GoogleTranslator _gt = GoogleTranslator();
  // true, ha az ensureReadyOnlineOnly lefutott.
  bool _ready = false;

  // Külső ellenőrzés: kész-e a fordító.
  bool get isReady => _ready;

  /// Cloud kliens: azonnal kész, nincs ML Kit pack várakozás.
  Future<void> ensureReadyOnlineOnly({
    // Nincs visszatérési érték.
    void Function(String status)? onStatus,
  // Blokk / szerkezet zárójele.
  }) async {
    // Splash státusz frissítés.
    onStatus?.call('Fordító (online)…');
    // Jelöljük késznek.
    _ready = true;
    // Napló.
    DiagnosticLog.log('Translate', 'Online translation ready');
  // Blokk / osztály vége.
  }

  /// Splash „kihagyás” gomb kompatibilitás – online módban üres.
  void skipStartupOfflineDownload() {}

  /// Magyar kérdés → angol (szerver / RAG angol embeddinghez).
  Future<String> toEnglish(String text) async {
    // Szóközök levágása.
    final t = text.trim();
    // Üres szöveg: nincs fordítás.
    if (t.isEmpty) return t;

    // Gyors sablonok gyakori iskolai kérdésekre (net nélkül is jó EN).
    final templated = _tryShortNameQuestionTemplate(t);
    // Feltételes elágazás.
    if (templated != null) {
      // Utasítás vége.
      DiagnosticLog.log('Translate', 'Hu→En template "$t" → "$templated"');
      // Visszatérési érték a hívónak.
      return templated;
    // Blokk / osztály vége.
    }

    // Hibakezelés kezdete (try).
    try {
      // Online fordítás, max 10 mp.
      final raw = await _gt
          // Kódsor: részlet a fenti logikából.
          .translate(t, from: 'hu', to: 'en')
          // Utasítás vége.
          .timeout(const Duration(seconds: 10));
      // Eredmény szöveg.
      var out = raw.text.trim();
      // Ha a fordító „lenyelte” a tulajdonneveket, visszatesszük.
      out = _reinjectMissingPersonNames(t, out);
      // Üres eredmény esetén az eredeti HU.
      if (out.isEmpty) out = t;
      // Utasítás vége.
      DiagnosticLog.log('Translate', 'Hu→En "$t" → "$out"');
      // Visszatérési érték a hívónak.
      return out;
    // Blokk / szerkezet zárójele.
    } catch (e, st) {
      // Hálózati / API hiba: fallback az eredeti szövegre.
      DiagnosticLog.log('Translate', 'Hu→En FAILED: $e\n$st');
      // Visszatérési érték a hívónak.
      return t;
    // Blokk / osztály vége.
    }
  // Blokk / osztály vége.
  }

  /// Angol szerver-válasz → magyar UI szöveg.
  Future<String> toHungarian(String text) async {
    // Változó / mező: egyszer állítható érték.
    final t = text.trim();
    // Feltételes elágazás.
    if (t.isEmpty) return t;
    // Hibakezelés kezdete (try).
    try {
      // Változó / mező: egyszer állítható érték.
      final out = await _gt
          // Kódsor: részlet a fenti logikából.
          .translate(t, from: 'en', to: 'hu')
          // Utasítás vége.
          .timeout(const Duration(seconds: 10));
      // Mojibake javítás a magyar eredményen.
      final result = fixUtf8Mojibake(out.text.trim());
      // Utasítás vége.
      DiagnosticLog.log('Translate', 'En→Hu → "$result"');
      // Ha üres a fordítás, legalább az angolt tisztítva adjuk.
      return result.isEmpty ? fixUtf8Mojibake(t) : result;
    // Blokk / szerkezet zárójele.
    } catch (e, st) {
      // Utasítás vége.
      DiagnosticLog.log('Translate', 'En→Hu FAILED: $e\n$st');
      // Visszatérési érték a hívónak.
      return fixUtf8Mojibake(t);
    // Blokk / osztály vége.
    }
  // Blokk / osztály vége.
  }

  /// Erőforrás elengedés.
  Future<void> dispose() async {
    // Értékadás / mezőkitöltés.
    _ready = false;
  // Blokk / osztály vége.
  }

  /// „Ki volt X?” típusú kérdések offline sablonja.
  String? _tryShortNameQuestionTemplate(String hu) {
    // Illesztés: Ki volt … ?
    final m = RegExp(r'^Ki volt\s+(.+?)\s*\??$', caseSensitive: false)
        // Utasítás vége.
        .firstMatch(hu.trim());
    // Feltételes elágazás.
    if (m == null) return null;
    // Változó / mező: egyszer állítható érték.
    final name = m.group(1)!.trim();
    // Athéné / bölcsesség istennője.
    if (RegExp(r'bölcsesség\s+istenn', caseSensitive: false).hasMatch(name)) {
      // Visszatérési érték a hívónak.
      return 'Who was the goddess of wisdom? Athena Athene';
    // Blokk / osztály vége.
    }
    // Szent István.
    if (RegExp(r'szent\s+istv', caseSensitive: false).hasMatch(name)) {
      // Visszatérési érték a hívónak.
      return 'Who was Saint Stephen?';
    // Blokk / osztály vége.
    }
    // Rövid név: Who was <név>?
    if (name.split(RegExp(r'\s+')).length <= 3) {
      // Visszatérési érték a hívónak.
      return 'Who was $name?';
    // Blokk / osztály vége.
    }
    // Nem sablonozható.
    return null;
  // Blokk / osztály vége.
  }

  /// Ha az EN fordításból hiányzik a HU tulajdonnév, zárójelben pótoljuk.
  String _reinjectMissingPersonNames(String hu, String en) {
    // Nagybetűvel kezdődő szavak a magyar kérdésből.
    final names = RegExp(r'\b([A-ZÁÉÍÓÖŐÚÜŰ][\wÁÉÍÓÖŐÚÜŰáéíóöőúüű]+)\b')
        // Kódsor: részlet a fenti logikából.
        .allMatches(hu)
        // Értékadás / mezőkitöltés.
        .map((m) => m.group(1)!)
        // Értékadás / mezőkitöltés.
        .where((n) => n.length >= 3)
        // Utasítás vége.
        .toList();
    // Lokális változó.
    var out = en;
    // Ciklus a listán / tartományon.
    for (final n in names) {
      // Ha az angolban nincs benne (kis/nagybetű függetlenül).
      if (!out.toLowerCase().contains(n.toLowerCase())) {
        // Értékadás / mezőkitöltés.
        out = '$out ($n)';
      // Blokk / osztály vége.
      }
    // Blokk / osztály vége.
    }
    // Visszatérési érték a hívónak.
    return out;
  // Blokk / osztály vége.
  }
// Blokk / osztály vége.
}
