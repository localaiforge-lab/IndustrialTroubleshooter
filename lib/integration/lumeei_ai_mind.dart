// DI (ServiceLocator) – init sikerének ellenőrzése.
import 'package:educational_chatbot/core/di/service_locator.dart';
// Diagnosztikai napló.
import 'package:educational_chatbot/core/utils/diagnostic_log.dart';
// Chat UI képernyő.
import 'package:educational_chatbot/features/chat/presentation/screens/lumeei_ai_mind_chat_screen.dart';
// Sötét téma.
import 'package:educational_chatbot/features/chat/presentation/theme/lumeei_theme.dart';
// Flutter widgetek + navigáció.
import 'package:flutter/material.dart';

/// Host appoknak szánt publikus API (initialize / openChat).
class LumeeiAiMind {
  // Ne példányosítsuk.
  LumeeiAiMind._();

  // true, ha a ServiceLocator.init sikeres.
  static bool get isInitialized => ServiceLocator.isInitialized;

  /// Cloud Run health + fordító előkészítés.
  static Future<void> initialize({
    // Opcionális progress callback a splash UI-nak.
    void Function(String status, double? progress)? onProgress,
  // Blokk / szerkezet zárójele.
  }) async {
    // Rövid helper a státusz jelentéshez.
    void report(String status, [double? progress]) {
      // Kódsor: részlet a fenti logikából.
      onProgress?.call(status, progress); // Ha van listener, szólunk.
    // Blokk / osztály vége.
    }

    // Aszinkron művelet megvárása.
    await DiagnosticLog.init(); // Napló fájl megnyitása.
    // Kódsor: részlet a fenti logikából.
    DiagnosticLog.installGlobalHandlers(); // Globális hibák naplózása.
    // Kódsor: részlet a fenti logikából.
    DiagnosticLog.log('LumeeiAiMind', 'initialize() start'); // Indulás jelzése.

    // Kódsor: részlet a fenti logikából.
    report('Inicializálás…', 0.1); // Splash szöveg.
    // Aszinkron művelet megvárása.
    await ServiceLocator.init(); // Konfig + ping + fordító.
    // Kódsor: részlet a fenti logikából.
    report('Kész', 1); // 100% kész.
    // Widget / hívás paraméterlista folytatása.
    DiagnosticLog.log(
      // Widget / hívás paraméterlista folytatása.
      'LumeeiAiMind',
      // Kódsor: részlet a fenti logikából.
      'initialize() cloud → ${ServiceLocator.config.cloudBaseUrl}', // URL napló.
    // Utasítás vége.
    );
  // Blokk / osztály vége.
  }

  /// Splash „kihagyás” gomb kompatibilitás (online-only fordítónál no-op).
  static void skipOfflineTranslatorWait() {
    // Utasítás vége.
    ServiceLocator.translation?.skipStartupOfflineDownload();
  // Blokk / osztály vége.
  }

  /// Chat widget visszaadása (route / embed).
  static Widget chatScreen({
    // Kódsor: részlet a fenti logikából.
    Key? key, // Opcionális widget key.
    // Igaz/hamis mező vagy változó.
    bool showBackButton = true, // Host FAB esetén legyen vissza gomb.
  // Blokk / szerkezet zárójele.
  }) {
    // Visszatérési érték a hívónak.
    return LumeeiAiMindChatScreen(
      // Widget / hívás paraméterlista folytatása.
      key: key,
      // Widget / hívás paraméterlista folytatása.
      showBackButton: showBackButton,
    // Utasítás vége.
    );
  // Blokk / osztály vége.
  }

  /// Chat megnyitása push navigációval (fade + slide).
  static Future<T?> openChat<T extends Object?>(
    // Widget / hívás paraméterlista folytatása.
    BuildContext context, {
    // Igaz/hamis mező vagy változó.
    bool showBackButton = true,
  // Blokk / szerkezet zárójele.
  }) {
    // Visszatérési érték a hívónak.
    return Navigator.of(context).push<T>(
      // Widget / hívás paraméterlista folytatása.
      PageRouteBuilder<T>(
        // Az oldal tartalma a chat képernyő.
        pageBuilder: (_, animation, __) => chatScreen(
          // Widget / hívás paraméterlista folytatása.
          showBackButton: showBackButton,
        // Widget / hívás paraméterlista folytatása.
        ),
        // Áttűnés animáció.
        transitionsBuilder: (_, animation, __, child) {
          // Görbe: lassuló kimenet.
          final curved = CurvedAnimation(
            // Widget / hívás paraméterlista folytatása.
            parent: animation,
            // Widget / hívás paraméterlista folytatása.
            curve: Curves.easeOutCubic,
          // Utasítás vége.
          );
          // Visszatérési érték a hívónak.
          return FadeTransition(
            // Kódsor: részlet a fenti logikából.
            opacity: curved, // Fokozatos megjelenés.
            // Widget / hívás paraméterlista folytatása.
            child: SlideTransition(
              // Widget / hívás paraméterlista folytatása.
              position: Tween<Offset>(
                // Kódsor: részlet a fenti logikából.
                begin: const Offset(0, 0.06), // Kicsit alulról.
                // Kódsor: részlet a fenti logikából.
                end: Offset.zero, // Végső pozíció.
              // Widget / hívás paraméterlista folytatása.
              ).animate(curved),
              // Kódsor: részlet a fenti logikából.
              child: child, // Maga a chat.
            // Widget / hívás paraméterlista folytatása.
            ),
          // Utasítás vége.
          );
        // Blokk / szerkezet zárójele.
        },
      // Widget / hívás paraméterlista folytatása.
      ),
    // Utasítás vége.
    );
  // Blokk / osztály vége.
  }

  /// Host opcionálisan ezzel a témával csomagolhatja a route-ot.
  static ThemeData get theme => LumeeiTheme.dark();

  /// Erőforrások elengedése (teszt / hot restart).
  static Future<void> dispose() => ServiceLocator.dispose();
// Blokk / osztály vége.
}
