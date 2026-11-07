# LUMEEI AI Mind — szoftverarchitektúra fejlesztőknek és agenteknek

**Státusz:** a repóban lévő, működő tananyagos rendszer.  
**Verzió:** Flutter app `2.0.0+1` · FastAPI `2.1.0` · anyagmanifest `version: 18` · 2026. október 15.

Ez a dokumentum a forráskód alapján készült (`lib/`, `ToDeploy/app/`, `web_tester/`, `assets/config/app_config.json`). A hadiipari gyártási asszisztens külön termékvízió (`docs/Hadiipari_Gyartasi_Asszisztens_Osszefoglalo.docx`). Az a vízió ebben a kódban nincs implementálva: nincs helyi zárt profil, nincs hibakód-katalógus, nincs OCR, nincs jogosultságkezelés.

A Dart fájlok soronként kommenteltek (`scripts/comment_dart_lines.py`). A kommentek gyakran sablonszövegek. Specifikációnak a végrehajtó kód számít, nem a komment.

## 1. Mit csinál a szoftver

Magyar nyelvű oktatási chat. A telefonon a felület, a felolvasás és a magyar–angol fordítás fut. A tananyagkeresés, a webes kiegészítés és a válaszgenerálás a szerveren fut.

Egy Flutter-kérdés útja:

1. A felhasználó magyarul ír a chatbe.
2. `TranslationService.toEnglish` a telefonon angolra fordít (Google Translate, a `translator` csomag).
3. `POST /v1/chat` a `cloudBaseUrl` címre: angol `question`, eredeti `hungarianQuestion`, kiválasztott `documentId`.
4. A szerver DistilUSE embeddinggel és lexikális boosttal keres az előre épített tananyagindexben.
5. Ha kevesebb mint két találat van, vagy a kontextus üres, DuckDuckGo HTML keresés egészíti ki.
6. A Qwen2.5 GGUF (`llama-cpp-python`) angol választ ad a kontextusból.
7. `TranslationService.toHungarian` visszafordítja, és a buborékban ez a magyar szöveg jelenik meg.

A belső pipeline angol, mert a kis modell és az angol chunkok együtt stabilabbak. A felhasználó végig magyart lát.

A beszélgetés előzménye csak a telefon memóriájában van. A szerver minden kérésnél csak az aktuális kérdést és a frissen kikeresett kontextust kapja. Többfordulós modellmemória nincs.

## 2. Futási kép

```
[Flutter telefon]
  UI, TTS, SharedPreferences, Google Translate
        |  HTTPS
        v
[ToDeploy FastAPI  :8080]
  Embedder (DistilUSE ONNX, 512 dim)
  RagStore (RAG1 prebuilt_index.bin, memóriában)
  web_search (DuckDuckGo HTML, ha kevés a találat)
  LocalLlm (Qwen2.5 GGUF, llama.cpp, CPU)

[web_tester böngésző]
  saját /v1/translate hívás a szerveren (nem a telefonos translator)
  /v1/chat documentId nélkül → minden betöltött könyv
```

Éles cím a konfigban: `https://lumeei-ai-mind-270606217294.europe-west1.run.app` (`assets/config/app_config.json`).

Helyi szervernél a telefonról a gép LAN IP-je kell (`http://192.168.x.x:8080`). A `127.0.0.1` a telefonról a telefont jelenti.

## 3. Repótérkép

