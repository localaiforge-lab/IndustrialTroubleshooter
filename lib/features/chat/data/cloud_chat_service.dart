// TimeoutException típus a hálózati időtúllépéshez.
// Import: külső/csomag függőség betöltése.
import 'dart:async';
// JSON encode/decode + utf8.
// Import: külső/csomag függőség betöltése.
import 'dart:convert';
// SocketException a net hibákhoz.
// Import: külső/csomag függőség betöltése.
import 'dart:io';

// Diagnosztikai napló.
// Import: külső/csomag függőség betöltése.
import 'package:educational_chatbot/core/utils/diagnostic_log.dart';
// Mojibake javítás.
// Import: külső/csomag függőség betöltése.
import 'package:educational_chatbot/core/utils/text_encoding_fix.dart';
// ChatService interfész.
// Import: külső/csomag függőség betöltése.
import 'package:educational_chatbot/features/chat/domain/chat_service.dart';
// ChatMessage / RagSourcePreview entitások.
// Import: külső/csomag függőség betöltése.
import 'package:educational_chatbot/features/chat/domain/entities/chat_message.dart';
// Online fordító.
// Import: külső/csomag függőség betöltése.
import 'package:educational_chatbot/features/translation/data/translation_service.dart';
// ChangeNotifier: UI figyelheti a változásokat.
// Import: külső/csomag függőség betöltése.
import 'package:flutter/foundation.dart';
// HTTP kliens a Cloud Run API-hoz.
// Import: külső/csomag függőség betöltése.
import 'package:http/http.dart' as http;
// Üzenet ID-k generálása.
// Import: külső/csomag függőség betöltése.
import 'package:uuid/uuid.dart';

// Megosztott UUID generátor.
// Fordítási idejű konstans.
const _uuid = Uuid();

/// Ha a Cloud Run nem elérhető / nem kész – ezt dobjuk a UI felé.
// Osztály definíció kezdete.
class CloudUnavailableException implements Exception {
  // Magyar, felhasználóbarát üzenet.
  // Utasítás vége.
  CloudUnavailableException(this.message);
  // A megjelenítendő szöveg.
  // Változó / mező: egyszer állítható érték.
  final String message;

  // Felülírja a szülő/interfész metódusát.
  @override
  // toString = maga az üzenet (splash „Hiba: …”hez).
  // Szöveges mező vagy változó.
  String toString() => message;
// Blokk / osztály vége.
}

/// Vékony HTTP kliens: telefon fordít, szerver RAG+web+Qwen.
// Osztály definíció kezdete.
class CloudChatService extends ChangeNotifier implements ChatService {
  // Widget / hívás paraméterlista folytatása.
  CloudChatService({
    // Kódsor: részlet a fenti logikából.
    required this.baseUrl, // Pl. https://….run.app
    // Kódsor: részlet a fenti logikából.
    required TranslationService translation, // Hu↔En a telefonon.
    // Kódsor: részlet a fenti logikából.
    http.Client? client, // Tesztelhetőség: mock client.
  // Blokk / szerkezet zárójele.
  })  : _translation = translation,
        // Értékadás / mezőkitöltés.
        _client = client ?? http.Client(); // Alap HTTP kliens.

  // Cloud Run gyökér URL.
  // Változó / mező: egyszer állítható érték.
  final String baseUrl;
  // Fordító szolgáltatás.
  // Változó / mező: egyszer állítható érték.
  final TranslationService _translation;
  // HTTP kliens példány.
  // Változó / mező: egyszer állítható érték.
  final http.Client _client;

  // Beszélgetés-előzmény memóriában.
  // Változó / mező: egyszer állítható érték.
  final List<ChatMessage> _messages = [];
  // Éppen generálunk-e választ.
  // Igaz/hamis mező vagy változó.
  bool _isGenerating = false;
  // Kör-azonosító: megszakítás / elavult válasz szűrése.
  // Egész szám.
  int _turnEpoch = 0;
  // Kiválasztott tankönyv documentId.
  // Utasítás vége.
  String? _selectedDocumentId;
  // Utolsó RAG context (opcionális debug).
  // Utasítás vége.
  String? lastContextBlock;
  // Utolsó találat-előnézetek.
  // Értékadás / mezőkitöltés.
  List<RagSourcePreview> lastPreviews = const [];

