// Timer a splash eltelt idejének méréséhez.
import 'dart:async';

// A fő app widget (splash után).
import 'package:educational_chatbot/app.dart';
// Diagnosztikai napló.
import 'package:educational_chatbot/core/utils/diagnostic_log.dart';
// LumeeiAiMind.initialize / dispose.
import 'package:educational_chatbot/integration/lumeei_ai_mind.dart';
// Flutter UI + runApp.
import 'package:flutter/material.dart';
// Riverpod ProviderScope a fő app körül.
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// App indítás: binding, napló, splash, majd a valódi MaterialApp.
Future<void> bootstrap() async {
  // Flutter engine / plugin binding kötelező async main előtt.
  WidgetsFlutterBinding.ensureInitialized();
  // Naplófájl előkészítése.
  await DiagnosticLog.init();
  // Globális hibák a naplóba menjenek.
  DiagnosticLog.installGlobalHandlers();
  // Indulás jelzése.
  DiagnosticLog.log('Bootstrap', 'App starting');
  // Először a splash / startup widget jelenik meg.
  runApp(const _StartupApp());
// Blokk / osztály vége.
}

/// Splash képernyő widget (állapotos: progress + hiba).
class _StartupApp extends StatefulWidget {
  // Privát widget, csak ebben a fájlban.
  const _StartupApp();

  // Felülírja a szülő/interfész metódusát.
  @override
  // Állapot objektum létrehozása.
  State<_StartupApp> createState() => _StartupAppState();
// Blokk / osztály vége.
}

/// Splash logika: initialize hívás, timer, hiba UI.
class _StartupAppState extends State<_StartupApp> {
  // 0..1 progress a LinearProgressIndicatornek (null = meghatározatlan).
  double? _progress;
  // Státuszszöveg a felhasználónak.
  String _status = 'Inicializálás…';
  // Ha nem null, hibaállapotban vagyunk.
  Object? _error;
  // Másodperc számláló a splashen.
  var _elapsedSec = 0;
  // Periodikus timer az _elapsedSec növelésére.
  Timer? _elapsedTimer;

  // Felülírja a szülő/interfész metódusát.
  @override
  // Nincs visszatérési érték.
  void initState() {
    // Szülő State init.
    super.initState();
    // Másodpercenként frissítjük az eltelt időt.
    _elapsedTimer = Timer.periodic(const Duration(seconds: 1), (_) {
      // Widget már nincs a fában → ne hívjunk setState-et.
      if (!mounted) return;
      // Eltelt másodperc növelése + UI frissítés.
      setState(() => _elapsedSec++);
    // Blokk / szerkezet zárójele.
    });
    // Cloud init elindítása.
    _start();
  // Blokk / osztály vége.
  }

  // Felülírja a szülő/interfész metódusát.
  @override
  // Nincs visszatérési érték.
  void dispose() {
    // Timer leállítása memória szivárgás ellen.
    _elapsedTimer?.cancel();
    // Szülő dispose.
    super.dispose();
  // Blokk / osztály vége.
  }

  /// Cloud Run ping + fordító; siker esetén átvált a fő appre.
  Future<void> _start() async {
    // Hibakezelés kezdete (try).
    try {
      // ServiceLocator.init a háttérben.
      await LumeeiAiMind.initialize(
        // Widget / hívás paraméterlista folytatása.
        onProgress: (status, progress) {
          // Ha már nem él a splash, ne frissítsünk.
          if (!mounted) return;
          // Státusz és progress a splash UI-ra.
          setState(() {
            // Értékadás / mezőkitöltés.
            _status = status;
            // Értékadás / mezőkitöltés.
            _progress = progress;
          // Blokk / szerkezet zárójele.
          });
        // Blokk / szerkezet zárójele.
        },
      // Utasítás vége.
      );
      // Init közben elnavigálhattak / unmount.
      if (!mounted) return;
      // Nincs többé szükség a stopperre.
      _elapsedTimer?.cancel();
      // Rövid szünet a „Kész” feliratnak.
      await Future<void>.delayed(const Duration(milliseconds: 200));
      // Újra mounted ellenőrzés a delay után.
      if (!mounted) return;
      // Splash lecserélése a valódi appre.
      runApp(
        // Fordítási idejű konstans.
        const ProviderScope(
          // Riverpod scope a leszármazott widgeteknek.
          child: EducationalChatbotApp(),
        // Widget / hívás paraméterlista folytatása.
        ),
      // Utasítás vége.
      );
    // Blokk / szerkezet zárójele.
    } catch (e, st) {
      // Hiba naplózása.
      DiagnosticLog.log('Startup', 'ERROR: $e\n$st');
      // Konzolra is.
      debugPrint('[Startup] $e\n$st');
      // UI hibaállapot, ha még él a widget.
      if (mounted) {
        // Exception: prefix levágása olvashatóbb üzenethez.
        var msg = e.toString();
        // Feltételes elágazás.
        if (msg.startsWith('Exception: ')) {
          // Értékadás / mezőkitöltés.
          msg = msg.substring('Exception: '.length);
        // Blokk / osztály vége.
        }
        // UI újrarajzolás kérése állapotváltozás után.
        setState(() {
          // Értékadás / mezőkitöltés.
          _error = e; // Nyers hiba objektum.
          // Egységes „Hiba: …” prefix.
          _status = msg.startsWith('Hiba:') ? msg : 'Hiba: $msg';
        // Blokk / szerkezet zárójele.
        });
      // Blokk / osztály vége.
      }
    // Blokk / osztály vége.
    }
  // Blokk / osztály vége.
  }

