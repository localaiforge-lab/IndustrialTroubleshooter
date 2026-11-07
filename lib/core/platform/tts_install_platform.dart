// Platform.isAndroid ellenőrzéshez.
import 'dart:io';

// Natív MethodChannel a Java/Kotlin TTS beállítások megnyitásához.
import 'package:flutter/services.dart';

/// Android TTS hangcsomag / beállítás UI megnyitása.
class TtsInstallPlatform {
  // Ne példányosítsuk – csak static metódusok.
  TtsInstallPlatform._();

  // Flutter ↔ Android kommunikációs csatorna azonosítója.
  static const _channel =
      // Utasítás vége.
      MethodChannel('hu.educational.educational_chatbot/tts_install');

  /// Megnyitja a rendszer TTS telepítő / beállítás képernyőjét.
  /// Visszatérés: státusz string, vagy null / failed.
  static Future<String?> openVoiceInstall() async {
    // iOS/desktopön nincs ilyen natív flow.
    if (!Platform.isAndroid) return null;
    // Natív metódus hívása; az eredmény egy rövid státusz kód.
    final result = await _channel.invokeMethod<String>('openTtsVoiceInstall');
    // Visszaadjuk a natív oldali választ a UI-nak.
    return result;
  // Blokk / osztály vége.
  }
// Blokk / osztály vége.
}