  // Felülírja a szülő/interfész metódusát.
  @override
  // UI csak olvasható másolatot kap.
  // Értékadás / mezőkitöltés.
  List<ChatMessage> get messages => List.unmodifiable(_messages);

  // Felülírja a szülő/interfész metódusát.
  @override
  // Generálás flag a UI lockhoz.
  // Igaz/hamis mező vagy változó.
  bool get isGenerating => _isGenerating;

  // Felülírja a szülő/interfész metódusát.
  @override
  // Aktív könyv ID.
  // Értékadás / mezőkitöltés.
  String? get selectedDocumentId => _selectedDocumentId;

  // Felülírja a szülő/interfész metódusát.
  @override
  // Widget / hívás paraméterlista folytatása.
  set selectedDocumentId(String? value) {
    // Üres string → null.
    // Változó / mező: egyszer állítható érték.
    final next = (value == null || value.isEmpty) ? null : value;
    // Nincs változás → ne notify.
    // Feltételes elágazás.
    if (_selectedDocumentId == next) return;
    // Értékadás / mezőkitöltés.
    _selectedDocumentId = next;
    // Kódsor: részlet a fenti logikából.
    notifyListeners(); // UI frissítés.
  // Blokk / osztály vége.
  }

  /// baseUrl + path → Uri (trailing slash kezeléssel).
  // Widget / hívás paraméterlista folytatása.
  Uri _uri(String path) {
    // Záró / levágása a gyökérről.
    // Változó / mező: egyszer állítható érték.
    final root = baseUrl.endsWith('/')
        // Kódsor: részlet a fenti logikából.
        ? baseUrl.substring(0, baseUrl.length - 1)
        // Utasítás vége.
        : baseUrl;
    // Teljes URL parse.
    // Visszatérési érték a hívónak.
    return Uri.parse('$root$path');
  // Blokk / osztály vége.
  }

  /// Indításkor: /health – net + ok + llmReady.
  // Aszinkron függvény / Future típus.
  Future<void> ping() async {
    // Hibakezelés kezdete (try).
    try {
      // GET /health, max 20 mp.
      // Változó / mező: egyszer állítható érték.
      final res = await _client
          // Kódsor: részlet a fenti logikából.
          .get(_uri('/health'))
          // Utasítás vége.
          .timeout(const Duration(seconds: 20));
      // Nem 200 → szolgáltatás gond.
      // Feltételes elágazás.
      if (res.statusCode != 200) {
        // Kivétel dobása.
        throw CloudUnavailableException(
          // Kódsor: részlet a fenti logikából.
          'A felhő szolgáltatás nem válaszol rendesen (HTTP ${res.statusCode}). '
          // Widget / hívás paraméterlista folytatása.
          'Próbáld újra később.',
        // Utasítás vége.
        );
      // Blokk / osztály vége.
      }
      // JSON body.
      // Változó / mező: egyszer állítható érték.
      final body = jsonDecode(res.body) as Map<String, dynamic>;
      // ok flag kötelező.
      // Feltételes elágazás.
      if (body['ok'] != true) {
        // Kivétel dobása.
        throw CloudUnavailableException(
          // Widget / hívás paraméterlista folytatása.
          'A felhő szolgáltatás jelenleg nem elérhető. Próbáld újra később.',
        // Utasítás vége.
        );
      // Blokk / osztály vége.
      }
      // Qwen GGUF betöltve legyen.
      // Feltételes elágazás.
      if (body['llmReady'] != true) {
        // Kivétel dobása.
        throw CloudUnavailableException(
          // Kódsor: részlet a fenti logikából.
          'A felhő szolgáltatás fut, de a nyelvi modell még nem kész. '
          // Widget / hívás paraméterlista folytatása.
          'Várj egy percet, majd próbáld újra.',
        // Utasítás vége.
        );
      // Blokk / osztály vége.
      }
    // Blokk / szerkezet zárójele.
    } on CloudUnavailableException {
      // Már magyar üzenet – továbbdobás.
      // Utasítás vége.
      rethrow;
    // Blokk / szerkezet zárójele.
    } catch (e) {
      // Egyéb net hibák → barátságos szöveg.
      // Kivétel dobása.
      throw CloudUnavailableException(_friendlyNetworkError(e));
    // Blokk / osztály vége.
    }
  // Blokk / osztály vége.
  }

