// Alkalmazás-konfig (cloudBaseUrl).
import 'package:educational_chatbot/core/config/app_config.dart';
// HTTP chat kliens a Cloud Run felé.
import 'package:educational_chatbot/features/chat/data/cloud_chat_service.dart';
// Chat absztrakció (UI ettől függ).
import 'package:educational_chatbot/features/chat/domain/chat_service.dart';
// Online Hu↔En fordító.
import 'package:educational_chatbot/features/translation/data/translation_service.dart';
// ChangeNotifier típus a listenhető chat-hez.
import 'package:flutter/foundation.dart';
// Kis kulcs–érték tároló (pl. kiválasztott tankönyv).
import 'package:shared_preferences/shared_preferences.dart';

/// Egyszerű DI (service locator): cloud chat + fordító.
class ServiceLocator {
  // Privát konstruktor: ne lehessen példányosítani, csak static tagok.
  ServiceLocator._();

  // Betöltött konfig (null, amíg nincs init).
  static AppConfig? _config;
  // SharedPreferences példány.
  static SharedPreferences? _prefs;
  // Aktív chat szolgáltatás (CloudChatService).
  static ChatService? _chat;
  // Fordító (online Google Translate wrapper).
  static TranslationService? translation;

  // Konfig getter – ha nincs init, hibát dob.
  static AppConfig get config =>
      // Utasítás vége.
      _config ?? (throw StateError('ServiceLocator not initialized'));
  // Prefs getter – ha nincs init, hibát dob.
  static SharedPreferences get prefs =>
      // Utasítás vége.
      _prefs ?? (throw StateError('ServiceLocator not initialized'));
  // Chat getter – ha nincs init, hibát dob.
  static ChatService get chat =>
      // Utasítás vége.
      _chat ?? (throw StateError('ServiceLocator not initialized'));

  // Jelzi, hogy az init sikeresen lefutott-e.
  static bool _initialized = false;
  // Publikus flag az UI / host számára.
  static bool get isInitialized => _initialized;
  // Cloud-only app: inicializálás = cloud mód.
  static bool get isCloudMode => _initialized;

  // Minden szolgáltatás előkészítése (konfig, fordító, health ping).
  static Future<void> init() async {
    // Ha már kész, ne csináljunk semmit.
    if (_initialized) return;
    // Előző részleges állapot törlése (Újrapróbálás esetén is biztonságos).
    await dispose();

    // app_config.json betöltése.
    final loaded = await AppConfig.load();
    // SharedPreferences megnyitása.
    final preferences = await SharedPreferences.getInstance();
    // Fordító létrehozása.
    translation = TranslationService();
    // Online módra állítás (nincs ML Kit pack várakozás).
    await translation!.ensureReadyOnlineOnly();

    // Cloud HTTP kliens a konfig URL-lel.
    final cloud = CloudChatService(
      // Kódsor: részlet a fenti logikából.
      baseUrl: loaded.cloudBaseUrl, // Cloud Run cím.
      // Kódsor: részlet a fenti logikából.
      translation: translation!, // Telefonon fordít Hu↔En.
    // Utasítás vége.
    );
    // /health hívás: net + llmReady ellenőrzés.
    await cloud.ping();

    // Sikeres ping után elmentjük a referenciákat.
    _config = loaded;
    // Értékadás / mezőkitöltés.
    _prefs = preferences;
    // Értékadás / mezőkitöltés.
    _chat = cloud;
    // Értékadás / mezőkitöltés.
    _initialized = true; // Mostantól isInitialized == true.
  // Blokk / osztály vége.
  }

  // Erőforrások elengedése (retry / tesztek).
  static Future<void> dispose() async {
    // Változó / mező: egyszer állítható érték.
    final c = _chat; // Lokális másolat a típusellenőrzéshez.
    // HTTP kliens bezárása, ha CloudChatService.
    if (c is CloudChatService) {
      // Utasítás vége.
      c.disposeClient();
    // Blokk / osztály vége.
    }
    // Fordító takarítás.
    await translation?.dispose();
    // Minden static mező nullázása.
    translation = null;
    // Értékadás / mezőkitöltés.
    _chat = null;
    // Értékadás / mezőkitöltés.
    _prefs = null;
    // Értékadás / mezőkitöltés.
    _config = null;
    // Értékadás / mezőkitöltés.
    _initialized = false;
  // Blokk / osztály vége.
  }
// Blokk / osztály vége.
}

/// A chat UI addListener-hez ChangeNotifier-ként kapja a ChatService-t.
ChangeNotifier chatAsListenable(ChatService chat) {
  // Ha ChangeNotifier, visszaadjuk castolva.
  if (chat is ChangeNotifier) return chat as ChangeNotifier;
  // Egyébként programozási hiba.
  throw StateError('ChatService must be a ChangeNotifier');
// Blokk / osztály vége.
}