| Útvonal | Szerep | Állapot |
|---|---|---|
| `lib/` | Flutter vékony kliens | Kész, cloud-only |
| `assets/config/app_config.json` | Egyetlen klienskonfig: `cloudBaseUrl` | Kész |
| `assets/branding/` | Logó a splashen és a home-on | Kész |
| `ToDeploy/app/` | FastAPI + RAG + LLM + keresés + fordítás | Kész |
| `ToDeploy/data/materials/materials_manifest.json` | Négy történelemkönyv katalógusa | A manifest a repóban van |
| `ToDeploy/data/embedding/vocab.txt` | DistilUSE szótár | A repóban van |
| `ToDeploy/data/embedding/model.onnx` | Embedding modell | Ebben a munkakópiában nincs |
| `ToDeploy/data/materials/*/prebuilt_index.bin` | RAG1 indexek | Ebben a munkakópiában nincsenek |
| `ToDeploy/models/*.gguf` | Qwen súlyok | Gitignore (`models/*.gguf`), nincs a fában |
| `web_tester/` | Statikus böngészős kliens | Kész (`index.html`, `app.js`) |
| `firebase.json` | Hosting `public: web_tester` | Kész |
| `examples/` | Host app bekötési példák | Kész |
| `test/widget_test.dart` | Placeholder `expect(true, isTrue)` | Nincs valódi teszt |
| `docs/Hadiipari_…docx` | Termékvízió | Nem kód |

A szerver embedding ONNX, a RAG1 bin-ek és a GGUF nélkül elindulásig eljut, de a chat nem válaszol: hiányzó ONNX-nál az indulás `FileNotFoundError`, hiányzó GGUF-nál a `/v1/chat` 503, üres katalógusnál `ragReady: false`. A manifestben szereplő bin, ha a fájl nincs a lemezen, csendben kimarad (`rag_store._load` `continue`).

## 4. Szerver (`ToDeploy/app`)

Indulás (`main.lifespan`), ebben a sorrendben:

1. `Embedder(settings.embedding_onnx, settings.embedding_vocab)`
2. `RagStore(settings.materials_dir, embedder)` — manifest + minden létező `prebuilt_index.bin`
3. `LocalLlm(...).load()` — hiányzó GGUF esetén logol és `ready` marad `False`, a folyamat nem hal el

A `requirements-llm.txt` megjegyzése azt írja, hogy GGUF nélkül a chat kontextus-fallback választ ad. A kód mást csinál: `chat()` 503-at ad, ha `llm.ready` hamis. Health és books GGUF nélkül is megy, ha az embedding és a manifest betöltődött.

Függőségek: `requirements.txt` (FastAPI 0.115.12, uvicorn 0.34.0, pydantic 2.11, pydantic-settings, numpy<2, onnxruntime 1.21, httpx 0.28). Az LLM külön: `llama-cpp-python==0.3.8`.

CORS: `CORS_ORIGINS` vesszős lista, alap `*`. Metódus és header mind engedett, `allow_credentials=True`.

`Settings.host` és `Settings.port` be vannak kötve, de `main.py` nem olvassa őket. A portot az uvicorn kapja (`Dockerfile`: `PORT`, alap 8080).

### 4.1 `GET /health`

Mindig 200, amíg a folyamat él. Nem 503, ha a modell hiányzik; a flag jelzi.

```json
{
  "ok": true,
  "uptimeSec": 12,
  "ragReady": true,
  "llmReady": true,
  "books": [{ "documentId": "tortenelem_9", "title": "Töri 5.", "chunkCount": 0 }]
}
```

- `ok` mindig `true` ezen az úton.
- `ragReady`: a store létezik és a katalógus nem üres.
- `llmReady`: a GGUF betöltődött.
- A Flutter `ping()` 200-at, `ok == true`-t és `llmReady == true`-t követel. `ragReady`-t nem nézi. Ha a modell nincs kész, a splash hibán marad.

### 4.2 `GET /v1/books`

`{"books": rag.catalog}`. A store még nincs: 503 `"RAG not ready"`. Egy katalóguselem: `documentId`, `title`, `chunkCount`.

A manifest címei a kódban így vannak, a mappa neve mást sugall:

| `documentId` | Mappa | `title` a manifestben |
|---|---|---|
| `tortenelem_9` | `tortenelem_9_llm` | Töri 5. |
| `tortenelem_6` | `tortenelem_6` | Töri 6. |
| `tortenelem_7` | `tortenelem_7` | Töri 7. |
| `tortenelem_8` | `tortenelem_8` | Töri 8. |