  /// Tankönyvlista a szerverről (GET /v1/books).
  // Aszinkron függvény / Future típus.
  Future<List<({String documentId, String title})>> fetchBooks() async {
    // Hibakezelés kezdete (try).
    try {
      // Változó / mező: egyszer állítható érték.
      final res = await _client
          // Kódsor: részlet a fenti logikából.
          .get(_uri('/v1/books'))
          // Utasítás vége.
          .timeout(const Duration(seconds: 20));
      // Feltételes elágazás.
      if (res.statusCode != 200) {
        // Kivétel dobása.
        throw CloudUnavailableException(
          // Widget / hívás paraméterlista folytatása.
          'A tananyaglista nem érhető el (HTTP ${res.statusCode}).',
        // Utasítás vége.
        );
      // Blokk / osztály vége.
      }
      // Változó / mező: egyszer állítható érték.
      final body = jsonDecode(res.body) as Map<String, dynamic>;
      // books tömb, vagy üres.
      // Változó / mező: egyszer állítható érték.
      final books = (body['books'] as List<dynamic>? ?? const []);
      // Visszatérési érték a hívónak.
      return [
        // Ciklus a listán / tartományon.
        for (final b in books)
          // Widget / hívás paraméterlista folytatása.
          (
            // Kötelező documentId.
            // Widget / hívás paraméterlista folytatása.
            documentId: (b as Map<String, dynamic>)['documentId'] as String,
            // Cím, fallback az ID-re.
            // Widget / hívás paraméterlista folytatása.
            title: b['title'] as String? ?? b['documentId'] as String,
          // Widget / hívás paraméterlista folytatása.
          ),
      // Utasítás vége.
      ];
    // Blokk / szerkezet zárójele.
    } on CloudUnavailableException {
      // Utasítás vége.
      rethrow;
    // Blokk / szerkezet zárójele.
    } catch (e) {
      // Kivétel dobása.
      throw CloudUnavailableException(_friendlyNetworkError(e));
    // Blokk / osztály vége.
    }
  // Blokk / osztály vége.
  }

