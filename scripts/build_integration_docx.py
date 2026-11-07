"""Build docs/Lumeei_AI_Mind_Integracio.docx for Flutter host integrators."""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "Lumeei_AI_Mind_Integracio.docx"


def set_run_font(run, size=11, bold=False, italic=False, code=False):
    run.bold = bold
    run.italic = italic
    run.font.size = Pt(size)
    if code:
        run.font.name = "Consolas"
        run._element.rPr.rFonts.set(qn("w:ascii"), "Consolas")
        run._element.rPr.rFonts.set(qn("w:hAnsi"), "Consolas")
        run.font.size = Pt(9)


def add_para(doc, text, *, bold=False, size=11, space_after=6, space_before=0):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.space_before = Pt(space_before)
    run = p.add_run(text)
    set_run_font(run, size=size, bold=bold)
    return p


def shade_paragraph(paragraph, hex_color="F5F5F7"):
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), hex_color)
    shd.set(qn("w:val"), "clear")
    paragraph._p.get_or_add_pPr().append(shd)


def add_code_block(doc, text: str):
    lines = text.splitlines() or [""]
    for i, line in enumerate(lines):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0 if i else 4)
        p.paragraph_format.space_after = Pt(0 if i < len(lines) - 1 else 8)
        p.paragraph_format.left_indent = Cm(0.3)
        run = p.add_run(line if line else " ")
        set_run_font(run, code=True)
        shade_paragraph(p)


def add_table(doc, headers, rows):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = ""
        run = cell.paragraphs[0].add_run(h)
        set_run_font(run, bold=True, size=10)
    for r_i, row in enumerate(rows):
        for c_i, val in enumerate(row):
            cell = table.rows[r_i + 1].cells[c_i]
            cell.text = ""
            run = cell.paragraphs[0].add_run(val)
            set_run_font(run, size=10)
    doc.add_paragraph()


