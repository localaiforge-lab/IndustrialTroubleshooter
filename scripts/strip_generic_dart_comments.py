# Remove auto-generated generic comments that sit immediately above code
# when a richer human comment already exists, and collapse duplicate generics.
from pathlib import Path
import re

GENERIC = {
    "Import: külső/csomag függőség betöltése.",
    "Export: publikus API továbbadása más fájloknak.",
    "Library jelölő a Dart csomaghoz.",
    "Osztály definíció kezdete.",
    "Enum (felsorolás) típus.",
    "Absztrakt típus / interfész jellegű osztály.",
    "Felülírja a szülő/interfész metódusát.",
    "Visszatérési érték a hívónak.",
    "Feltételes elágazás.",
    "Az if hamis ága.",
    "Ciklus a listán / tartományon.",
    "Amíg igaz, ismétel.",
    "Hibakezelés kezdete (try).",
    "Hibaág – kivétel elkapása.",
    "Mindig lefutó takarító blokk.",
    "Kivétel dobása.",
    "Aszinkron művelet megvárása.",
    "Változó / mező: egyszer állítható érték.",
    "Fordítási idejű konstans.",
    "Lokális változó.",
    "Osztályszintű (példány nélküli) tag.",
    "Aszinkron függvény / Future típus.",
    "Nincs visszatérési érték.",
    "Igaz/hamis mező vagy változó.",
    "Szöveges mező vagy változó.",
    "Egész szám.",
    "Lebegőpontos szám.",
    "UI widget építő metódus / típus.",
    "Szülő osztály metódusának hívása.",
    "UI újrarajzolás kérése állapotváltozás után.",
    "Képernyőnavigáció.",
    "Fejlesztői konzol kiírás.",
    "Fut a háttérben, nem várjuk meg.",
    "Blokk / osztály vége.",
    "Blokk kezdete.",
    "Blokk / szerkezet zárójele.",
    "Widget / hívás paraméterlista folytatása.",
    "Értékadás / mezőkitöltés.",
    "Utasítás vége.",
    "Kódsor: részlet a fenti logikából.",
}

# Files that already had rich hand-written comments – strip ONLY pure generic
# lines that duplicate coverage (keep one comment layer).
HAND = {
    "lib/main.dart",
    "lib/app.dart",
    "lib/lumeei_ai_mind.dart",
    "lib/bootstrap.dart",
    "lib/core/config/app_config.dart",
    "lib/core/di/service_locator.dart",
    "lib/core/platform/tts_install_platform.dart",
    "lib/core/utils/diagnostic_log.dart",
    "lib/core/utils/text_encoding_fix.dart",
    "lib/features/chat/domain/chat_service.dart",
    "lib/features/chat/domain/entities/chat_message.dart",
    "lib/features/chat/presentation/lumeei_ai_mind.dart",
    "lib/features/chat/presentation/theme/lumeei_theme.dart",
    "lib/features/chat/presentation/screens/home_screen.dart",
    "lib/features/translation/data/translation_service.dart",
    "lib/integration/lumeei_ai_mind.dart",
}


def strip_generics(path: Path) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        st = line.strip()
        if st.startswith("// ") and st[3:] in GENERIC:
            # Look ahead: if next non-empty is code, drop this generic
            # only when previous line was already a non-generic comment/doc.
            prev = out[-1].strip() if out else ""
            if prev.startswith("//") or prev.startswith("///") or prev.startswith("*"):
                i += 1
                continue
        out.append(line)
        i += 1
    # Collapse consecutive identical comments.
    cleaned: list[str] = []
    for line in out:
        if cleaned and cleaned[-1] == line and line.strip().startswith("//"):
            continue
        cleaned.append(line)
    path.write_text("\n".join(cleaned) + "\n", encoding="utf-8")
    print("cleaned", path)


for rel in HAND:
    p = Path(rel)
    if p.exists():
        strip_generics(p)