  // Felülírja a szülő/interfész metódusát.
  @override
  /// Egy felhasználói kérdés elküldése a felhőnek.
  // Aszinkron függvény / Future típus.
  Future<void> sendMessage(
    // Szöveges mező vagy változó.
    String text, {
    // Igaz/hamis mező vagy változó.
    bool useRag = true, // Kompatibilitás; a szerver mindig RAG-ol.
    // Kódsor: részlet a fenti logikából.
    String? documentId, // Opcionális könyv-felülírás.
  // Blokk / szerkezet zárójele.
  }) async {
    // Változó / mező: egyszer állítható érték.
    final trimmed = text.trim();
    // Üres vagy már futó generálás → kilépés.
    // Feltételes elágazás.
    if (trimmed.isEmpty || _isGenerating) return;

    // Új kör azonosító (régi válaszok eldobásához).
    // Változó / mező: egyszer állítható érték.
    final turn = ++_turnEpoch;
    // Értékadás / mezőkitöltés.
    _isGenerating = true;
    // Kódsor: részlet a fenti logikából.
    notifyListeners(); // UI: gondolatjel / lock.

    // Üzenet ID-k.
    // Változó / mező: egyszer állítható érték.
    final userId = _uuid.v4();
    // Változó / mező: egyszer állítható érték.
    final assistantId = _uuid.v4();
    // Felhasználói buborék.
    // Widget / hívás paraméterlista folytatása.
    _messages.add(
      // Widget / hívás paraméterlista folytatása.
      ChatMessage(
        // Widget / hívás paraméterlista folytatása.
        id: userId,
        // Widget / hívás paraméterlista folytatása.
        role: ChatRole.user,
        // Widget / hívás paraméterlista folytatása.
        content: trimmed,
        // Widget / hívás paraméterlista folytatása.
        createdAt: DateTime.now(),
      // Widget / hívás paraméterlista folytatása.
      ),
    // Utasítás vége.
    );
    // Asszisztens placeholder („…”).
    // Widget / hívás paraméterlista folytatása.
    _messages.add(
      // Widget / hívás paraméterlista folytatása.
      ChatMessage(
        // Widget / hívás paraméterlista folytatása.
        id: assistantId,
        // Widget / hívás paraméterlista folytatása.
        role: ChatRole.assistant,
        // Widget / hívás paraméterlista folytatása.
        content: '…',
        // Widget / hívás paraméterlista folytatása.
        createdAt: DateTime.now(),
        // Widget / hívás paraméterlista folytatása.
        isStreaming: true,
      // Widget / hívás paraméterlista folytatása.
      ),
    // Utasítás vége.
    );
    // Utasítás vége.
    notifyListeners();

    // Hibakezelés kezdete (try).
    try {
      // 1) HU → EN a telefonon.
      // Változó / mező: egyszer állítható érték.
      final englishQuestion = await _translation.toEnglish(trimmed);
      // Megszakították a kört?
      // Feltételes elágazás.
      if (turn != _turnEpoch) return;

      // 2) JSON body a szervernek.
      // Változó / mező: egyszer állítható érték.
      final payload = <String, dynamic>{
        // Kódsor: részlet a fenti logikából.
        'question': englishQuestion, // Angol kérdés (RAG/LLM).
        // Kódsor: részlet a fenti logikából.
        'hungarianQuestion': trimmed, // Lexikai boost.
        // Kódsor: részlet a fenti logikából.
        'documentId': documentId ?? _selectedDocumentId, // Könyv szűrés.
      // Blokk / szerkezet zárójele.
      };
      // POST /v1/chat, hosszú timeout (LLM).
      // Változó / mező: egyszer állítható érték.
      final res = await _client
          // Widget / hívás paraméterlista folytatása.
          .post(
            // Widget / hívás paraméterlista folytatása.
            _uri('/v1/chat'),
            // Widget / hívás paraméterlista folytatása.
            headers: {'Content-Type': 'application/json'},
            // Widget / hívás paraméterlista folytatása.
            body: jsonEncode(payload),
          // Kódsor: részlet a fenti logikából.
          )
          // Utasítás vége.
          .timeout(const Duration(seconds: 180));

      // Feltételes elágazás.
      if (turn != _turnEpoch) return;

      // 503: modell / túlterhelés.
      // Feltételes elágazás.
      if (res.statusCode == 503) {
        // Widget / hívás paraméterlista folytatása.
        _finish(
          // Widget / hívás paraméterlista folytatása.
          assistantId,
          // Kódsor: részlet a fenti logikából.
          'A felhő szolgáltatás átmenetileg nem tud válaszolni '
          // Widget / hívás paraméterlista folytatása.
          '(modell / túlterhelés). Próbáld újra egy kicsit később.',
        // Utasítás vége.
        );
        // Utasítás vége.
        return;
      // Blokk / osztály vége.
      }
      // Egyéb HTTP hiba.
      // Feltételes elágazás.
      if (res.statusCode != 200) {
        // Widget / hívás paraméterlista folytatása.
        _finish(
          // Widget / hívás paraméterlista folytatása.
          assistantId,
          // Kódsor: részlet a fenti logikából.
          'A felhő szolgáltatás hibát jelzett (HTTP ${res.statusCode}). '
          // Widget / hívás paraméterlista folytatása.
          'Próbáld újra később.',
        // Utasítás vége.
        );
        // Utasítás vége.
        return;
      // Blokk / osztály vége.
      }

      // Válasz JSON (UTF-8 bájtokból).
      // Változó / mező: egyszer állítható érték.
      final body =
          // Utasítás vége.
          jsonDecode(utf8.decode(res.bodyBytes)) as Map<String, dynamic>;
      // Angol answer mező.
      // Változó / mező: egyszer állítható érték.
      final englishAnswer =
          // Utasítás vége.
          fixUtf8Mojibake((body['answer'] as String?)?.trim() ?? '');
      // 3) EN → HU a telefonon.
      // Változó / mező: egyszer állítható érték.
      final hungarianAnswer = englishAnswer.isEmpty
          // Kódsor: részlet a fenti logikából.
          ? ''
          // Utasítás vége.
          : fixUtf8Mojibake(await _translation.toHungarian(englishAnswer));

      // Feltételes elágazás.
      if (turn != _turnEpoch) return;

      // Opcionális debug blokk a szervertől.
      // Változó / mező: egyszer állítható érték.
      final debug = body['debug'] as Map<String, dynamic>?;
      // Változó / mező: egyszer állítható érték.
      final context = (debug?['context'] as String?) ?? '';
      // Változó / mező: egyszer állítható érték.
      final hits = (debug?['hits'] as List<dynamic>? ?? const [])
          // Utasítás vége.
          .cast<Map<String, dynamic>>();
      // Előnézet lista a UI-nak (nem feltétlen jelenik meg).
      // Változó / mező: egyszer állítható érték.
      final previews = [
        // Ciklus a listán / tartományon.
        for (var i = 0; i < hits.length; i++)
          // Widget / hívás paraméterlista folytatása.
          RagSourcePreview(
            // Widget / hívás paraméterlista folytatása.
            documentTitle: hits[i]['title'] as String? ?? 'hit',
            // Widget / hívás paraméterlista folytatása.
            chunkIndex: i,
            // Widget / hívás paraméterlista folytatása.
            text: hits[i]['text'] as String? ?? '',
            // Widget / hívás paraméterlista folytatása.
            score: (hits[i]['score'] as num?)?.toDouble() ?? 0,
            // Widget / hívás paraméterlista folytatása.
            usedInPrompt: i < 2,
          // Widget / hívás paraméterlista folytatása.
          ),
      // Utasítás vége.
      ];
      // Értékadás / mezőkitöltés.
      lastContextBlock = context;
      // Értékadás / mezőkitöltés.
      lastPreviews = previews;

      // Asszisztens üzenet frissítése a listában.
      // Változó / mező: egyszer állítható érték.
      final idx = _messages.indexWhere((m) => m.id == assistantId);
      // Feltételes elágazás.
      if (idx != -1) {
        // Widget / hívás paraméterlista folytatása.
        _messages[idx] = _messages[idx].copyWith(
          // Kódsor: részlet a fenti logikából.
          content: hungarianAnswer.isEmpty
              // Kódsor: részlet a fenti logikából.
              ? 'Nem született használható válasz. Kérdezz újra.'
              // Widget / hívás paraméterlista folytatása.
              : hungarianAnswer,
          // Widget / hívás paraméterlista folytatása.
          isStreaming: false,
          // Widget / hívás paraméterlista folytatása.
          ragContextBlock: context,
          // Widget / hívás paraméterlista folytatása.
          ragPreviews: previews,
          // Widget / hívás paraméterlista folytatása.
          ragSearchQuery: englishQuestion,
        // Utasítás vége.
        );
      // Blokk / osztály vége.
      }
      // Utasítás vége.
      notifyListeners();
    // Blokk / szerkezet zárójele.
    } catch (e, st) {
      // Utasítás vége.
      DiagnosticLog.log('CloudChat', 'sendMessage failed: $e\n$st');
      // Feltételes elágazás.
      if (turn == _turnEpoch) {
        // Utasítás vége.
        _finish(assistantId, _friendlyNetworkError(e));
      // Blokk / osztály vége.
      }
    // Blokk / szerkezet zárójele.
    } finally {
      // Generálás vége (ha még ez a kör).
      // Feltételes elágazás.
      if (turn == _turnEpoch) {
        // Értékadás / mezőkitöltés.
        _isGenerating = false;
        // Utasítás vége.
        notifyListeners();
      // Blokk / osztály vége.
      }
    // Blokk / osztály vége.
    }
  // Blokk / osztály vége.
  }