def main() -> None:
    doc = Document()
    for section in doc.sections:
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin = Cm(2.2)
        section.right_margin = Cm(2.2)

    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    doc.add_heading("LUMEEI AI Mind", level=0)
    add_para(
        doc,
        "Bekötés meglévő Flutter alkalmazásba – lépésről lépésre",
        bold=True,
        size=14,
        space_after=4,
    )
    add_para(
        doc,
        "Célközönség: Flutter-t ismerő fejlesztő  ·  Csomag: educational_chatbot  ·  "
        "Verzió: app 2.0.0 · 2026",
        size=10,
        space_after=12,
    )
    add_para(
        doc,
        "A host appból egy gombbal vagy route-tal megnyílik a LUMEEI tananyag-chat. "
        "A host feladata: függőség + assetek + initialize + chat megnyitás. "
        "A válaszokat a Cloud Run adja; a Hu↔En fordítás a telefonon fut (internet kell).",
        space_after=10,
    )

    doc.add_heading("Publikus API (egy import)", level=1)
    add_code_block(
        doc,
        "import 'package:educational_chatbot/lumeei_ai_mind.dart';\n"
        "\n"
        "await LumeeiAiMind.initialize(onProgress: ...);\n"
        "LumeeiAiMind.openChat(context);\n"
        "// vagy: LumeeiAiMind.chatScreen(showBackButton: true)",
    )

    doc.add_heading("Előfeltételek", level=1)
    for item in [
        "Flutter SDK kompatibilis a csomaggal (sdk: ^3.9.2 a csomag pubspec.yaml-jában).",
        "A Cloud Run szolgáltatás elérhető (prod URL az app_config.json-ban, vagy saját URL).",
        "A host appnak van internetes hozzáférése (Android INTERNET permission).",
        "A chatbot forráskód elérhető path dependency-ként (vagy később git/path szerint).",
    ]:
        doc.add_paragraph(item, style="List Number")

    add_para(doc, "Jelenlegi alapértelmezett szerver:", space_before=8, space_after=2)
    add_code_block(
        doc, "https://lumeei-ai-mind-270606217294.europe-west1.run.app"
    )

    doc.add_heading("1. lépés – Csomag hozzáadása", level=1)
    add_para(doc, "A legegyszerűbb mód: path dependency a host pubspec.yaml-ban:")
    add_code_block(
        doc,
        "dependencies:\n"
        "  flutter:\n"
        "    sdk: flutter\n"
        "  educational_chatbot:\n"
        "    path: ../educational_chatbot   # igazítsd a saját útvonalhoz",
    )
    add_para(doc, "Majd futtasd:")
    add_code_block(doc, "flutter pub get")
    add_para(
        doc,
        "A csomag függőségei (http, translator, flutter_tts, shared_preferences, stb.) "
        "automatikusan feloldódnak.",
    )

    doc.add_heading("2. lépés – Assetek a host appban", level=1)
    add_para(
        doc,
        "A csomag kódja gyökér asset útvonalakat tölt (assets/config/..., assets/branding/...), "
        "nem packages/educational_chatbot/... formát. Ezért a host projektben is legyenek "
        "ezek a fájlok, és a host pubspec.yaml deklarálja őket.",
    )

    doc.add_heading("2.1 Másold át a fájlokat", level=2)
    add_table(
        doc,
        ["Forrás (chatbot)", "Cél (host)"],
        [
            ["assets/config/app_config.json", "assets/config/app_config.json"],
            ["assets/branding/ (pl. LUMEEiAi.png)", "assets/branding/"],
        ],
    )

    doc.add_heading("2.2 Host pubspec.yaml – assets", level=2)
    add_code_block(
        doc,
        "flutter:\n"
        "  uses-material-design: true\n"
        "  assets:\n"
        "    - assets/config/\n"
        "    - assets/branding/",
    )

    doc.add_heading("2.3 Szerver URL (cloudBaseUrl)", level=2)
    add_para(doc, "Szerkeszd a host assets/config/app_config.json fájlját:")
    add_code_block(
        doc,
        '{\n'
        '  "cloudBaseUrl": "https://lumeei-ai-mind-270606217294.europe-west1.run.app"\n'
        "}",
    )
    add_para(
        doc,
        "Helyi demóhoz (LAN): http://192.168.x.x:8080 – fizikai telefonon ne 127.0.0.1-et használj.",
    )
    add_para(
        doc,
        "Ellenőrzés: GET {cloudBaseUrl}/health → ok, ragReady, llmReady legyen true.",
    )

    doc.add_heading("3. lépés – Android jogosultság", level=1)
    add_para(doc, "A host android/app/src/main/AndroidManifest.xml fájlban:")
    add_code_block(
        doc, '<uses-permission android:name="android.permission.INTERNET"/>'
    )
    add_para(
        doc,
        "iOS: HTTPS Cloud Run URL-lel nincs külön teendő; HTTP LAN demóhoz ATS kivétel kellhet.",
    )

    doc.add_heading("4. lépés – Inicializálás", level=1)
    add_para(
        doc,
        "LumeeiAiMind.initialize() betölti a konfigot, előkészíti a fordítót, és pingeli "
        "a Cloud Run /health végpontot. Ha a szerver nem elérhető vagy llmReady false, "
        "kivételt dob – kezeld a UI-ban.",
    )

    doc.add_heading("Eager init (splash / indítás)", level=2)
    add_code_block(
        doc,
        "await LumeeiAiMind.initialize(\n"
        "  onProgress: (status, progress) {\n"
        "    // opcionális: státusz + LinearProgressIndicator\n"
        "  },\n"
        ");",
    )

    doc.add_heading("Lazy init (első chat nyitás előtt)", level=2)
    add_code_block(
        doc,
        "Future<void> openAiMind(BuildContext context) async {\n"
        "  if (!LumeeiAiMind.isInitialized) {\n"
        "    showDialog<void>(\n"
        "      context: context,\n"
        "      barrierDismissible: false,\n"
        "      builder: (_) => const Center(child: CircularProgressIndicator()),\n"
        "    );\n"
        "    try {\n"
        "      await LumeeiAiMind.initialize();\n"
        "    } finally {\n"
        "      if (context.mounted) Navigator.of(context).pop();\n"
        "    }\n"
        "  }\n"
        "  if (!context.mounted) return;\n"
        "  await LumeeiAiMind.openChat(context);\n"
        "}",
    )
    add_para(
        doc,
        "initialize előtt legyen WidgetsFlutterBinding.ensureInitialized() (általában a main-ben).",
    )

    doc.add_heading("5. lépés – Chat megnyitása", level=1)

    doc.add_heading("A) Navigátor push", level=2)
    add_code_block(
        doc,
        "await LumeeiAiMind.openChat(context);\n"
        "await LumeeiAiMind.openChat(context, showBackButton: true);",
    )

    doc.add_heading("B) go_router / AutoRoute", level=2)
    add_code_block(
        doc,
        "GoRoute(\n"
        "  path: '/ai-mind',\n"
        "  builder: (context, state) => LumeeiAiMind.chatScreen(showBackButton: true),\n"
        "),",
    )
    add_para(doc, "A route elérése előtt: LumeeiAiMind.isInitialized == true.")

    doc.add_heading("C) Beágyazott képernyő (tab)", level=2)
    add_code_block(
        doc,
        "Scaffold(\n"
        "  body: LumeeiAiMind.chatScreen(showBackButton: false),\n"
        ")",
    )

    doc.add_heading("6. lépés – UI illesztés (opcionális)", level=1)
    for item in [
        "Téma: LumeeiAiMind.theme – sötét LUMEEI kinézet; a host MaterialApp témáját nem kötelező átírni.",
        "Gomb: FAB, menüpont, drawer – bármi, ami openChat-et hív.",
        "Riverpod: a openChat / chatScreen útvonalhoz a hostnak nem kell ProviderScope.",
    ]:
        doc.add_paragraph(item, style="List Bullet")

    doc.add_heading("7. lépés – Teljes minimál példa (FAB)", level=1)
    add_code_block(
        doc,
        "import 'package:educational_chatbot/lumeei_ai_mind.dart';\n"
        "import 'package:flutter/material.dart';\n"
        "\n"
        "class HostHome extends StatelessWidget {\n"
        "  const HostHome({super.key});\n"
        "\n"
        "  Future<void> _openChat(BuildContext context) async {\n"
        "    try {\n"
        "      if (!LumeeiAiMind.isInitialized) {\n"
        "        await LumeeiAiMind.initialize();\n"
        "      }\n"
        "      if (!context.mounted) return;\n"
        "      await LumeeiAiMind.openChat(context);\n"
        "    } catch (e) {\n"
        "      if (!context.mounted) return;\n"
        "      ScaffoldMessenger.of(context).showSnackBar(\n"
        "        SnackBar(content: Text('Chatbot nem elérhető: $e')),\n"
        "      );\n"
        "    }\n"
        "  }\n"
        "\n"
        "  @override\n"
        "  Widget build(BuildContext context) {\n"
        "    return Scaffold(\n"
        "      appBar: AppBar(title: const Text('Host alkalmazás')),\n"
        "      body: const Center(child: Text('Saját tartalom')),\n"
        "      floatingActionButton: FloatingActionButton.extended(\n"
        "        onPressed: () => _openChat(context),\n"
        "        icon: const Icon(Icons.auto_awesome),\n"
        "        label: const Text('Tananyag chat'),\n"
        "      ),\n"
        "    );\n"
        "  }\n"
        "}",
    )
    add_para(
        doc,
        "További minták: examples/host_simple_main.dart, examples/host_complex_integration.dart",
    )

    doc.add_heading("8. lépés – Ellenőrzőlista", level=1)
    add_table(
        doc,
        ["#", "Ellenőrzés"],
        [
            ["1", "flutter pub get hibamentes"],
            ["2", "Hostban van assets/config/app_config.json helyes cloudBaseUrl-lel"],
            ["3", "Hostban van assets/branding/ (logo)"],
            ["4", "Host pubspec.yaml deklarálja a fenti asset mappákat"],
            ["5", "Android INTERNET permission"],
            ["6", "GET {cloudBaseUrl}/health → llmReady: true"],
            ["7", "initialize() lefut (eager vagy lazy)"],
            ["8", "openChat / chatScreen megnyílik, magyar kérdésre válasz érkezik"],
            ["9", "Offline / rossz URL esetén érthető hibaüzenet a host UI-ban"],
        ],
    )

    doc.add_heading("9. Gyakori hibák", level=1)
    add_table(
        doc,
        ["Tünet", "Ok / megoldás"],
        [
            [
                "Unable to load asset: assets/config/...",
                "Nincs átmásolva / nincs a host pubspec assets listájában → pub get + hot restart",
            ],
            ["cloudBaseUrl hiányzik", "Üres vagy hibás JSON"],
            [
                "CloudUnavailableException",
                "Rossz URL, nincs net, Cloud Run down, vagy llmReady: false",
            ],
            ["127.0.0.1 telefonról", "LAN IP vagy Cloud Run HTTPS URL"],
            ["initialize kétszer", "Ártalmatlan – a DI idempotens"],
        ],
    )

    doc.add_heading("10. API rövid referencia", level=1)
    add_table(
        doc,
        ["Tag", "Szerep"],
        [
            ["initialize({onProgress})", "Konfig + fordító + health ping"],
            ["isInitialized", "bool – kész-e a DI"],
            ["openChat(context, {showBackButton})", "Push navigáció a chatre"],
            ["chatScreen({showBackButton})", "Widget route-hoz / embedhez"],
            ["theme", "Sötét ThemeData"],
            ["dispose()", "Erőforrások elengedése (teszt)"],
        ],
    )

    doc.add_heading("11. Architektúra (host szemszög)", level=1)
    add_code_block(
        doc,
        "[Host Flutter app]\n"
        "   │  LumeeiAiMind.initialize / openChat\n"
        "   ▼\n"
        "[educational_chatbot csomag]\n"
        "   │  Hu↔En fordítás (telefon) + HTTPS\n"
        "   ▼\n"
        "[Cloud Run: RAG + web search + Qwen GGUF]",
    )
    add_para(
        doc,
        "A host nem telepít MediaPipe-ot, ONNX-ot, GGUF-et vagy tananyag-indexet az APK-ba.",
    )

    doc.add_heading("12. Kapcsolódó dokumentumok", level=1)
    for item in [
        "README.md – projekt áttekintés",
        "docs/Oktatasi_Cloud_Chatbot_Osszefoglalo.md – technikai összefoglaló",
        "ToDeploy/README.md – szerver deploy",
        "docs/Lumeei_AI_Mind_Integracio.md – ugyanez Markdownban",
    ]:
        doc.add_paragraph(item, style="List Bullet")

    add_para(
        doc,
        "Összefoglalva: path dependency → assetek átmásolása + cloudBaseUrl → "
        "INTERNET → initialize → openChat / chatScreen.",
        bold=True,
        space_before=12,
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