`format` mindenhol `llm_pack`, `languages` csak `en`, indexfájl `prebuilt_index.bin`. A UI cím a manifest `title`, nem a bin saját címe (`RagStore._load` felülírja).

### 4.3 `POST /v1/translate`

A böngészős tesztelőnek van. A Flutter nem hívja; a telefon a `translator` csomagot használja.

Kérés: `text` (1–4000 karakter), `source` = `hu` | `en` | `auto` (alap `auto`), `target` = `hu` | `en` (alap `en`).

`auto`: ha van magyar ékezet a szövegben, a forrás `hu`, különben `en`. Azonos forrás és cél esetén a szöveg változatlan. Üres szöveg: 400.

A megvalósítás `gt_translate.translate_text`: nem hivatalos `translate.googleapis.com/translate_a/single?client=gtx` hívás, 12 másodperc timeout. Hiba esetén az eredeti szöveget adja vissza, nem 5xx-et. A válasz: `{ "text", "source", "target" }`.

### 4.4 `POST /v1/chat`

Kérés (camelCase alias, a snake_case mezőnév is érvényes, `populate_by_name`):

```json
{
  "question": "Who was Koppany?",
  "hungarianQuestion": "Ki volt Koppány?",
  "documentId": "tortenelem_9"
}
```

- `question`: kötelező, 1–2000 karakter. Ezt embeddeli és ezt adja a modellnek.
- `hungarianQuestion`: opcionális. Lexikális boost. Ha üres, az angol kérdés helyettesíti.
- `documentId`: opcionális. Ha a katalógusban nincs ilyen id, vagy null, minden betöltött könyvben keres.

Előfeltétel: store és llm objektum létezik, és `llm.ready`. Különben 503, GGUF-útvonalas üzenettel.

Lépések a `chat()` függvényben:

1. `rag.retrieve(english_query, hungarian_query, document_id)`.
2. Ha `len(hits) < 2` vagy a kontextus üres: `web_search.search_curriculum`. Sikeres webes találat a kontextus elejére kerül, `[Internet (Hungarian curriculum)]` fejléccel, és `web_used` igaz lesz.
3. `llm.generate`. Üres kontextusnál a modell nem hívódik; a fix mondat: `I do not know from the course material.`
4. Válasz: `answer` (angol), `documentId` (a kérésből másolva, nem a nyertes chunké), `debug`.

A `debug` mezői snake_case, mert a `ChatDebug` modellnek nincs aliasa:

| Mező | Jelentés |
|---|---|
| `english_question` | A kapott angol kérdés |
| `context` | Ami a modell promptjába került |
| `search_terms` | Foldolt, kiegészített lexikális termek |
| `hits` | Legfeljebb 5 tankönyvi találat; webes találat esetén az a lista elejére kerül |
| `llm_ready` | Itt mindig true (különben 503 volt) |
| `web_used` | Belépett-e a DuckDuckGo |

Egy hit: `id`, `title`, `score` (4 tizedes), `text` (legfeljebb 280 karakter). A `score` koszinusz-távolság lexikális boost után. Kisebb jobb. A webes hit `id` értéke `web::curriculum`, a `score` ott a webes relevancia (nagyobb jobb). A két skála nem ugyanaz.

### 4.5 Keresés (`rag_store.retrieve`)

Alapok: `top_k = 4`, `max_context_chars = 1400`. A promptba a kiválasztottak közül az első kettő kerül (`_build_context(picked[:2])`).

Vektor: az angol kérdés 512 dimenziós, L2-normalizált DistilUSE vektora. A chunk mátrixszal skalárszorzat = koszinusz, mert a tárolt vektorok is normalizáltak. Távolság = `1 - similarity`.

Lexika:

- Termek az angol és a magyar kérdésből. Minimum 3 karakter. Stopwords magyarul és angolul (`_STOP`).
- Ékezet lenyomása: á→a, é→e, í→i, ó/ö/ő→o, ú/ü/ű→u.
- `translate.expand_terms` néhány fix alias (Athéné/bölcsesség, Zeusz, Koppány, Szent István, olimpia). Ez nem általános fordító.
- A keresett szöveg a chunk `metadata_json.canonical_text_en` mezője, ha van; különben `chunk.text`.
- Találatonként `dist *= 1 / (1 + 0.45 * term_hits)`.

Szűrés:

- `record_id` (vagy ennek híján a chunk id) szerint deduplikál.
- Ha van term, és egyik sincs a passzázsban, a találat kiesik.
- Ha így nulla találat marad, tiszta embedding top-k, de csak `score <= 0.55` távolságig (erősebb egyezés; a távolság kicsi).
- A kontextusblokk fejléce `[Cím p.OLDAL]`, ha a metában van `page_start`, különben `[Cím #chunk_index]`.
- A kivonat a leghosszabb illeszkedő term köré van vágva, `…` prefix/suffix-szel. 120 karakter alatti maradék helyen a következő hit már nem fér be.

### 4.6 RAG1 bin (`rag_index.py`)

Little-endian. A betöltő a `scripts/prebuild_llm_pack_index.py` által írt formát várja; az a script ebben a repóban nincs.

| Mező | Típus |
|---|---|
| magic | 4 bájt `RAG1` |
| format_version, dimensions, count | 3 × uint32; a verzió csak 1 lehet |
| embedding_model_id, document_id, title | uint32 hossz + UTF-8 |
| ismételve `count` alkalommal | chunk id, uint32 chunk_index, text, metadata_json, majd `dimensions × float32` embedding |

A metadata JSON, amit a kereső olvas: `canonical_text_en`, `record_id`, `page_start`. Más kulcsot a futó kód nem használ.

### 4.7 Embedding (`embedder.py`)

`WordPieceTokenizer`, `do_lower_case=False`, max 128 token, `[CLS]` / `[SEP]` / pad. ONNX bemenet: `input_ids`, `attention_mask` (int64). Kimenet: `sentence_embedding`. Provider: csak `CPUExecutionProvider`. A vektor L2-normalizált. `dimensions` fixen 512, nem az ONNX-ból olvasott érték.

### 4.8 LLM (`llm.py`)

`LocalLlm.load`: a fájl hiánya nem kivétel a folyamatnak. `generate`:

- Üres kontextus → azonnal `I do not know from the course material.`
- Különben egy system + egy user üzenet, `create_chat_completion`.
- Alap: `n_ctx=1024`, `n_threads=4`, `max_tokens=256`, `temperature=0.3`.
- A system prompt szabálya: csak a kurzuskontextusból, tankönyvet előnyben a webes részlettel szemben, angolul 2–4 mondat, ne találjon ki tényt. Ha nincs a kontextusban a válasz, ugyanez a fix mondat.
- Üres modellkimenet ugyanerre a mondatra cserélődik.

Nincs streaming, nincs temperature a kérésből, nincs előzmény a `messages` listában.

### 4.9 Webes keresés (`web_search.py`)

`search_curriculum`: a lekérdezés az angol kérdés plusz a fix toldalék `based on the Hungarian curriculum`. GET `https://html.duckduckgo.com/html/`, `kl=us-en`, timeout 12 s, az első 8 HTML találat. Regex a `result__a` és `result__snippet` osztályokra.

Egy találat akkor elég jó (`good_enough`), ha a snippet legalább 60 karakter, legalább két term egyezik, és a pontszám legalább 2.5. A pontszám a termek száma plusz a leghosszabb term hossza / 8, legfeljebb +2. Hiba vagy gyenge találat: `None`, a chat megy tovább a tankönyvi kontextussal.

### 4.10 Környezeti változók

Pydantic Settings, `.env`, a mezőnév nagybetűsítve.

