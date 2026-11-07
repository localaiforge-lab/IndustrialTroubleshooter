# Add a Hungarian explanation comment above every non-empty, non-comment Dart line.
# Usage: python scripts/comment_dart_lines.py path/to/file.dart

from __future__ import annotations

import re
import sys
from pathlib import Path

HINTS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^import "), "Import: külső/csomag függőség betöltése."),
    (re.compile(r"^export "), "Export: publikus API továbbadása más fájloknak."),
    (re.compile(r"^library;?$"), "Library jelölő a Dart csomaghoz."),
    (re.compile(r"^class "), "Osztály definíció kezdete."),
    (re.compile(r"^enum "), "Enum (felsorolás) típus."),
    (re.compile(r"^abstract "), "Absztrakt típus / interfész jellegű osztály."),
    (re.compile(r"^@override"), "Felülírja a szülő/interfész metódusát."),
    (re.compile(r"^return "), "Visszatérési érték a hívónak."),
    (re.compile(r"^if \("), "Feltételes elágazás."),
    (re.compile(r"^} else"), "Az if hamis ága."),
    (re.compile(r"^else \{"), "Az if hamis ága."),
    (re.compile(r"^for \("), "Ciklus a listán / tartományon."),
    (re.compile(r"^while \("), "Amíg igaz, ismétel."),
    (re.compile(r"^try \{"), "Hibakezelés kezdete (try)."),
    (re.compile(r"^catch \("), "Hibaág – kivétel elkapása."),
    (re.compile(r"^finally \{"), "Mindig lefutó takarító blokk."),
    (re.compile(r"^throw "), "Kivétel dobása."),
    (re.compile(r"^await "), "Aszinkron művelet megvárása."),
    (re.compile(r"^final "), "Változó / mező: egyszer állítható érték."),
    (re.compile(r"^const "), "Fordítási idejű konstans."),
    (re.compile(r"^var "), "Lokális változó."),
    (re.compile(r"^static "), "Osztályszintű (példány nélküli) tag."),
    (re.compile(r"^Future<"), "Aszinkron függvény / Future típus."),
    (re.compile(r"^void "), "Nincs visszatérési érték."),
    (re.compile(r"^bool "), "Igaz/hamis mező vagy változó."),
    (re.compile(r"^String "), "Szöveges mező vagy változó."),
    (re.compile(r"^int "), "Egész szám."),
    (re.compile(r"^double "), "Lebegőpontos szám."),
    (re.compile(r"^Widget "), "UI widget építő metódus / típus."),
    (re.compile(r"^super\."), "Szülő osztály metódusának hívása."),
    (re.compile(r"^setState\("), "UI újrarajzolás kérése állapotváltozás után."),
    (re.compile(r"^Navigator\."), "Képernyőnavigáció."),
    (re.compile(r"^debugPrint\("), "Fejlesztői konzol kiírás."),
    (re.compile(r"^unawaited\("), "Fut a háttérben, nem várjuk meg."),
    (re.compile(r"^}$"), "Blokk / osztály vége."),
    (re.compile(r"^\{$"), "Blokk kezdete."),
]


def hint_for(line: str) -> str:
    s = line.strip()
    if not s:
        return ""
    for pat, msg in HINTS:
        if pat.search(s):
            return msg
    if s.startswith("}"):
        return "Blokk / szerkezet zárójele."
    if s.endswith(",") or s.endswith("(") or s.endswith("{"):
        return "Widget / hívás paraméterlista folytatása."
    if "=" in s and not s.startswith("//"):
        return "Értékadás / mezőkitöltés."
    if s.endswith(";"):
        return "Utasítás vége."
    return "Kódsor: részlet a fenti logikából."


def comment_file(path: Path) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        # Keep existing comments / blanks / doc comments as-is.
        if (
            not stripped
            or stripped.startswith("//")
            or stripped.startswith("///")
            or stripped.startswith("*")
            or stripped.startswith("/*")
            or stripped.startswith("*/")
        ):
            out.append(line)
            i += 1
            continue
        # Skip if previous emitted line is already our style comment for this.
        indent = line[: len(line) - len(line.lstrip(" "))]
        msg = hint_for(line)
        # Avoid double-commenting if previous non-empty was identical hint.
        if out and out[-1].strip() == f"// {msg}":
            out.append(line)
        else:
            out.append(f"{indent}// {msg}")
            out.append(line)
        i += 1
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"commented: {path}")


def main() -> None:
    roots = [Path("lib"), Path("test")]
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*.dart"):
            comment_file(path)


if __name__ == "__main__":
    main()
