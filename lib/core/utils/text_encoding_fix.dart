// latin1.encode / utf8.decode a mojibake javításhoz.
import 'dart:convert';

/// Hibás kódolású magyar szöveg javítása (pl. "BÃ©la" → "Béla").
///
/// Gyakori ok: UTF-8 bájtokat Latin-1-ként olvasták, néha szóközzel törve.
String fixUtf8Mojibake(String input) {
  // Üres bemenet: nincs mit javítani.
  if (input.isEmpty) return input;

  // Munkaváltozó, amit lépésenként javítunk.
  var s = input;

  // "Ã ©" → "Ã©" (szóköz eltávolítása a multi-byte szekvenciából).
  s = s.replaceAllMapped(
    // Kódsor: részlet a fenti logikából.
    RegExp(r'Ã\s+([\u00A0-\u00FF])'), // Ã + szóköz + Latin-1 karakter.
    // Értékadás / mezőkitöltés.
    (m) => 'Ã${m[1]}', // Összevonás szóköz nélkül.
  // Utasítás vége.
  );
  // Ugyanez Â prefixre.
  s = s.replaceAllMapped(
    // Widget / hívás paraméterlista folytatása.
    RegExp(r'Â\s+([\u00A0-\u00FF])'),
    // Widget / hívás paraméterlista folytatása.
    (m) => 'Â${m[1]}',
  // Utasítás vége.
  );

  // Csak a gyanús tokeneket dekódoljuk újra (ne az egész mondatot).
  if (s.contains('Ã') || s.contains('Â')) {
    // Widget / hívás paraméterlista folytatása.
    s = s.replaceAllMapped(
      // Kódsor: részlet a fenti logikából.
      RegExp(r'[^\s]*[ÃÂ][^\s]*'), // Nem-üres token Ã/Â karakterrel.
      // Widget / hívás paraméterlista folytatása.
      (m) {
        // Változó / mező: egyszer állítható érték.
        final part = m[0]!; // Illeszkedő részstring.
        // Hibakezelés kezdete (try).
        try {
          // Latin-1 bájtokként értelmezve → UTF-8 szöveg.
          final repaired = utf8.decode(latin1.encode(part));
          // Csak akkor fogadjuk el, ha „magyarabb” lett.
          if (_scoreHungarianText(repaired) >= _scoreHungarianText(part)) {
            // Visszatérési érték a hívónak.
            return repaired;
          // Blokk / osztály vége.
          }
        // Blokk / szerkezet zárójele.
        } catch (_) {} // Hibás bájtsor: hagyjuk az eredetit.
        // Visszatérési érték a hívónak.
        return part;
      // Blokk / szerkezet zárójele.
      },
    // Utasítás vége.
    );
  // Blokk / osztály vége.
  }

  // "Bé La" → "Béla" típusú törött név-összevonás.
  s = s.replaceAllMapped(
    // Widget / hívás paraméterlista folytatása.
    RegExp(
      // Widget / hívás paraméterlista folytatása.
      r'([ÁÉÍÓÖŐÚÜŰáéíóöőúüű])\s+([A-Za-zÁÉÍÓÖŐÚÜŰáéíóöőúüű]{1,2})\b',
      // Kódsor: részlet a fenti logikából.
      unicode: true, // Unicode szóhatár.
    // Widget / hívás paraméterlista folytatása.
    ),
    // Értékadás / mezőkitöltés.
    (m) => '${m[1]}${m[2]!.toLowerCase()}', // Ékezetes + kisbetűs folytatás.
  // Utasítás vége.
  );

  // Javított szöveg visszaadása.
  return s;
// Blokk / osztály vége.
}

/// Egyszerű pontozás: ékezetes magyar betűk jók, Ã/Â rosszak.
int _scoreHungarianText(String s) {
  // Lokális változó.
  var score = 0; // Kezdőpont.
  // Fordítási idejű konstans.
  const good = 'áéíóöőúüűÁÉÍÓÖŐÚÜŰ'; // Elvárt magyar karakterek.
  // Ciklus a listán / tartományon.
  for (final r in s.runes) {
    // Unicode kódpont → egy karakter string.
    final ch = String.fromCharCode(r);
    // Feltételes elágazás.
    if (good.contains(ch)) score += 3; // Magyar ékezet: jó.
    // Feltételes elágazás.
    if (ch == 'Ã' || ch == 'Â') score -= 4; // Mojibake jel: rossz.
  // Blokk / osztály vége.
  }
  // Visszatérési érték a hívónak.
  return score; // Magasabb = jobb minőség.
// Blokk / osztály vége.
}
