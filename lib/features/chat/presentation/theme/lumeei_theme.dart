// Flutter Material: Color, ThemeData, InputDecorationTheme…
import 'package:flutter/material.dart';

/// LUMEEI vizuális tokenek (sötét tananyag-asszisztens kinézet).
abstract final class LumeeiTheme {
  // Fő háttér (majdnem fekete).
  static const Color voidBlack = Color(0xFF07070C);
  // Alap felület szín.
  static const Color surface = Color(0xFF12121A);
  // Emelt kártya / input háttér.
  static const Color surfaceElevated = Color(0xFF1A1A26);
  // Márka cián.
  static const Color cyan = Color(0xFF00E5FF);
  // Márka kék.
  static const Color blue = Color(0xFF4A90E2);
  // Márka lila.
  static const Color purple = Color(0xFF9B5CFF);
  // Fő szöveg (fehér).
  static const Color textPrimary = Color(0xFFFFFFFF);
  // Másodlagos szöveg (szürke).
  static const Color textSecondary = Color(0xFFB8B8C8);

  // Chip / gomb márka-gradiens (cián → kék → lila).
  static const LinearGradient brandGradient = LinearGradient(
    // Kódsor: részlet a fenti logikából.
    begin: Alignment.centerLeft, // Balról.
    // Kódsor: részlet a fenti logikából.
    end: Alignment.centerRight, // Jobbra.
    // Kódsor: részlet a fenti logikából.
    colors: [cyan, blue, purple], // Három márkaszín.
  // Utasítás vége.
  );

  // Finom fény effekt üres állapothoz.
  static const LinearGradient softGlow = LinearGradient(
    // Widget / hívás paraméterlista folytatása.
    begin: Alignment.topLeft,
    // Widget / hívás paraméterlista folytatása.
    end: Alignment.bottomRight,
    // Kódsor: részlet a fenti logikából.
    colors: [
      // Kódsor: részlet a fenti logikából.
      Color(0x3300E5FF), // Áttetsző cián.
      // Kódsor: részlet a fenti logikából.
      Color(0x229B5CFF), // Áttetsző lila.
      // Kódsor: részlet a fenti logikából.
      Color(0x00000000), // Teljesen átlátszó.
    // Widget / hívás paraméterlista folytatása.
    ],
  // Utasítás vége.
  );

  /// Sötét ThemeData az egész modulhoz.
  static ThemeData dark() {
    // Alap ColorScheme a cián seedből.
    final base = ColorScheme.fromSeed(
      // Widget / hívás paraméterlista folytatása.
      seedColor: cyan,
      // Widget / hívás paraméterlista folytatása.
      brightness: Brightness.dark,
    // Utasítás vége.
    );
    // Teljes ThemeData felülírásokkal.
    return ThemeData(
      // Kódsor: részlet a fenti logikából.
      useMaterial3: true, // Material 3 komponensek.
      // Kódsor: részlet a fenti logikából.
      brightness: Brightness.dark, // Sötét paletta.
      // Kódsor: részlet a fenti logikából.
      scaffoldBackgroundColor: voidBlack, // Scaffold alap háttér.
      // Widget / hívás paraméterlista folytatása.
      colorScheme: base.copyWith(
        // Kódsor: részlet a fenti logikából.
        primary: cyan, // Elsődleges akció szín.
        // Kódsor: részlet a fenti logikából.
        secondary: purple, // Másodlagos akcent.
        // Kódsor: részlet a fenti logikából.
        surface: surface, // Felület.
        // Kódsor: részlet a fenti logikából.
        onSurface: textPrimary, // Felületen lévő szöveg.
      // Widget / hívás paraméterlista folytatása.
      ),
      // Widget / hívás paraméterlista folytatása.
      appBarTheme: const AppBarTheme(
        // Kódsor: részlet a fenti logikából.
        backgroundColor: Colors.transparent, // Átlátszó app bar.
        // Kódsor: részlet a fenti logikából.
        elevation: 0, // Nincs árnyék.
        // Kódsor: részlet a fenti logikából.
        centerTitle: false, // Cím balra.
        // Kódsor: részlet a fenti logikából.
        foregroundColor: textPrimary, // Ikonok/szöveg színe.
      // Widget / hívás paraméterlista folytatása.
      ),
      // Widget / hívás paraméterlista folytatása.
      inputDecorationTheme: InputDecorationTheme(
        // Kódsor: részlet a fenti logikából.
        filled: true, // Kitöltött mező.
        // Kódsor: részlet a fenti logikából.
        fillColor: surfaceElevated, // Mező háttér.
        // Kódsor: részlet a fenti logikából.
        hintStyle: const TextStyle(color: textSecondary), // Hint szín.
        // Widget / hívás paraméterlista folytatása.
        border: OutlineInputBorder(
          // Kódsor: részlet a fenti logikából.
          borderRadius: BorderRadius.circular(28), // Lekerekítés.
          // Kódsor: részlet a fenti logikából.
          borderSide: BorderSide.none, // Alapból nincs keret.
        // Widget / hívás paraméterlista folytatása.
        ),
        // Widget / hívás paraméterlista folytatása.
        enabledBorder: OutlineInputBorder(
          // Widget / hívás paraméterlista folytatása.
          borderRadius: BorderRadius.circular(28),
          // Kódsor: részlet a fenti logikából.
          borderSide: const BorderSide(color: Color(0x33FFFFFF)), // Halvány keret.
        // Widget / hívás paraméterlista folytatása.
        ),
        // Widget / hívás paraméterlista folytatása.
        focusedBorder: OutlineInputBorder(
          // Widget / hívás paraméterlista folytatása.
          borderRadius: BorderRadius.circular(28),
          // Kódsor: részlet a fenti logikából.
          borderSide: const BorderSide(color: cyan, width: 1.4), // Fókusz: cián.
        // Widget / hívás paraméterlista folytatása.
        ),
        // Kódsor: részlet a fenti logikából.
        contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14), // Belső margó.
      // Widget / hívás paraméterlista folytatása.
      ),
    // Utasítás vége.
    );
  // Blokk / osztály vége.
  }
// Blokk / osztály vége.
}
