"""Plant library: many document shapes, one searchable factory store."""

from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path

os.environ.setdefault("PLANT_DIR", tempfile.mkdtemp(prefix="plant-api-"))

from fastapi.testclient import TestClient

from app.main import app
from app.plant_store import PlantStore


def _xlsx() -> bytes:
    from openpyxl import Workbook

    book = Workbook()
    sheet = book.active
    sheet.title = "Riasztasok"
    sheet.append(["Hibakód", "Tünet", "Teendő"])
    sheet.append(["E-204", "A védőrács nyitva", "Csukja be a rácsot, majd nyomja meg a nyugtázást"])
    sheet.append(["F-12", "Alacsony olajnyomás", "Ellenőrizze az olajszintet"])
    buf = io.BytesIO()
    book.save(buf)
    return buf.getvalue()


def _docx() -> bytes:
    from docx import Document

    document = Document()
    document.add_heading("Karbantartás", level=1)
    document.add_paragraph("A szíjat negyedévente kell cserélni, ha repedt.")
    table = document.add_table(rows=2, cols=2)
    table.rows[0].cells[0].text = "Hibakód"
    table.rows[0].cells[1].text = "Teendő"
    table.rows[1].cells[0].text = "A12"
    table.rows[1].cells[1].text = "Állítsa le a gépet és hűtse ki"
    buf = io.BytesIO()
    document.save(buf)
    return buf.getvalue()


def _text_pdf(text: str) -> bytes:
    raw = text.encode("latin-1", errors="replace")
    raw = raw.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")
    content = b"BT /F1 12 Tf 50 750 Td (" + raw + b") Tj ET"
    stream = b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream"
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        stream,
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{index} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode()
    out += (
        f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF"
    ).encode()
    return bytes(out)


def _blank_pdf() -> bytes:
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


class PlantLibraryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = PlantStore(Path(self.tmp.name))
        self.store.load()

    def tearDown(self):
        self.tmp.cleanup()

    def test_excel_fault_rows_stay_with_their_code(self):
        results = self.store.ingest_many([("hiba.xlsx", _xlsx())], area="Prés 2")
        self.assertEqual(results[0]["status"], "added")
        self.assertGreaterEqual(results[0]["faultCodeCount"], 2)
        answer = self.store.ask("Mit jelent az E-204?")
        self.assertTrue(answer["found"])
        self.assertIn("rácsot", answer["answer"])
        self.assertNotIn("olajszintet", answer["answer"])
        other = self.store.ask("F-12")
        self.assertIn("olajszintet", other["answer"])
        self.assertNotIn("rácsot", other["answer"])

    def test_word_heading_and_table(self):
        results = self.store.ingest_many([("karbantartas.docx", _docx())])
        self.assertEqual(results[0]["status"], "added")
        belt = self.store.ask("Mikor kell a szíjat cserélni?")
        self.assertIn("negyedévente", belt["answer"])
        self.assertIn("Karbantartás", belt["answer"])
        code = self.store.ask("A12")
        self.assertIn("hűtse", code["answer"])

    def test_hungarian_excel_csv_and_json_and_html(self):
        csv_bytes = "Hibakód;Tünet\nB30;Szivárgás a szelepnél\n".encode("cp1250")
        payload = json.dumps(
            [{"hibakod": "C-07", "teendo": "Cserélje a biztosítékot"}],
            ensure_ascii=False,
        ).encode("utf-8")
        html = "<h1>Kenés</h1><p>A csapágyat hetente zsírozza.</p>".encode("utf-8")
        results = self.store.ingest_many(
            [
                ("szelep.csv", csv_bytes),
                ("biztositek.json", payload),
                ("kenes.html", html),
            ]
        )
        self.assertTrue(all(item["status"] == "added" for item in results))
        self.assertIn("szelepnél", self.store.ask("Hol van szivárgás a szelepnél?")["answer"])
        self.assertIn("biztosítékot", self.store.ask("C-07")["answer"])
        grease = self.store.ask("Hogyan kell a csapágyat kenni?")
        self.assertIn("zsírozza", grease["answer"])
        self.assertIn("Kenés", grease["answer"])

    def test_pdf_text_blank_pdf_and_picture(self):
        text = self.store.ingest_many(
            [("orszag.pdf", _text_pdf("Fault code E-310 means the guard switch is open."))]
        )
        self.assertEqual(text[0]["status"], "added")
        self.assertIn("guard switch", self.store.ask("What does E-310 mean?")["answer"])
        blank = self.store.ingest_many([("scan.pdf", _blank_pdf())])
        self.assertEqual(blank[0]["status"], "rejected")
        self.assertIn("szkennelt", blank[0]["message"].casefold())
        picture = self.store.ingest_many([("foto.png", b"\x89PNG\r\nnot-a-real-image")])
        self.assertEqual(picture[0]["status"], "rejected")
        self.assertIn("képen", picture[0]["message"])

    def test_zip_folder_duplicate_and_reload(self):
        packed = io.BytesIO()
        with zipfile.ZipFile(packed, "w") as archive:
            archive.writestr("../jegyzet.txt", "Az F-88 kódnál ellenőrizze a szűrőt.\n")
            archive.writestr("foto.png", b"png")
        results = self.store.ingest_many([("csomag.zip", packed.getvalue())])
        names = {item["filename"]: item["status"] for item in results}
        self.assertEqual(names["jegyzet.txt"], "added")
        self.assertEqual(names["foto.png"], "rejected")
        self.assertIn("szűrőt", self.store.ask("F-88")["answer"])
        again = self.store.ingest_many(
            [("jegyzet.txt", "Az F-88 kódnál ellenőrizze a szűrőt.\n".encode("utf-8"))]
        )
        self.assertEqual(again[0]["status"], "duplicate")
        fresh = PlantStore(Path(self.tmp.name))
        fresh.load()
        self.assertEqual(len(fresh.list_documents()), 1)
        self.assertIn("szűrőt", fresh.ask("F-88")["answer"])

    def test_same_name_new_content_warns_and_unknown_code_misses(self):
        self.store.ingest_many([("naplo.txt", "A szivattyú indítása a főkapcsolóval történik.\n".encode())])
        second = self.store.ingest_many(
            [("naplo.txt", "A új napló a hőcserélő légtelenítését írja.\n".encode())]
        )
        self.assertEqual(second[0]["status"], "added")
        self.assertTrue(any("nevű" in note for note in second[0]["warnings"]))
        missed = self.store.ask("Z-999")
        self.assertFalse(missed["found"])
        self.assertIn("nincs ehhez", missed["answer"])

    def test_empty_library_message(self):
        answer = self.store.ask("Mi a teendő?")
        self.assertTrue(answer["libraryEmpty"])
        self.assertIn("Még nincs dokumentum", answer["answer"])


class PlantApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.client.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None, None, None)

    def test_console_and_upload_roundtrip(self):
        page = self.client.get("/plant/")
        self.assertEqual(page.status_code, 200)
        self.assertIn("Üzemi hibakereső", page.text)
        root = self.client.get("/", follow_redirects=False)
        self.assertEqual(root.status_code, 302)
        status = self.client.get("/v1/plant/status")
        self.assertEqual(status.status_code, 200)
        self.assertIn("documents", status.json())
        upload = self.client.post(
            "/v1/plant/documents",
            files={"files": ("pres.xlsx", _xlsx(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"area": "Prés 2"},
        )
        self.assertEqual(upload.status_code, 200, upload.text)
        self.assertEqual(upload.json()["results"][0]["status"], "added")
        asked = self.client.post("/v1/plant/ask", json={"question": "E-204 a présen"})
        self.assertEqual(asked.status_code, 200, asked.text)
        self.assertIn("rácsot", asked.json()["answer"])
        document_id = upload.json()["results"][0]["documentId"]
        removed = self.client.delete(f"/v1/plant/documents/{document_id}")
        self.assertEqual(removed.status_code, 200)


if __name__ == "__main__":
    unittest.main()