  // Felülírja a szülő/interfész metódusát.
  @override
  // UI widget építő metódus / típus.
  Widget build(BuildContext context) {
    // Minimális MaterialApp csak a splashhez.
    return MaterialApp(
      // Kódsor: részlet a fenti logikából.
      debugShowCheckedModeBanner: false, // DEBUG szalag kikapcsolva.
      // Widget / hívás paraméterlista folytatása.
      theme: ThemeData(
        // Kódsor: részlet a fenti logikából.
        brightness: Brightness.dark, // Sötét téma.
        // Kódsor: részlet a fenti logikából.
        scaffoldBackgroundColor: const Color(0xFF07070C), // Háttér.
        // Widget / hívás paraméterlista folytatása.
        colorScheme: const ColorScheme.dark(
          // Kódsor: részlet a fenti logikából.
          primary: Color(0xFF00E5FF), // Cián.
          // Kódsor: részlet a fenti logikából.
          secondary: Color(0xFF9B5CFF), // Lila.
        // Widget / hívás paraméterlista folytatása.
        ),
      // Widget / hívás paraméterlista folytatása.
      ),
      // Widget / hívás paraméterlista folytatása.
      home: Scaffold(
        // Középre igazított tartalom.
        body: Center(
          // Widget / hívás paraméterlista folytatása.
          child: Padding(
            // Kódsor: részlet a fenti logikából.
            padding: const EdgeInsets.all(32), // Külső margó.
            // Widget / hívás paraméterlista folytatása.
            child: Column(
              // Kódsor: részlet a fenti logikából.
              mainAxisAlignment: MainAxisAlignment.center, // Függőleges közép.
              // Kódsor: részlet a fenti logikából.
              children: [
                // Márkalogó.
                Image.asset(
                  // Widget / hívás paraméterlista folytatása.
                  'assets/branding/LUMEEiAi.png',
                  // Widget / hívás paraméterlista folytatása.
                  width: 160,
                  // Widget / hívás paraméterlista folytatása.
                  fit: BoxFit.contain,
                  // Ha a kép hiányzik, szöveges fallback.
                  errorBuilder: (_, __, ___) => const Text(
                    // Widget / hívás paraméterlista folytatása.
                    'LUMEEI AI Mind',
                    // Widget / hívás paraméterlista folytatása.
                    style: TextStyle(fontSize: 20, fontWeight: FontWeight.w600),
                    // Widget / hívás paraméterlista folytatása.
                    textAlign: TextAlign.center,
                  // Widget / hívás paraméterlista folytatása.
                  ),
                // Widget / hívás paraméterlista folytatása.
                ),
                // Fordítási idejű konstans.
                const SizedBox(height: 28), // Térköz.
                // Progress csak ha nincs hiba.
                if (_error == null) ...[
                  // Határozott progress, ha van érték.
                  if (_progress != null)
                    // Widget / hívás paraméterlista folytatása.
                    LinearProgressIndicator(
                      // Kódsor: részlet a fenti logikából.
                      value: _progress!.clamp(0, 1), // 0..1 tartomány.
                      // Widget / hívás paraméterlista folytatása.
                      color: const Color(0xFF00E5FF),
                      // Widget / hívás paraméterlista folytatása.
                      backgroundColor: const Color(0x33FFFFFF),
                    // Kódsor: részlet a fenti logikából.
                    )
                  // Kódsor: részlet a fenti logikából.
                  else
                    // Határozatlan (végtelen) progress.
                    const LinearProgressIndicator(
                      // Widget / hívás paraméterlista folytatása.
                      color: Color(0xFF00E5FF),
                      // Widget / hívás paraméterlista folytatása.
                      backgroundColor: Color(0x33FFFFFF),
                    // Widget / hívás paraméterlista folytatása.
                    ),
                  // Fordítási idejű konstans.
                  const SizedBox(height: 16),
                // Widget / hívás paraméterlista folytatása.
                ],
                // Státusz / hibaüzenet.
                Text(
                  // Widget / hívás paraméterlista folytatása.
                  _status,
                  // Widget / hívás paraméterlista folytatása.
                  textAlign: TextAlign.center,
                  // Widget / hívás paraméterlista folytatása.
                  style: const TextStyle(
                    // Widget / hívás paraméterlista folytatása.
                    color: Color(0xFFB8B8C8),
                    // Widget / hívás paraméterlista folytatása.
                    height: 1.35,
                  // Widget / hívás paraméterlista folytatása.
                  ),
                // Widget / hívás paraméterlista folytatása.
                ),
                // Fordítási idejű konstans.
                const SizedBox(height: 8),
                // Eltelt idő.
                Text(
                  // Widget / hívás paraméterlista folytatása.
                  'Eltelt idő: ${_elapsedSec}s',
                  // Widget / hívás paraméterlista folytatása.
                  style: const TextStyle(
                    // Widget / hívás paraméterlista folytatása.
                    color: Color(0x88B8B8C8),
                    // Widget / hívás paraméterlista folytatása.
                    fontSize: 12,
                  // Widget / hívás paraméterlista folytatása.
                  ),
                // Widget / hívás paraméterlista folytatása.
                ),
                // Hiba esetén súgó + újrapróbálás.
                if (_error != null) ...[
                  // Fordítási idejű konstans.
                  const SizedBox(height: 12),
                  // Fordítási idejű konstans.
                  const Text(
                    // Kódsor: részlet a fenti logikából.
                    'A tananyag-asszisztens a felhőn fut.\n'
                    // Kódsor: részlet a fenti logikából.
                    'Ha nincs internet, vagy a szolgáltatás átmenetileg '
                    // Widget / hívás paraméterlista folytatása.
                    'szünetel, az Újrapróbálás gombbal próbálkozhatsz.',
                    // Widget / hívás paraméterlista folytatása.
                    textAlign: TextAlign.center,
                    // Widget / hívás paraméterlista folytatása.
                    style: TextStyle(
                      // Widget / hívás paraméterlista folytatása.
                      color: Color(0x88B8B8C8),
                      // Widget / hívás paraméterlista folytatása.
                      fontSize: 12,
                      // Widget / hívás paraméterlista folytatása.
                      height: 1.35,
                    // Widget / hívás paraméterlista folytatása.
                    ),
                  // Widget / hívás paraméterlista folytatása.
                  ),
                  // Fordítási idejű konstans.
                  const SizedBox(height: 16),
                  // Widget / hívás paraméterlista folytatása.
                  TextButton(
                    // Widget / hívás paraméterlista folytatása.
                    onPressed: () async {
                      // Hibaállapot törlése.
                      setState(() {
                        // Értékadás / mezőkitöltés.
                        _error = null;
                        // Értékadás / mezőkitöltés.
                        _status = 'Újrapróbálás…';
                        // Értékadás / mezőkitöltés.
                        _elapsedSec = 0;
                      // Blokk / szerkezet zárójele.
                      });
                      // Régi DI állapot elengedése.
                      await LumeeiAiMind.dispose();
                      // Unmount védelem.
                      if (!mounted) return;
                      // Újraindítás.
                      _start();
                    // Blokk / szerkezet zárójele.
                    },
                    // Widget / hívás paraméterlista folytatása.
                    child: const Text(
                      // Widget / hívás paraméterlista folytatása.
                      'Újrapróbálás',
                      // Widget / hívás paraméterlista folytatása.
                      style: TextStyle(color: Color(0xFF00E5FF)),
                    // Widget / hívás paraméterlista folytatása.
                    ),
                  // Widget / hívás paraméterlista folytatása.
                  ),
                // Widget / hívás paraméterlista folytatása.
                ],
              // Widget / hívás paraméterlista folytatása.
              ],
            // Widget / hívás paraméterlista folytatása.
            ),
          // Widget / hívás paraméterlista folytatása.
          ),
        // Widget / hívás paraméterlista folytatása.
        ),
      // Widget / hívás paraméterlista folytatása.
      ),
    // Utasítás vége.
    );
  // Blokk / osztály vége.
  }
// Blokk / osztály vége.
}
