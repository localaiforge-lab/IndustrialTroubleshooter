// Téma színek / gradiens.
import 'package:educational_chatbot/features/chat/presentation/theme/lumeei_theme.dart';
// openChat API.
import 'package:educational_chatbot/integration/lumeei_ai_mind.dart';
// Flutter Material UI.
import 'package:flutter/material.dart';

/// Demo host képernyő: FAB megnyitja az AI Mind chatet.
class HomeScreen extends StatelessWidget {
  // Állapot nélküli képernyő.
  const HomeScreen({super.key});

  // Chat route push.
  void _openAiMind(BuildContext context) {
    // Utasítás vége.
    LumeeiAiMind.openChat(context);
  // Blokk / osztály vége.
  }

  // Felülírja a szülő/interfész metódusát.
  @override
  // UI widget építő metódus / típus.
  Widget build(BuildContext context) {
    // LUMEEI sötét téma erőltetése ezen a route-on.
    return Theme(
      // Widget / hívás paraméterlista folytatása.
      data: LumeeiTheme.dark(),
      // Widget / hívás paraméterlista folytatása.
      child: Scaffold(
        // Kódsor: részlet a fenti logikából.
        backgroundColor: LumeeiTheme.voidBlack, // Háttér.
        // Widget / hívás paraméterlista folytatása.
        body: DecoratedBox(
          // Háttérgradiens.
          decoration: const BoxDecoration(
            // Widget / hívás paraméterlista folytatása.
            gradient: LinearGradient(
              // Widget / hívás paraméterlista folytatása.
              begin: Alignment.topLeft,
              // Widget / hívás paraméterlista folytatása.
              end: Alignment.bottomRight,
              // Kódsor: részlet a fenti logikából.
              colors: [
                // Widget / hívás paraméterlista folytatása.
                Color(0xFF0B1020),
                // Widget / hívás paraméterlista folytatása.
                LumeeiTheme.voidBlack,
                // Widget / hívás paraméterlista folytatása.
                Color(0xFF140A22),
              // Widget / hívás paraméterlista folytatása.
              ],
            // Widget / hívás paraméterlista folytatása.
            ),
          // Widget / hívás paraméterlista folytatása.
          ),
          // Widget / hívás paraméterlista folytatása.
          child: SafeArea(
            // Notch / status bar elkerülés.
            child: Padding(
              // Widget / hívás paraméterlista folytatása.
              padding: const EdgeInsets.fromLTRB(28, 36, 28, 28),
              // Widget / hívás paraméterlista folytatása.
              child: Column(
                // Kódsor: részlet a fenti logikából.
                crossAxisAlignment: CrossAxisAlignment.start, // Balra zárt.
                // Kódsor: részlet a fenti logikából.
                children: [
                  // Logo.
                  Image.asset(
                    // Widget / hívás paraméterlista folytatása.
                    'assets/branding/LUMEEiAi.png',
                    // Widget / hívás paraméterlista folytatása.
                    width: 160,
                    // Widget / hívás paraméterlista folytatása.
                    fit: BoxFit.contain,
                  // Widget / hívás paraméterlista folytatása.
                  ),
                  // Fordítási idejű konstans.
                  const SizedBox(height: 28),
                  // Főcím.
                  const Text(
                    // Widget / hívás paraméterlista folytatása.
                    'Lumeei tanulási tér',
                    // Widget / hívás paraméterlista folytatása.
                    style: TextStyle(
                      // Widget / hívás paraméterlista folytatása.
                      color: LumeeiTheme.textPrimary,
                      // Widget / hívás paraméterlista folytatása.
                      fontSize: 28,
                      // Widget / hívás paraméterlista folytatása.
                      fontWeight: FontWeight.w700,
                    // Widget / hívás paraméterlista folytatása.
                    ),
                  // Widget / hívás paraméterlista folytatása.
                  ),
                  // Fordítási idejű konstans.
                  const SizedBox(height: 10),
                  // Rövid magyarázat.
                  const Text(
                    // Kódsor: részlet a fenti logikából.
                    'A jobb alsó gomb megnyitja a LUMEEI AI Mind '
                    // Widget / hívás paraméterlista folytatása.
                    'tananyag-asszisztenst (Cloud Run + Qwen).',
                    // Widget / hívás paraméterlista folytatása.
                    style: TextStyle(
                      // Widget / hívás paraméterlista folytatása.
                      color: LumeeiTheme.textSecondary,
                      // Widget / hívás paraméterlista folytatása.
                      height: 1.45,
                      // Widget / hívás paraméterlista folytatása.
                      fontSize: 15,
                    // Widget / hívás paraméterlista folytatása.
                    ),
                  // Widget / hívás paraméterlista folytatása.
                  ),
                  // Fordítási idejű konstans.
                  const Spacer(), // Kitölti a középső üres helyet.
                  // Infó doboz.
                  Container(
                    // Widget / hívás paraméterlista folytatása.
                    width: double.infinity,
                    // Widget / hívás paraméterlista folytatása.
                    padding: const EdgeInsets.all(18),
                    // Widget / hívás paraméterlista folytatása.
                    decoration: BoxDecoration(
                      // Widget / hívás paraméterlista folytatása.
                      color: LumeeiTheme.surfaceElevated,
                      // Widget / hívás paraméterlista folytatása.
                      borderRadius: BorderRadius.circular(18),
                      // Widget / hívás paraméterlista folytatása.
                      border: Border.all(color: const Color(0x22FFFFFF)),
                    // Widget / hívás paraméterlista folytatása.
                    ),
                    // Widget / hívás paraméterlista folytatása.
                    child: const Text(
                      // Kódsor: részlet a fenti logikából.
                      'Integráció: a Lumeei alkalmazásban ugyanez a floating '
                      // Widget / hívás paraméterlista folytatása.
                      'gomb nyitja majd ezt a modult.',
                      // Widget / hívás paraméterlista folytatása.
                      style: TextStyle(
                        // Widget / hívás paraméterlista folytatása.
                        color: LumeeiTheme.textSecondary,
                        // Widget / hívás paraméterlista folytatása.
                        height: 1.4,
                      // Widget / hívás paraméterlista folytatása.
                      ),
                    // Widget / hívás paraméterlista folytatása.
                    ),
                  // Widget / hívás paraméterlista folytatása.
                  ),
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
        // Jobb alsó FAB → chat.
        floatingActionButton: _AiMindFab(onPressed: () => _openAiMind(context)),
      // Widget / hívás paraméterlista folytatása.
      ),
    // Utasítás vége.
    );
  // Blokk / osztály vége.
  }
// Blokk / osztály vége.
}

/// Kör alakú márka-FAB.
class _AiMindFab extends StatelessWidget {
  // Fordítási idejű konstans.
  const _AiMindFab({required this.onPressed});

  // Koppintás kezelő.
  final VoidCallback onPressed;

  // Felülírja a szülő/interfész metódusát.
  @override
  // UI widget építő metódus / típus.
  Widget build(BuildContext context) {
    // Visszatérési érték a hívónak.
    return GestureDetector(
      // Kódsor: részlet a fenti logikából.
      onTap: onPressed, // Chat megnyitása.
      // Widget / hívás paraméterlista folytatása.
      child: Container(
        // Kódsor: részlet a fenti logikából.
        width: 68, // FAB méret.
        // Widget / hívás paraméterlista folytatása.
        height: 68,
        // Widget / hívás paraméterlista folytatása.
        decoration: BoxDecoration(
          // Kódsor: részlet a fenti logikából.
          shape: BoxShape.circle, // Kör.
          // Kódsor: részlet a fenti logikából.
          gradient: LumeeiTheme.brandGradient, // Márka szegélyfény.
          // Kódsor: részlet a fenti logikából.
          boxShadow: [
            // Widget / hívás paraméterlista folytatása.
            BoxShadow(
              // Kódsor: részlet a fenti logikából.
              color: LumeeiTheme.cyan.withValues(alpha: 0.35), // Fényárnyék.
              // Widget / hívás paraméterlista folytatása.
              blurRadius: 18,
              // Widget / hívás paraméterlista folytatása.
              offset: const Offset(0, 6),
            // Widget / hívás paraméterlista folytatása.
            ),
          // Widget / hívás paraméterlista folytatása.
          ],
        // Widget / hívás paraméterlista folytatása.
        ),
        // Kódsor: részlet a fenti logikából.
        padding: const EdgeInsets.all(3), // Vékony gyűrű a logo körül.
        // Widget / hívás paraméterlista folytatása.
        child: ClipOval(
          // Körre vágott belső.
          child: ColoredBox(
            // Kódsor: részlet a fenti logikából.
            color: LumeeiTheme.voidBlack, // Belső háttér.
            // Widget / hívás paraméterlista folytatása.
            child: Image.asset(
              // Widget / hívás paraméterlista folytatása.
              'assets/branding/LUMEEiAi.png',
              // Widget / hívás paraméterlista folytatása.
              fit: BoxFit.cover,
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
