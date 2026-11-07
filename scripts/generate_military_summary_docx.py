#!/usr/bin/env python3
"""Hadiipari gyártási asszisztens: cél, MVP és termékvízió (DOCX)."""

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs" / "Hadiipari_Gyartasi_Asszisztens_Osszefoglalo.docx"


def set_run_font(run, size=None, bold=False, italic=False, color=None):
    run.font.name = "Calibri"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
    if size:
        run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if color:
        run.font.color.rgb = color


def add_heading_hu(doc, text, level=1):
    p = doc.add_heading(text, level=level)
    size = 16 if level == 1 else 13 if level == 2 else 12
    color = RGBColor(0x1A, 0x3A, 0x5C) if level <= 2 else RGBColor(0x2C, 0x4A, 0x6E)
    for run in p.runs:
        set_run_font(run, size=size, bold=True, color=color)
    return p


def add_para(doc, text, bold=False, italic=False):
    p = doc.add_paragraph()
    run = p.add_run(text)
    set_run_font(run, bold=bold, italic=italic)
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

    core = doc.core_properties
    core.title = "Hadiipari gyártási asszisztens — cél, MVP és termékvízió"
    core.subject = "LUMEEI AI Mind hadiipari termékvonal"
    core.category = "Termékvízió"
    core.language = "hu-HU"

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run_font(
        title.add_run("Hadiipari gyártási asszisztens"),
        size=22,
        bold=True,
        color=RGBColor(0x1A, 0x3A, 0x5C),
    )

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run_font(
        subtitle.add_run("Cél, MVP és termékvízió"),
        size=14,
        color=RGBColor(0x44, 0x55, 0x66),
    )

    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run_font(
        meta.add_run(
            "LUMEEI AI Mind termékvonal\n"
            "Helyi hálózat · dokumentáció-alapú válaszadás · hibakód és OCR\n"
            "2026. október"
        ),
        size=10,
        color=RGBColor(0x66, 0x66, 0x66),
    )
    doc.add_paragraph()

    add_heading_hu(doc, "1. Miről szól ez a dokumentum", 1)
    add_para(
        doc,
        "Ez az összefoglaló a LUMEEI AI Mind tananyagos chatbotjából kinövő hadiipari "
        "termékvonalat írja le. A tananyagos rendszer ma felhőben fut, és iskolai "
        "anyagra válaszol. A hadiipari változat ugyanarra a kereső és válaszadó "
        "vázra épül, de a tudásforrás a gyár saját jóváhagyott dokumentációja, "
        "a futás helye pedig a telephely helyi hálózata.",
    )
    add_para(
        doc,
        "A dokumentum három kérdést válaszol meg: mi a cél, mi fér bele az első "
        "használható változatba (MVP), és milyen termékké érdemes ezt kinöveszteni, "
        "hogy hadiipari gyártásban valódi értéket hordozzon.",
    )

    add_heading_hu(doc, "2. Cél", 1)
    add_para(
        doc,
        "A cél egy olyan üzemi asszisztens, amely a gyártósor mellett, a gyár saját "
        "gépkönyveiből, hibakatalógusaiból és jóváhagyott utasításaiból válaszol "
        "a műszak kérdéseire. A kezelő begépeli a hibakódot, vagy lefényképezi a "
        "kijelzőt, és másodpercek alatt megkapja a dokumentumban szereplő jelentést "
        "és a hozzá tartozó eljárás helyét, oldalszámmal és fejezetszámmal.",
    )
    add_para(doc, "A cél közönsége a hadiipari gyártás műszaka:", bold=True)
    add_bullets(
        doc,
        [
            "Gépkezelő, aki állás közben a kijelző hibakódját akarja megfejteni.",
            "Karbantartó, aki a vonatkozó gépkönyvi fejezetet és a jóváhagyott teendőt keresi.",
            "Műszakvezető, aki azt akarja látni, hogy a válasz melyik érvényes dokumentumváltozatból jött.",
            "Minőség- és megfelelőségi szerep, aki utólag visszanézheti, milyen forrás alapján született a javasolt lépés.",
        ],
    )
    add_para(
        doc,
        "A termék ígérete egy mondatban: a jóváhagyott eljárás a műszak kezében van "
        "akkor is, amikor a tapasztalt szakember másik műszakban van, és eközben a "
        "dokumentum, a kérdés és a válasz a telephelyen marad.",
    )

    add_heading_hu(doc, "3. Kiindulópont", 1)
    add_para(
        doc,
        "A meglévő LUMEEI AI Mind (alkalmazás 2.0.0, API 2.1.0) vékony Flutter kliens "
        "és Google Cloud Run szerver. A telefon a felületet viszi. A szerveren fut a "
        "DistilUSE embedding, a tananyagkeresés, a webes kiegészítő keresés és a "
        "Qwen2.5 GGUF válaszgenerálás. A magyar–angol fordítás a telefonon, online "
        "fordítóval történik.",
    )
    add_para(
        doc,
        "Ez a váz bizonyítja, hogy a kérdés útja működik: szöveg be, releváns részlet "
        "ki, rövid válasz forrásszövegből. A hadiipari termék ezt a vázat három "
        "helyen cseréli le. A tananyag helyére a gyár dokumentumai kerülnek. A felhő "
        "helyére egy helyi gép kerül, kimenő internet nélkül. A webes keresés és a "
        "külső fordító helyére olyan út kerül, amely a kerítésen belül marad.",
    )
    add_table(
        doc,
        ["", "Tananyagos rendszer ma", "Hadiipari termék"],
        [
            ["Tudás", "Iskolai tananyag", "A gyár betöltött gépkönyve, hibakatalógusa, utasításai"],
            ["Futás helye", "Google Cloud Run", "Szerver a gyári hálózaton"],
            ["Adat útja", "Kérdés kimegy a felhőbe és a fordítóba", "Kérdés, kép és válasz a telephelyen marad"],
            ["Gyenge találat", "Webes keresés egészíti ki", "A rendszer jelzi, hogy a dokumentumban nincs meg"],
            ["Bejárat", "Szabad kérdés", "Szabad kérdés, begépelt hibakód, kijelzőfotó"],
            ["Válasz", "Rövid tananyagi válasz", "Idézett bekezdés, dokumentum, fejezet, oldal"],
        ],
    )

    add_heading_hu(doc, "4. Miért lehet belőle értékes hadiipari termék", 1)
    add_para(
        doc,
        "Hadiipari gyártásban a tudás megvan, csak nem akkor érhető el, amikor a sor "
        "áll. Az eljárás vastag PDF-ben, gépkönyvben vagy nyomtatott dossziéban van. "
        "Aki fejből tudja, nincs mindig a gépen. A felhős általános chatbot ide nem "
        "vihető be: a gépkönyv, a hibakatalógus és a gyártási utasítás ellenőrzött "
        "műszaki adat, üzemi titok, sokszor szabályozott technikai információ.",
    )
    add_para(doc, "Az érték ott jelenik meg, ahol a műszak ma időt és kockázatot veszít:")
    add_bullets(
        doc,
        [
            "Állásidő. A kódtól a helyes fejezetig percek vagy egy másik műszak telik el. A termék ezt a keresést viszi le másodpercekre.",
            "Szórt gyakorlat. Két műszak kétféleképpen emlékszik ugyanarra a hibára. A termék mindenkit ugyanahhoz a jóváhagyott bekezdéshez visz.",
            "Selejt és újramunka. A találgatott lépés drágább, mint a dokumentált lépés. A válasz csak akkor lépés, ha a dokumentum tartalmazza.",
            "Audit. Utólag meg kell tudni mondani, melyik dokumentumváltozat alapján született a döntés. A válasz mellé ezért verzió, fejezet és oldal jár.",
            "Bevezethetőség. A termék ott adható el, ahova a felhős MI nem léphet be. A zártság a funkció része, nem utólagos korlát.",
        ],
    )
    add_para(
        doc,
        "Az általános chatbotok hadiipari gyárban nehezen válnak gyártási eszközzé, "
        "mert kitalálhatnak lépést, és mert a kérdés elhagyja a telepet. Ez a termék "
        "akkor értékes, ha egyiket sem teszi. Forrásolt, zárt, hibakódra épülő üzemi "
        "eszköz, amelyet a műszak a gép mellett használ.",
    )

    add_heading_hu(doc, "5. Működési alapelv", 1)
    add_para(
        doc,
        "A hadiipari termékben a válasz a telephelyen betöltött, jóváhagyott "
        "dokumentumokból születik. A modell a keresés által kiemelt bekezdéseket "
        "fogalmazza rövid, hivatkozott válasszá. A tartalom tulajdonosa a gyár és a "
        "dokumentum kibocsátója. A végrehajtás felelőse a műszak és az eljárás gazdája marad.",
    )
    add_bullets(
        doc,
        [
            "Válasz csak betöltött dokumentumból születik: gépkönyv, hibakatalógus, karbantartási utasítás, gyártási vagy vizsgálati utasítás, jóváhagyott módosítási lap.",
            "Minden válasz megnevezi a dokumentumot, a változatot, a fejezetet és az oldalt.",
            "Ha a kérdésre a korpuszban nincs támpont, a rendszer ezt mondja ki. Kiegészítő lépést a modell emlékezetéből nem ír.",
            "A webes keresés ebben a termékben nincs bekötve.",
            "A fordítás, a karakterfelismerés és a válaszgenerálás a helyi gépen fut.",
            "A kezelő azt a dokumentumkört látja, ami a saját sorához és a saját szerepéhez tartozik.",
        ],
    )
    add_para(doc, "Két bejárat ugyanahhoz a tudáshoz vezet.", bold=True)
    add_para(
        doc,
        "Szabad kérdés. A kezelő természetes mondattal kérdez, például hogy egy adott "
        "leállásnál melyik fejezet érvényes. A rendszer jelentés alapján keres a "
        "bekezdések között, és a legjobban illeszkedő részekből fogalmaz rövid választ, "
        "idézettel.",
    )
    add_para(
        doc,
        "Hibakód. A kód először a katalógusban keres pontos egyezést. A katalógussor "
        "mellé a kapcsolódó eljárási bekezdés kerül. A fénykép ugyanezt az utat járja: "
        "a helyi karakterfelismerő kiolvassa a kijelző szövegét, a kódot normalizálja "
        "(hasonló karakterek, kötőjel, szóköz), majd a begépelt kóddal azonos katalógust "
        "nyitja meg. A kép a telephelyen marad.",
    )

    add_heading_hu(doc, "6. Az MVP", 1)
    add_para(
        doc,
        "Az MVP egy telephely, egy gyártósor vagy egy gépcsalád dokumentumkészletén "
        "bizonyítja, hogy a műszak a helyi hálózaton megbízható választ kap. Még nem "
        "gyártelepi platform. Az első telepítés annyit tud, amennyi egy valós műszak "
        "egy valós gépe mellett már hasznos.",
    )

    add_heading_hu(doc, "6.1 Amit az első változat tud", 2)
    add_bullets(
        doc,
        [
            "Helyi szerver a gyári hálózaton. A gépnek nincs útvonala az internet felé. A modell, az embedding és a dokumentumok előre, offline csomagban kerülnek fel.",
            "Dokumentumok betöltése a telephelyen: PDF gépkönyv és strukturált hibakatalógus. A bekezdések helye (dokumentum, fejezet, oldal) megmarad.",
            "Magyar kérdés és magyar válasz a munkaállomás böngészőjében, belső címen. A meglévő vékony kliens később ugyanerre a belső címre állítható.",
            "Szabad kérdés: jelentés alapú keresés, rövid válasz, forrásblokkal.",
            "Begépelt hibakód: pontos találat a katalógusban, mellé a kapcsolódó eljárási rész.",
            "Kijelzőfotó: a kép feltöltése a belső API-ra, helyi karakterfelismerés, a kiolvasott kód ugyanabba a katalógusba megy. Az MVP jól olvasható kijelzőszövegre készül.",
            "Üres találat őszinte: a rendszer kiírja, hogy a betöltött anyagban nincs válasz, és nem pótol lépést.",
            "Egyszerű üzemi belépés, hogy a végpont a műhelyben se legyen nyílt.",
            "Helyi napló: ki, mikor, melyik dokumentumváltozatból kapott választ. A napló a telepen marad.",
        ],
    )

    add_heading_hu(doc, "6.2 Amit az MVP-ben a válasz mindig tartalmaz", 2)
    add_table(
        doc,
        ["Mező", "Miért kell a műszaknak"],
        [
            ["Rövid válasz magyarul", "A gép mellett olvasható, nem egy fejezet másolata"],
            ["Idézett bekezdés", "Látszik, hogy a mondat a dokumentumból van"],
            ["Dokumentum neve és változata", "Egyértelmű, melyik jóváhagyott kiadás érvényes"],
            ["Fejezet és oldal", "A papír vagy a PDF ugyanott kinyitható"],
            ["Hibakód és katalógussor", "A kód és a jelentés egy helyen ellenőrizhető"],
            ["„Nincs a dokumentumban” jelzés", "A modell emlékezete nem válik eljárássá"],
        ],
    )

    add_heading_hu(doc, "6.3 Technikai keret az MVP-hez", 2)
    add_para(
        doc,
        "Az MVP a meglévő ToDeploy szervercsomag helyi profilja. A webes keresés és "
        "minden külső fordító ebben a profilban nincs betöltve. A hibakód külön, "
        "pontos index. A szabad kérdés a meglévő embeddinges keresés. A fénykép útja "
        "a karakterfelismerés után ugyanabba a hibakód-indexbe köt.",
    )
    add_para(
        doc,
        "A tananyagos 1,5 milliárd paraméteres modell rövid iskolai válaszra készült. "
        "Gyártási szöveghez az MVP nagyobb, helyben futó modellt használ, hogy a "
        "magyar műszaki mondat és a hosszabb eljárási bekezdés vállalható legyen. "
        "A modell a helyi gépen fut, GPU-s üzemi szerveren.",
    )
    add_table(
        doc,
        ["Réteg", "MVP-beli választás"],
        [
            ["Kliens", "Böngésző a műhelyi gépen; a Flutter kliens belső URL-je a következő kör"],
            ["API", "Egészség, dokumentumlista, kérdés, hibakód, képből kiolvasott kód"],
            ["Keresés", "Pontos hibakód-index és bekezdésekre bontott jelentéskeresés"],
            ["Karakterfelismerés", "Helyi motor, felhős képfelismerő nélkül"],
            ["Válaszadás", "Helyi, nagyobb instruct modell, kötelező forrásmezőkkel"],
            ["Hálózat", "Csak a gyári címtartomány, belső tanúsítvány, nincs kimenő útvonal"],
        ],
    )

    add_heading_hu(doc, "7. Amit az első változat szándékosan még nem vállal", 1)
    add_para(
        doc,
        "Az MVP értéke a szűk és bizonyítható kör. Az alábbiak a vízió részei, az első "
        "telepítés feltételei közül kimaradnak.",
    )
    add_bullets(
        doc,
        [
            "Több telep, több sor és csoportszintű felügyelet.",
            "Teljes dokumentuméletciklus: jóváhagyás, hatályon kívül helyezés, automatikus csere a keresőben.",
            "Karbantartó rendszerbe írt munkalap és műszaknapló.",
            "Hangos kérdezés a zajos sor mellett.",
            "Olajos, kopott, döntött címkék megbízható olvasása. Az első OCR a tiszta kijelzőszöveg.",
            "A gyár minősítési, akkreditációs és exportellenőrzési eljárásának lefolytatása. Az MVP a műszaki zártságot adja; a telephelyi engedélyezés a gyár saját rendje szerint történik.",
            "Saját, gyárra finomhangolt nyelvi modell. Először a dokumentumkeresésnek kell pontosnak lennie.",
        ],
    )

    add_heading_hu(doc, "8. Vízió", 1)
    add_para(
        doc,
        "A vízió egy üzemi tudásréteg a hadiipari gyártó cégeknek. Amikor a gép megáll, "
        "a kezelő a kódot vagy a kérdést beadja, és a jóváhagyott eljárás vonatkozó "
        "bekezdését kapja vissza, azon a nyelven, amelyen a műszak dolgozik, annak a "
        "sornak a dokumentumaiból, amelyhez jogosultsága van. A válasz mellől "
        "visszakövethető a dokumentumváltozat. A telephely határán adat nem lép ki.",
    )
    add_para(
        doc,
        "Ebből akkor lesz a hadiiparban nehezen helyettesíthető termék, ha a chatablak "
        "helyett a sor megállásának eszköze lesz. A hibakód a bejárat. A forrás a "
        "bizalom. A zártság a beszerzés feltétele. A mérhető eredmény az állásidő, "
        "az egységes eljárás és az auditálható válasz.",
    )

    add_heading_hu(doc, "8.1 Amit a kész termék a gyárnak ad", 2)
    add_bullets(
        doc,
        [
            "Soronkénti tudáskör. Egy kezelő a saját gépeinek könyvét látja. A szomszéd sor anyaga a jogosultság nélkül meg sem jelenik a találatok között.",
            "Érvényes változat. Hatályon kívül helyezett utasítás kiesik a keresésből. A válasz mindig a hatályos kiadásra hivatkozik.",
            "Műszakváltás. Az előző műszak kérdései és a hozzájuk tartozó források a helyi naplóból átadhatók, szóbeszéd nélkül.",
            "Karbantartási kapcsolat. A megtalált eljárásból munkalap nyitható a gyár saját karbantartó rendszerében, a fejezet és az oldal már kitöltve.",
            "Telepítési csomag kerítésen belülre. Modell, embedding és üres dokumentumtár offline telepítőn érkezik. A gyár a saját anyagát tölti be. Frissítés ugyanígy, hálózat nélkül megy be.",
            "Több telephely ugyanazzal a termékkel, telepenként külön zárt géppel. Közös felhő, közös napló és közös dokumentumtár nincs.",
        ],
    )

    add_heading_hu(doc, "8.2 Amitől a vevő fizetni fog érte", 2)
    add_para(
        doc,
        "Hadiipari beszállítónál a beszerzés ritkán egy újabb chatfelületért indul. "
        "Azért indul, mert a felhős eszköz a megfelelőség miatt eleve kiesik, a papír "
        "pedig a sor mellett lassú. A termék ezt a rést tölti ki.",
    )
    add_table(
        doc,
        ["Vevői kényszer", "Amit a termék erre ad"],
        [
            ["A műszaki adat nem mehet ki a telepről", "Helyi gép, nincs kimenő kapcsolat, nincs külső fordító és nincs webes keresés"],
            ["A válaszért valakinek felelnie kell", "Idézet, változat, fejezet, oldal; a modell üres találatnál megáll"],
            ["A műszak nem egyforma tapasztalatú", "Ugyanaz a hatályos bekezdés minden műszaknak"],
            ["A hiba a kijelzőn jelenik meg, nem a chatben", "Begépelt kód és lefényképezett kijelző ugyanabba a katalógusba fut"],
            ["Az auditor dokumentumot kér, benyomást nem", "Napló: kérdés, idő, szerep, dokumentumváltozat"],
            ["Több sor, több telep, ugyanaz a cég", "Azonos termék, telepenként elszigetelt telepítés"],
        ],
    )
    add_para(
        doc,
        "A tananyagos LUMEEI AI Mind a technológiai alap és a referencia, hogy a "
        "keresés és a válaszadás már létezik. A hadiipari vonal külön termék: más "
        "tudás, más hálózat, más felelősség, más értékesítési mondat. Az árazás alapja "
        "a telepített sorok és a betöltött dokumentumkör, valamint a helyi üzemeltetés, "
        "nem a felhős tokencsere.",
    )

    add_heading_hu(doc, "9. Fejlesztési lépcsők", 1)
    add_table(
        doc,
        ["Lépcső", "Állapot", "Amit a gyár ebből érzékel"],
        [
            [
                "1. MVP",
                "Egy sor, egy dokumentumkör",
                "Kérdés, begépelt kód és tiszta kijelzőfotó helyi választ ad, forrással",
            ],
            [
                "2. Üzemi megbízhatóság",
                "Jogosultság, napló, OCR-minőség",
                "Minden szerep a saját anyagát látja; a kijelzőfotó a műszak valós képein is megáll",
            ],
            [
                "3. Dokumentumélet",
                "Hatály, verzió, csere",
                "A kereső mindig a jóváhagyott kiadást adja; a régi utasítás kikerül",
            ],
            [
                "4. Sor és karbantartás",
                "Több gépcsalád, munkalap",
                "A válaszból a gyár saját rendszerében nyílik a teendő, fejezettel kitöltve",
            ],
            [
                "5. Telephelyi termék",
                "Több zárt telepítés",
                "A cég minden gyárában ugyanaz az eszköz fut, adatot egymással sem osztanak",
            ],
        ],
    )
    add_para(
        doc,
        "A lépcsők sorrendje szándékos. Először a találatnak kell igaznak lennie egy "
        "gépen. Utána érdemes jogosultságot, verziót és más rendszereket ráépíteni. "
        "Egy látványos, de forrás nélkül fogalmazó asszisztens hadiipari gyártásban "
        "hamar kiesik a műszak bizalmából.",
    )

    add_heading_hu(doc, "10. Biztonság a termékígéretben", 1)
    add_para(
        doc,
        "A zártság a hadiipari változat fő tulajdonsága. Az alábbiak az MVP-től "
        "kezdve a termék részei.",
    )
    add_bullets(
        doc,
        [
            "A szerver csak a gyári címtartományt figyeli. Alapértelmezett útvonal az internet felé nincs.",
            "A kérdésszöveg, a hibakód és a kijelzőfotó a helyi API-n marad. Külső fordító, külső képfelismerő és külső kereső nincs a láncban.",
            "A kapcsolat a műhely és a szerver között belső tanúsítvánnyal védett.",
            "A belépés azonosított. A dokumentumkör szerephez és sorhoz kötött.",
            "A dokumentumtár és a napló a telephelyen, a gyár által kezelt gépen tárolódik.",
            "A modell és a program offline csomagban érkezik és ugyanígy frissül.",
            "A napló megmondja, melyik változatból született a válasz. A napló másolatát a termék kifelé nem küldi.",
        ],
    )
    add_para(
        doc,
        "A termék a gyár dokumentumrendjét követi. Azt a kört tölti be és azt a kört "
        "szolgálja ki, amelyet a telephely az adott gépre és szerepre jóváhagy. A "
        "minősített környezetbe helyezés, a hozzáférési szabály és az üzemeltetési "
        "engedély a gyár eljárása. A szoftver ehhez a zárt, naplózott, forrásolt "
        "működést adja.",
    )

    add_heading_hu(doc, "11. Az MVP sikerének feltétele", 1)
    add_para(
        doc,
        "Az első telepítés akkor kész, ha egy valós gépkönyvön és egy valós "
        "hibakatalóguson az alábbiak teljesülnek. A számok egy sor átvételi "
        "próbájához valók, marketingígéretnek nem.",
    )
    add_bullets(
        doc,
        [
            "A kijelölt gépkönyv és hibakatalógus a helyi gépen, a gyár hálózatán van betöltve.",
            "Húsz, a műszakkal előre egyeztetett kérdésből a válasz a helyes fejezetre és oldalra hivatkozik.",
            "A katalógus kijelölt kódjai begépelve a megfelelő sort hozzák, a kapcsolódó eljárással.",
            "Ugyanezek a kódok tiszta kijelzőfotóról kiolvasva ugyanahhoz a sorhoz érkeznek.",
            "Olyan kérdésre, amelynek nincs nyoma a betöltött anyagban, a rendszer dokumentált választ nem gyárt.",
            "A próba idején a szerverről kimenő kapcsolat nem indul: sem fordító, sem kereső, sem modellhívás.",
            "A műszakvezető a naplóból egy válaszhoz vissza tudja keresni a dokumentumváltozatot.",
        ],
    )

    add_heading_hu(doc, "12. Összefoglaló", 1)
    add_para(
        doc,
        "A cél egy helyi gyártási asszisztens hadiipari üzemeknek. A műszak a saját "
        "jóváhagyott dokumentumaiból kap választ, hibakóddal vagy kijelzőfotóval is, "
        "és a kérdés a telephelyen marad.",
    )
    add_para(
        doc,
        "Az MVP egy soron bizonyítja ezt: helyi szerver, egy dokumentumkör, szabad "
        "kérdés, pontos hibakód, tiszta fotóról kiolvasott kód, kötelező forrás, "
        "őszinte üres találat, azonosított belépés és helyi napló.",
    )
    add_para(
        doc,
        "A vízió ebből üzemi tudásréteg. Hatályos változat, soronkénti jogosultság, "
        "karbantartási kapcsolat, majd több egymástól elzárt telephely ugyanazzal a "
        "termékkel. Hadiipari gyártásban azért lehet belőle erős termék, mert oda is "
        "bevihető, ahova a felhős asszisztens nem, és azért marad bent, mert a választ "
        "mindig vissza lehet vezetni a jóváhagyott bekezdésig.",
    )

    footer = doc.add_paragraph()
    footer.paragraph_format.space_before = Pt(18)
    set_run_font(
        footer.add_run(
            "Termékvízió a LUMEEI AI Mind tananyagos, Cloud Run-os rendszeréből "
            "(alkalmazás 2.0.0, API 2.1.0, 2026). A hadiipari változat a gyár által "
            "betöltött dokumentációból válaszol; gyártási eljárást a modell nem pótol."
        ),
        size=9,
        italic=True,
        color=RGBColor(0x77, 0x77, 0x77),
    )

    doc.save(OUT)
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
