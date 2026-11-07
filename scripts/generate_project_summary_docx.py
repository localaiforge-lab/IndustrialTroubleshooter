#!/usr/bin/env python3
"""Generate Hungarian project/tech summary DOCX."""

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs" / "Oktatasi_Offline_Chatbot_Osszefoglalo.docx"


def set_run_font(run, size=None, bold=False, color=None):
    run.font.name = "Calibri"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
    if size:
        run.font.size = Pt(size)
    run.bold = bold
    if color:
        run.font.color.rgb = color


def add_heading_hu(doc, text, level=1):
    p = doc.add_heading(text, level=level)
    size = 16 if level == 1 else 13 if level == 2 else 12
    color = RGBColor(0x1A, 0x3A, 0x5C) if level <= 2 else RGBColor(0x2C, 0x4A, 0x6E)
    for run in p.runs:
        set_run_font(run, size=size, bold=True, color=color)
    return p


def add_para(doc, text, bold=False):
    p = doc.add_paragraph()
    run = p.add_run(text)
    set_run_font(run, bold=bold)
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.line_spacing = 1.15
    return p


def add_bullets(doc, items):
    for item in items:
        p = doc.add_paragraph(style="List Bullet")
        run = p.add_run(item)
        set_run_font(run)
        p.paragraph_format.space_after = Pt(3)