  /// Net / timeout hibák → magyar UI szöveg.
  // Osztályszintű (példány nélküli) tag.
  static String _friendlyNetworkError(Object e) {
    // Feltételes elágazás.
    if (e is CloudUnavailableException) return e.message;
    // Feltételes elágazás.
    if (e is TimeoutException) {
      // Visszatérési érték a hívónak.
      return 'A felhő szolgáltatás nem válaszol időben. '
          // Utasítás vége.
          'Ellenőrizd az internetkapcsolatot, majd próbáld újra.';
    // Blokk / osztály vége.
    }
    // Feltételes elágazás.
    if (e is SocketException) {
      // Visszatérési érték a hívónak.
      return 'Nincs kapcsolat a felhő szolgáltatással. '
          // Utasítás vége.
          'Ellenőrizd az internetet, majd koppints az Újrapróbálásra.';
    // Blokk / osztály vége.
    }
    // Feltételes elágazás.
    if (e is http.ClientException) {
      // Visszatérési érték a hívónak.
      return 'Nincs kapcsolat a felhő szolgáltatással. '
          // Utasítás vége.
          'Ellenőrizd az internetet, majd próbáld újra.';
    // Blokk / osztály vége.
    }
    // Változó / mező: egyszer állítható érték.
    final s = e.toString().toLowerCase();
    // Feltételes elágazás.
    if (s.contains('failed host lookup') ||
        // Kódsor: részlet a fenti logikából.
        s.contains('connection refused') ||
        // Kódsor: részlet a fenti logikából.
        s.contains('network is unreachable') ||
        // Kódsor: részlet a fenti logikából.
        s.contains('connection reset') ||
        // Widget / hívás paraméterlista folytatása.
        s.contains('software caused connection abort')) {
      // Visszatérési érték a hívónak.
      return 'A felhő szolgáltatás jelenleg nem elérhető. '
          // Utasítás vége.
          'Ellenőrizd az internetkapcsolatot, majd próbáld újra.';
    // Blokk / osztály vége.
    }
    // Visszatérési érték a hívónak.
    return 'A felhő szolgáltatás jelenleg nem elérhető. Próbáld újra később.';
  // Blokk / osztály vége.
  }