| Változó | Alap | Hatás |
|---|---|---|
| `MATERIALS_DIR` | `ToDeploy/data/materials` | Manifest és bin-ek |
| `EMBEDDING_ONNX` | `data/embedding/model.onnx` | Kötelező az induláshoz |
| `EMBEDDING_VOCAB` | `data/embedding/vocab.txt` | Kötelező az induláshoz |
| `LLM_MODEL_PATH` | üres | GGUF; Dockerben a Qwen2.5 1.5B Q4_K_M útvonal |
| `LLM_N_CTX` | 1024 | llama.cpp kontextus |
| `LLM_N_THREADS` | 4 | CPU szál |
| `LLM_MAX_TOKENS` | 256 | Válaszhossz |
| `LLM_TEMPERATURE` | 0.3 | |
| `CORS_ORIGINS` | `*` | Vesszős lista |

Docker: Python 3.11-slim, build-essential + cmake a llama-cpp miatt, `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Az image a `data/` és a `models/` mappát bemásolja buildkor.

## 5. Flutter kliens

Csomag: `educational_chatbot`. SDK `^3.9.2`. Függőségek, amik tényleg számítanak: `http`, `translator`, `flutter_tts`, `shared_preferences`, `path_provider`, `uuid`, `equatable`. A `flutter_riverpod` csak a `ProviderScope` héj a splash után; chat providerek nincsenek. Az állapot `ChangeNotifier` + `ServiceLocator`.

Belépés: `lib/main.dart` → `bootstrap()`.

### 5.1 Indítás

`bootstrap` logot nyit, majd a `_StartupApp` splasht. Az `LumeeiAiMind.initialize` meghívja a `ServiceLocator.init`-et:

1. `AppConfig.load` — `assets/config/app_config.json`. Üres `cloudBaseUrl` → `StateError`.
2. `SharedPreferences`.
3. `TranslationService.ensureReadyOnlineOnly` — azonnal késznek jelöli magát, hálózatot itt még nem hív.
4. `CloudChatService.ping` — `GET /health`, 20 s. Kell a 200, az `ok` és az `llmReady`.
5. Csak sikeres ping után lesz `isInitialized`.

Hiba: magyar splash szöveg és Újrapróbálás. A gomb `LumeeiAiMind.dispose()` után újra `_start()`. Sikernél `runApp(ProviderScope(child: EducationalChatbotApp()))`. A fő app `HomeScreen`: bemutató oldal, a chat a FAB-ból `LumeeiAiMind.openChat`-tel nyílik (fade + enyhe slide).

### 5.2 `CloudChatService` — a kliens összes hálózati chat-funkciója

| Metódus | Mit csinál |
|---|---|
| `ping()` | Health. Sikertelenül `CloudUnavailableException`, magyar szöveggel. |
| `fetchBooks()` | `GET /v1/books` → `(documentId, title)` lista. |
| `sendMessage(text, {useRag, documentId})` | Egy kör. `useRag` hatástalan: a szerver mindig keres. |
| `stopGeneration()` | Növeli a `_turnEpoch`-ot, a buborék szövege „A válasz megszakítva.” A már kint lévő HTTP kérés a szerveren lefut; csak a késő válasz dobódik el. |
| `clearHistory()` | Memóriaüzenetek, `lastContextBlock`, `lastPreviews` törlése. A szervert nem érinti. |
| `selectedDocumentId` | Üres stringből `null` lesz, és `notifyListeners`. |

`sendMessage` sorrendje:

1. Üres szöveg vagy már futó generálás: return.
2. Új epoch, user buborék, assistant buborék `…` és `isStreaming: true`.
3. `toEnglish(trimmed)`. Fordítási hiba esetén a magyar szöveg megy tovább kérdésként.
4. POST `/v1/chat`, timeout 180 s. Body: `question`, `hungarianQuestion`, `documentId` (paraméter vagy a kiválasztott könyv).
5. 503 és minden nem-200: magyar hiba a buborékban.
6. `answer` mojibake-javítás, majd `toHungarian`.
7. `debug.context` és `debug.hits` → `lastContextBlock` és `RagSourcePreview` lista. `usedInPrompt` a kliensen `i < 2`. Ez sorrendi becslés. Webes hit a lista elején eltolja, ezért nem azonos a szerver promptjába került két tankönyvi passzázssal.
8. `finally`: ha az epoch még a miénk, `isGenerating = false`.

Hálózati hibák (`TimeoutException`, `SocketException`, `ClientException`, lookup/refused/reset) külön magyar mondatok. A részletes ok a `DiagnosticLog`-ba megy.

### 5.3 Fordítás (`translation_service.dart`)

`toEnglish`:

- „Ki volt …?” sablon, legfeljebb három szavas névvel: `Who was <név>?`, a név fordítás nélkül.
- „bölcsesség istennője” → `Who was the goddess of wisdom? Athena Athene`.
- „Szent István” → `Who was Saint Stephen?`.
- Egyébként Google Translate `hu`→`en`, 10 s. Ha az angolból hiányzik a magyar nagybetűs név (legalább 3 karakter), zárójelben visszakerül.
- Hiba vagy üres eredmény: az eredeti magyar szöveg.

`toHungarian`: `en`→`hu`, 10 s, utána `fixUtf8Mojibake`. Hiba: az angol szöveg, javított kódolással.

`skipStartupOfflineDownload` üres. Régi offline fordítócsomag maradványa.

### 5.4 Mojibake (`text_encoding_fix.dart`)

`fixUtf8Mojibake`: ha a szövegben `Ã` vagy `Â` van, a tokent Latin-1 bájtként visszafejti UTF-8-ra (tipikusan `BÃ©la` → `Béla`). Csak akkor cserél, ha a javított alak „magyarabb” (`_scoreHungarianText`). A chat válaszán és a magyar fordításon fut.

### 5.5 Napló (`diagnostic_log.dart`)

`documents/diagnostic.log`, gyűrűben 400 sor. `log(tag, message)` konzolra és fájlba. `installGlobalHandlers` a Flutter hibákat is ide írja. A chat UI ezt nem mutatja; USB nélkül a fájl a készüléken marad.

### 5.6 Chat képernyő — kész funkciók

Fájl: `lib/features/chat/presentation/screens/lumeei_ai_mind_chat_screen.dart`. A UI a `ChatService`-t figyeli (`addListener`), nem hív HTTP-t közvetlenül, kivéve a könyvlistát, ami `CloudChatService.fetchBooks`.

| Funkció | Viselkedés |
|---|---|
| Könyvválasztó | Induláskor `fetchBooks`. A mentett id `lumeei.selected_document_id`. Ha az nincs a listában, az első könyv. Választáskor prefs + `selectedDocumentId`. Generálás alatt a váltás zárolt. |
| Küldés | Üres és zárolt állapotban nem megy. A mező törlődik, a fókusz el. `sendMessage(text, useRag: true, documentId: kiválasztott)`. |
| Zárolás | `_sendInFlight` vagy `isGenerating`: input, törlés, könyvváltás áll. |
| Gondolkodás | `_ThinkingBar`, amíg a kör tart. A szerver nem streamel; a `…` egyben cserélődik a válaszra. |
| Megszakítás | Vissza gomb generálás közben dialógust ad: „Várok” vagy „Megszakítás”. A megszakítás TTS-t állít és `stopGeneration`-t hív, majd pop. |
| Előzmény törlése | `clearHistory`. Generálás alatt a gomb kikapcsol. |
| Felolvasás | `flutter_tts`, `hu-HU`, sebesség 0.45, hangmagasság 1.0. Ugyanarra a buborékra újra kattintva stop. Ha nincs `hu` nyelv a készüléken, Androidon a `TtsInstallPlatform` a TTS-telepítőt nyitja (`MethodChannel` `hu.educational.educational_chatbot/tts_install`). Más platformon csak snackbar. |
| Görgetés | Új üzenetre az aljára ugrik. |
| Források | A `RagSourcePreview` a `ChatMessage`-en ott van (`ragPreviews`, `ragContextBlock`, `ragSearchQuery`). A buborék a magyar választ mutatja; a debug mezők a modellen vannak, a szerver `debug` objektumából töltve. |

`ChatMessage` szerepek: `user`, `assistant`, `system`. A futó kód `system` üzenetet nem hoz létre. `ragSources` mező létezik, a cloud út nem tölti.

### 5.7 Publikus bekötés másik Flutter appba

Egy import: `package:educational_chatbot/lumeei_ai_mind.dart`.

```dart
await LumeeiAiMind.initialize(onProgress: (status, progress) {});
LumeeiAiMind.openChat(context);
```

| API | Szerep |
|---|---|
| `initialize` | Napló + `ServiceLocator.init` (health ping). `onProgress` a splashnek; a cloud úton 0.1 majd 1.0. |
| `openChat` | Push route, `showBackButton` alap true. |
| `chatScreen` | Widget beágyazáshoz, navigáció nélkül. |
| `theme` | `LumeeiTheme.dark()`. |
| `skipOfflineTranslatorWait` | No-op. |
| `dispose` | HTTP kliens és fordító elengedése, locator nullázása. |
| `isInitialized` | A sikeres ping után true. |

Példák: `examples/host_simple_main.dart`, `examples/host_complex_integration.dart`. Emberi bekötési leírás: `docs/Lumeei_AI_Mind_Integracio.md`.

### 5.8 Téma

`LumeeiTheme.dark()`: sötét háttér, cián `0xFF00E5FF`, lila `0xFF9B5CFF`. A `EducationalChatbotApp` light és dark témája is ez, `ThemeMode.dark`.

## 6. Böngészős tesztelő

`web_tester/app.js`, statikus, Firebase Hosting a `firebase.json` szerint mindent `index.html`-re ír.

| Viselkedés | Részlet |
|---|---|
| API cím | `localStorage` kulcs `lumeei.webTester.apiUrl`. Ha nincs mentés és nincs `window.LUMEEI_DEFAULT_API`, a mező `https://example.invalid`. A README Cloud Run előtöltést ír; a kód ezt csak akkor teszi, ha a default globális meg van adva. |
| Health | `GET /health`, 20 s. Pirulák: ok, rag, llm, uptime, könyvek száma. |
| Kérdés | `POST /v1/translate` hu→en, majd `POST /v1/chat`, majd translate en→hu. Chat timeout 180 s, fordítás 20 s. |
| `documentId` | A web kliens nem küldi. A szerver az összes könyvben keres. |
| Fordítás hiba | A magyar kérdés megy tovább nyersen, a válasz angolul marad, és egy meta-sor redeploy-t kér. |
| Debug panel | Kapcsolható. Kiírja a két nyelvű kérdést, a két választ és a szerver `debug` objektumát. |
| TTS, könyvválasztó | Nincs. |