def add_table(doc, headers, rows):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = ""
        set_run_font(cell.paragraphs[0].add_run(h), bold=True, size=10)
    for r_i, row in enumerate(rows):
        for c_i, val in enumerate(row):
            cell = table.rows[r_i + 1].cells[c_i]
            cell.text = ""
            set_run_font(cell.paragraphs[0].add_run(val), size=10)
    doc.add_paragraph()


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = Document()
    for section in doc.sections:
        section.top_margin = Cm(2.2)
        section.bottom_margin = Cm(2.2)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)

    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run_font(
        title.add_run("Oktatási Offline Chatbot"),
        size=22,
        bold=True,
        color=RGBColor(0x1A, 0x3A, 0x5C),
    )

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run_font(
        subtitle.add_run("Technikai és projektösszefoglaló"),
        size=14,
        color=RGBColor(0x44, 0x55, 0x66),
    )

    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run_font(
        meta.add_run(
            "Flutter · on-device LLM · RAG · Android\n"
            "Verzió: 1.0.0 · anyagindex: v11 · 2026"
        ),
        size=10,
        color=RGBColor(0x66, 0x66, 0x66),
    )
    doc.add_paragraph()

    add_heading_hu(doc, "1. Cél és áttekintés", 1)
    add_para(
        doc,
        "Az alkalmazás egy magyar nyelvű, oktatási célú chatbot, amely a készüléken "
        "futó nagy nyelvi modellel (LLM) és tananyag-alapú kereséssel (RAG) válaszol "
        "a tankönyvi kontextus alapján. A felhasználói felület magyar; a belső "
        "feldolgozás (keresés és generálás) angol nyelvű szövegeken történik, online "
        "Hu↔En fordítással összekötve.",
    )
    add_bullets(
        doc,
        [
            "Célközönség: magyar iskolai tananyag (OH tankönyvek) – fizika, matek, irodalom, magyar nyelv.",
            "Platform: elsősorban Android (minSdk 26, arm64-v8a, largeHeap) – telefon/tablet.",
            "Csomagnév / brand: „Oktatási Offline Chatbot” (hu.educational.educational_chatbot).",
            "„Offline” értelemben: az LLM-következtetés és a RAG a készüléken fut; a kérdés/válasz fordításához internet kell.",
        ],
    )

    add_heading_hu(doc, "2. Végfelhasználói adatfolyam", 1)
    add_para(doc, "Egy tipikus kérdés útja:")
    add_bullets(
        doc,
        [
            "A felhasználó magyarul kérdez a chat UI-ban.",
            "TranslationService: Hu→En (Google Translate online; rövid „Ki volt X?” sablonok megőrzik a neveket).",
            "RAG: angol kérdés + eredeti magyar lexicalQuery → hibrid keresés az angol tankönyv-chunkokon.",
            "LLM (Qwen2.5 MediaPipe): angol rendszerprompt + talált kontextus → angol válasz.",
            "TranslationService: En→Hu → magyar válasz a felületen.",
        ],
    )
    add_para(
        doc,
        "A rendszerprompt angolul kéri, hogy a modell csak a megadott tananyag-kontextusból "
        "válaszoljon, röviden (2–4 mondat).",
    )

    add_heading_hu(doc, "3. Architektúra", 1)
    add_para(
        doc,
        "Feature-alapú Flutter alkalmazás: bootstrap indítás, ServiceLocator DI, "
        "majd chat / RAG / LLM / fordítás rétegek.",
    )
    add_table(
        doc,
        ["Réteg", "Feladat", "Fő komponensek"],
        [
            ["Bootstrap / DI", "Modellek kibontása, indexelés, fordító", "bootstrap.dart, service_locator.dart"],
            ["Chat", "Fordítás → RAG → LLM → fordítás", "ChatServiceImpl, RagChatScreen"],
            ["Fordítás", "Online Hu↔En", "TranslationService (translator)"],
            ["RAG", "Chunk, embed, HNSW, hibrid retrieve", "RagServiceImpl, EmbeddingService, ObjectBox"],
            ["Tananyag", "Manifest szerinti indexelés", "MaterialIndexService"],
            ["LLM", "On-device generálás", "FlutterGemmaLlmService (MediaPipe)"],
            ["Modellek", "APK asset → documents", "ModelAssetService"],
            ["Konfig", "Futásidejű JSON", "assets/config/app_config.json"],
        ],
    )
    add_para(
        doc,
        "Indítási sorrend: ServiceLocator → LLM extract → embedding ONNX extract → "
        "embedding betöltés + tananyag index → fordító → fő alkalmazás.",
    )

    add_heading_hu(doc, "4. Használt technológiák", 1)

    add_heading_hu(doc, "4.1 Alkalmazásréteg", 2)
    add_table(
        doc,
        ["Technológia", "Szerep"],
        [
            ["Flutter / Dart (SDK ^3.9)", "Keresztplatform UI és üzleti logika"],
            ["flutter_riverpod", "ProviderScope (állapotkezelés héj)"],
            ["gpt_markdown", "Chat markdown megjelenítés"],
            ["shared_preferences", "Index verzió, embedding model ID"],
            ["path_provider, uuid, equatable", "Útvonalak, ID-k, értékobjektumok"],
        ],
    )

    add_heading_hu(doc, "4.2 On-device LLM", 2)
    add_table(
        doc,
        ["Technológia", "Szerep"],
        [
            ["flutter_gemma + flutter_gemma_mediapipe", "MediaPipe .task LLM motor"],
            ["Qwen2.5 1.5B Instruct (Q8 .task)", "Alapértelmezett modell (~1,6 GB)"],
            ["Qwen2.5 0.5B / Qwen3 0.6B", "Kisebb alternatívák a konfigban"],
            ["llama_cpp_dart (legacy)", "GGUF útvonal; MediaTeken problémás"],
        ],
    )
    add_para(
        doc,
        "Alapértelmezett beállítások: contextSize 1024, maxTokens 256, threads 2, "
        "gpuLayers 0 (CPU). MediaPipe GPU sok MediaTek eszközön crash-hajlamos, "
        "ezért CPU az ajánlott.",
    )

    add_heading_hu(doc, "4.3 RAG: embedding és vektortár", 2)
    add_table(
        doc,
        ["Technológia", "Szerep"],
        [
            ["DistilUSE multilingual (ONNX)", "Mondat-embedding, 512 dimenzió"],
            ["flutter_onnxruntime + onnxruntime-android", "ONNX futás Androidon"],
            ["ObjectBox + HNSW", "Helyi vektortár és közelítő keresés"],
            ["ChunkingService", "~256 token cél, 32 overlap"],
        ],
    )
    add_para(
        doc,
        "Hibrid keresés: (1) DistilUSE → HNSW vektor ANN; (2) lexikális teljes szöveges "
        "scan (angol + magyar kifejezések, ékezet-fold); (3) score-ok összevonása; "
        "(4) focus excerpt a találatok körül a kontextusablakba. topK=4, maxContextChars≈1400.",
    )

    add_heading_hu(doc, "4.4 Fordítás", 2)
    add_bullets(
        doc,
        [
            "translator csomag → Google Translate API (online).",
            "Névvédő sablonok (pl. „Ki volt Koppány?” → „Who was Koppány?”).",
            "Hiányzó tulajdonnevek visszainjektálása a fordítás után.",
        ],
    )

    add_heading_hu(doc, "4.5 Tananyag-előkészítés (PC)", 2)
    add_table(
        doc,
        ["Eszköz", "Szerep"],
        [
            ["scripts/extract_pdf_materials.py (pymupdf)", "PDF → magyar .txt"],
            ["syncfusion_flutter_pdf", "Eszközön PDF szöveg (ha bundolt)"],
            ["scripts/translate_materials_to_en.py (Argos)", "HU → EN offline fordítás"],
            ["materials_manifest.json (v11)", "Indexelt fájlok listája + verzió"],
        ],
    )
    add_para(
        doc,
        "Az APK-ba csak a *_en.txt fájlok és a manifest kerül; a nagy PDF-ek szándékosan kimaradnak.",
    )

    add_heading_hu(doc, "5. Indexelt tananyagok (v11)", 1)
    add_table(
        doc,
        ["Fájl", "Tárgy"],
        [
            ["OH-FIZ78TB__teljes_en.txt", "Physics 7–8"],
            ["OH-MAT08TB__teljes_en.txt", "Mathematics 8"],
            ["OH-MIR05TB__teljes_en.txt", "Literature 5"],
            ["OH-MIR08TB__teljes_en.txt", "Literature 8"],
            ["OH-MNY05TB__teljes_en.txt", "Hungarian Language 5"],
            ["OH-MNY06TB__teljes_en.txt", "Hungarian Language 6"],
        ],
    )
    add_para(
        doc,
        "Manifest verzióváltáskor az ObjectBox index törlődik és újraépül "
        "(első indítás hosszabb lehet).",
    )

    add_heading_hu(doc, "6. Miért angol belső pipeline?", 1)
    add_para(
        doc,
        "A kis (1.5B) Qwen modell magyarul gyengébben teljesített. A korábbi angol "
        "tananyag + angol keresés stabilabb találatokat és válaszokat adott. Ezért a "
        "használható magyar TXT-eket angolra fordítottuk (Argos), a keresési beállításokat "
        "pedig visszacsináltuk az angol-kori hibrid scoringra. A UI továbbra is magyar "
        "marad az online fordítón keresztül.",
    )

    add_heading_hu(doc, "7. Korlátok és ismert tényezők", 1)
    add_bullets(
        doc,
        [
            "Kis LLM: korlátozott érvelés; rövid válaszok; maxTokens 256.",
            "Chat nem teljesen offline: Hu↔En fordításhoz internet kell.",
            "Az Argos-fordítás minősége befolyásolja a RAG találatok pontosságát.",
            "Sérült / kép-alapú OH PDF-ekből nem mindig nyerhető szöveg (OCR nincs).",
            "APK méret: ~1,5 GB .task modell + embedding ONNX; első extract percekig tarthat.",
            "Csak arm64-v8a; R8 minify kikapcsolva (JNI/ONNX kompatibilitás).",
            "Többfordulós LLM history jelenleg üres a ChatServiceImpl-ben.",
            "Lexikális keresés O(n) az összes chunkon – kisebb korpuszra tervezve.",
        ],
    )

    add_heading_hu(doc, "8. Fontos fájlok", 1)
    add_table(
        doc,
        ["Útvonal", "Jelentőség"],
        [
            ["pubspec.yaml", "Függőségek és bundolt assetek"],
            ["assets/config/app_config.json", "LLM / RAG / path konfig"],
            ["assets/materials/materials_manifest.json", "Tananyaglista + verzió"],
            ["lib/bootstrap.dart", "Indítási pipeline"],
            ["lib/core/di/service_locator.dart", "DI / backend választás"],
            ["lib/features/chat/data/chat_service_impl.dart", "Q&A orkesztráció"],
            ["lib/features/rag/data/rag_service_impl.dart", "Hibrid RAG"],
            ["lib/features/llm/data/flutter_gemma_llm_service.dart", "MediaPipe LLM"],
            ["lib/features/translation/data/translation_service.dart", "Hu↔En"],
            ["scripts/extract_pdf_materials.py", "PDF→TXT"],
            ["scripts/translate_materials_to_en.py", "HU→EN (Argos)"],
        ],
    )

    add_heading_hu(doc, "9. Összefoglaló folyamat", 1)
    add_para(
        doc,
        "UI (HU) → Google Translate (Hu→En) → DistilUSE + ObjectBox HNSW + lexikális boost "
        "→ Qwen2.5 MediaPipe (.task) → Google Translate (En→Hu) → UI (HU)",
    )
    add_para(
        doc,
        "Előkészítés (PC): OH PDF → (pymupdf) HU TXT → (Argos) EN TXT → manifest v11 → "
        "APK asset → első futáskor ObjectBox index.",
    )

    footer = doc.add_paragraph()
    footer.paragraph_format.space_before = Pt(18)
    set_run_font(
        footer.add_run(
            "Ez a dokumentum a educational_chatbot kódbázis aktuális állapotáról készült "
            "(app_config.json és lib/features forrás alapján)."
        ),
        size=9,
        color=RGBColor(0x77, 0x77, 0x77),
    )

    doc.save(OUT)
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