  /// Asszisztens buborék végleges szövege (hiba / kész).
  // Nincs visszatérési érték.
  void _finish(String id, String content) {
    // Változó / mező: egyszer állítható érték.
    final idx = _messages.indexWhere((m) => m.id == id);
    // Feltételes elágazás.
    if (idx == -1) return;
    // Widget / hívás paraméterlista folytatása.
    _messages[idx] = _messages[idx].copyWith(
      // Widget / hívás paraméterlista folytatása.
      content: content,
      // Widget / hívás paraméterlista folytatása.
      isStreaming: false,
    // Utasítás vége.
    );
    // Utasítás vége.
    notifyListeners();
  // Blokk / osztály vége.
  }

  // Felülírja a szülő/interfész metódusát.
  @override
  /// Felhasználó megszakítja a választ.
  // Aszinkron függvény / Future típus.
  Future<void> stopGeneration() async {
    // Kódsor: részlet a fenti logikából.
    _turnEpoch++; // Érvényteleníti a futó kört.
    // Értékadás / mezőkitöltés.
    _isGenerating = false;
    // Változó / mező: egyszer állítható érték.
    final streaming = _messages.indexWhere((m) => m.isStreaming);
    // Feltételes elágazás.
    if (streaming != -1) {
      // Widget / hívás paraméterlista folytatása.
      _messages[streaming] = _messages[streaming].copyWith(
        // Widget / hívás paraméterlista folytatása.
        content: 'A válasz megszakítva.',
        // Widget / hívás paraméterlista folytatása.
        isStreaming: false,
      // Utasítás vége.
      );
    // Blokk / osztály vége.
    }
    // Utasítás vége.
    notifyListeners();
  // Blokk / osztály vége.
  }

  // Felülírja a szülő/interfész metódusát.
  @override
  /// Új beszélgetés: history törlése.
  // Nincs visszatérési érték.
  void clearHistory() {
    // Utasítás vége.
    _messages.clear();
    // Értékadás / mezőkitöltés.
    lastContextBlock = null;
    // Értékadás / mezőkitöltés.
    lastPreviews = const [];
    // Utasítás vége.
    notifyListeners();
  // Blokk / osztály vége.
  }

  /// HTTP kliens bezárása (dispose).
  // Nincs visszatérési érték.
  void disposeClient() {
    // Utasítás vége.
    _client.close();
  // Blokk / osztály vége.
  }
// Blokk / osztály vége.
}