## 7. Ami kész, és ami nincs

Kész és a fenti fájlokban végig van kötve:

- Splash health-kapuval és újrapróbálással
- Magyar UI, angol belső pipeline, két független fordítási út (telefonos csomag és szerver `/v1/translate`)
- Tankönyvlista, egy könyvre szűrt keresés a telefonon, összes könyv a web tesztelőn
- Hibrid RAG: embedding + lexikális boost + kis alias-szótár + dedup + gyenge találatnál embedding-visszaesés
- Vékony webes tananyag-kiegészítés DuckDuckGo HTML-ből
- GGUF válasz, fix „nem tudom” mondat üres kontextusra
- Felolvasás magyar rendszerhanggal, megszakítás, előzmény törlése a készüléken
- Host API másik Flutter alkalmazáshoz
- Docker image és Cloud Run-ra szánt indítás
- Diagnosztikai napló a telefonon

Nincs a kódban, agent ne építsen rá és ne írjon úgy, mintha létezne:

- Felhasználói fiók, API-kulcs, tanúsítvány, szerep, soronkénti dokumentumjog
- A modellnek átadott beszélgetés-előzmény
- Tokenstream a kliens felé (`isStreaming` csak helyi placeholder)
- OCR, hibakód-index, kamera
- Kimenő hálózat tiltása; a szerver fordítót és DuckDuckGo-t hív
- Hadiipari jogosultság, verzióhatály, munkalap, auditnapló. Az általános üzemi tudástár külön van: `ToDeploy/plant_console` a `/plant/` címen, a feltöltés a `/v1/plant/documents` úton.
- Automatizált teszt a chat útra (a `test/` egy igaz assert)
- A RAG1 indexet előállító script ebben a fában
- On-device LLM, ObjectBox, MediaPipe: a dokumentáció régi fejezetei ezt írják, a `lib/` cloud-only

## 8. Invariánsok módosításkor

- A Flutter `answer`-t angolnak kezeli és lefordítja. Magyar szerverválasz kétszer fordítódna.
- A `debug.hits[].score` tankönyvnél kisebb-jobb távolság. Új mezőnél a nevet és az irányt egyszerre kell közölni.
- `documentId` hiánya minden packet keres. A telefon mindig küld kiválasztott id-t, a web tesztelő sosem.
- `useRag: false` a kliensen nem kapcsolja ki a keresést.
- A `ping` `llmReady` nélkül nem engedi be a felhasználót, akkor sem, ha a RAG kész.
- Üres kontextusnál a modell hívása szándékosan kimarad.
- A manifest `title` felülírja a bin címét. A `tortenelem_9` sor címe „Töri 5.”.
- A Dart kommentgenerátor (`scripts/comment_dart_lines.py`) ne fusson újra egy változtatás részeként, hacsak nem az a feladat: a zaj elfedi a diffet.

## 9. Fájl → felelősség, gyorsan

| Fájl | Felelősség |
|---|---|
| `ToDeploy/app/main.py` | Életciklus, `/health`, `/v1/books`, `/v1/translate`, `/v1/chat`, `/v1/plant/*`, `/plant/` |
| `ToDeploy/app/plant_extract.py` | Gyári fájlok szövege: PDF, Word, Excel, PowerPoint, szöveg, táblázat |
| `ToDeploy/app/plant_store.py` | Üzemi tudástár, hibakód-kiemelés, keresés |
| `ToDeploy/plant_console/` | Személyzeti és vezetői felület |
| `ToDeploy/app/config.py` | Env → útvonalak és LLM számok |
| `ToDeploy/app/embedder.py` | WordPiece + DistilUSE ONNX |
| `ToDeploy/app/rag_index.py` | RAG1 olvasó, manifest |
| `ToDeploy/app/rag_store.py` | Hibrid retrieve, kontextusablak |
| `ToDeploy/app/translate.py` | Term aliasok, nem mondatfordító |
| `ToDeploy/app/gt_translate.py` | Google Translate a web tesztelőnek |
| `ToDeploy/app/web_search.py` | DuckDuckGo curriculum snippet |
| `ToDeploy/app/llm.py` | GGUF chat completion, system prompt |
| `lib/bootstrap.dart` | Splash, ping, átváltás a home-ra |
| `lib/core/di/service_locator.dart` | Egyetlen cloud chat + fordító |
| `lib/features/chat/data/cloud_chat_service.dart` | HTTP kör, epoch, hibaszövegek |
| `lib/features/translation/data/translation_service.dart` | Hu↔En a telefonon, névsablonok |
| `lib/features/chat/presentation/screens/lumeei_ai_mind_chat_screen.dart` | Chat UI, könyv, TTS, zárolás |
| `lib/integration/lumeei_ai_mind.dart` | Host API |
| `web_tester/app.js` | Böngészős health, translate, chat, debug |
